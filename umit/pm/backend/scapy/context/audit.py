#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
#
# Author: Francesco Piccinno <stack.box@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import os
import time
import socket

from threading import Thread

from umit.pm.core.i18n import _
from umit.pm.core.netconst import *
from umit.pm.core.logger import log
from umit.pm.core.atoms import ThreadPool, defaultdict
from umit.pm.manager.auditmanager import AuditDispatcher, AuditManager, \
                                         IL_TYPE_ETH
from umit.pm.backend.scapy import *

import select
from struct import pack, unpack_from

# These should be moved outside.

ERR_TIMEOUT   = 0
ERR_EXCEPTION = 1

PF_INET = socket.AF_INET
SIOCGIFMTU = 0x8921

if os.name != 'nt':
    from fcntl import ioctl

    def get_mtu(iface):
        s = socket.socket(PF_INET, socket.SOCK_DGRAM, 0)
        mtu = unpack_from("16sI",
                          ioctl(s.fileno(),
                                SIOCGIFMTU,
                                pack("16sI", iface, 0)))[1]
        s.close()

        log.debug('%s MTU = %d' % (iface, mtu))

        return mtu
else:
    def get_mtu(iface):
        log.warning('Returning 1500 as MTU for %s' % iface)
        return 1500

def get_routes(_iface):
    for ip, netmask, gw, iface, outputip in conf.route.routes:
        if iface == _iface:
            return (socket.inet_ntoa(pack("!I", ip)),
                    socket.inet_ntoa(pack("!I", netmask)),
                    gw, outputip)

    return (None, None, None, None)

class SendWorker(object):
    def __init__(self, sck, mpkts, repeat=1, delay=None, onsend=None, \
                 oncomplete=None, onerror=None, timeout=None, onrecv=None, \
                 onreply=None, udata=None):

        if isinstance(mpkts, MetaPacket):
            mpkts = [mpkts]

        # Core attributes
        self.socket = sck
        self.mpkts = mpkts

        # Timeouts and repeat
        self.repeat = repeat
        self.delay = delay
        self.timeout = timeout
        self.lastrecv = None

        # Callables
        self.oncomplete = oncomplete
        self.onerror = onerror
        self.onrecv = onrecv
        self.onreply = onreply
        self.onsend = onsend
        self.udata = udata

        # Num of answers excepted
        self.ans_left = len(mpkts)

def register_audit_context(BaseAuditContext):
    class AuditContext(BaseAuditContext):
        """
        Here we have 3 different function types:
         - s_l{2,3,b} (mpkts = A single MetaPacket or a list,
                       repeat = how many time send the mpkts (-1 for infinite),
                       delay = time between two send,
                       onsend = callable or None,
                       oncomplete = callable or None,
                       onerror = callable or None)
         - sr_l{2,3,b} (**same arguments of s_l***,
                        timeout = if no reply between ts than stop send
                        onrecv = callable,
                        onreply = callable)
         - si_l{2,3,b} (mpkt) -> immediate send a single packet

        NB: timeout parameter is in seconds, while delay in msecs

        Prototypes for callbacks:
         - onsend(send, mpkt, udata)
         - oncomplete(send, udata)
         - onerror(send, status, udata)
         - onreply(send, orig, ans, udata)
         - onrecv(send, mpkt, udata)
        """

        def __init__(self, dev1, dev2=None, bpf_filter=None, \
                     skip_forwarded=True, unoffensive=False, capmethod=0):
            BaseAuditContext.__init__(self, dev1, dev2, bpf_filter, capmethod)

            self._mac1, self._mac2 = None, None
            self._ip1, self._ip2 = None, None
            self.linktype = None

            self.internal = False
            self.thread1 = None
            self.thread2 = None
            self.skip_forwarded = skip_forwarded
            self.unoffensive = unoffensive

            self.thread_pool = ThreadPool()
            self.audit_dispatcher = None

            self.ans_dict = defaultdict(list)
            self.receivers = [] # A list of callable

            self.iface_origin_table = []
            self.bridge_origin_table = []

            if dev2:
                self.title = self.summary = _('Audit on %s:%s') % (dev1, dev2)
            else:
                self.title = self.summary = _('Audit on %s') % dev1

            log.debug('Creating send sockets')

            try:
                # Here we create L2 and L3 sockets used to send packets
                self._l2_socket = conf.L2socket(iface=dev1)
                self._l3_socket = conf.L3socket(iface=dev1)

                self._ip1 = get_if_addr(dev1)
                self._mac1 = get_if_hwaddr(dev1)
                self._mtu1 = get_mtu(dev1)

                if dev2:
                    self._ip2 = get_if_addr(dev2)
                    self._mac2 = get_if_hwaddr(dev2)
                    self._mtu2 = get_mtu(dev2)

                    self._lb_socket = conf.L2socket(iface=dev2)

                    self.check_forwarded = self.__check_forwarded_multi
                    self.set_forwardable = self.__set_forwardable_multi
                    self.forward = self.__forward_multi
                else:
                    self._ip2 = None
                    self._mac2 = None
                    self._mtu2 = None

                    self.check_forwarded = self.__check_forwarded_single
                    self.set_forwardable = self.__set_forwardable_single
                    self.forward = self.__forward_single

                if capmethod == 0:
                    log.debug('Creating listen sockets')

                    self._listen_dev1 = conf.L2listen(iface=dev1,
                                                      filter=bpf_filter)

                    if dev2:
                        self._listen_dev2 = conf.L2listen(iface=dev2,
                                                          filter=bpf_filter)

                    # Get datalink
                    try:
                        if self._listen_dev1.LL in conf.l2types.layer2num:
                            self.linktype = \
                                conf.l2types.layer2num[self._listen_dev1.LL]
                        elif self._listen_dev1.LL in conf.l3types.layer2num:
                            self.linktype = \
                                conf.l3types.layer2num[self._listen_dev1.LL]
                        else:
                            log.debug('Falling back to IL_TYPE_ETH as DL')
                            self.linktype = IL_TYPE_ETH
                    except:
                        try:
                            self.linktype = self._listen_dev1.ins.datalink()
                        except:
                            log.debug('It seems that we\'re using PF_PACKET'
                                      ' socket. Using IL_TYPE_ETH as DL')
                            self.linktype = IL_TYPE_ETH
                else:
                    log.debug('Creating helper processes')

                    # FIXME: what we are doing here is to assume that the
                    # the interface on which we're running tcpdump is an
                    # ethernet. We should find a way to get the datalink type
                    # from run_helper or just drop this workaround and implement
                    # a C module.


                    log.warn('Assuming IL_TYPE_ETH as datalink!')
                    self.linktype = IL_TYPE_ETH

                    self._listen_dev1 = run_helper(self.capmethod - 1, dev1,
                                                   bpf_filter)

                    if dev2:
                        self._listen_dev2 = run_helper(self.capmethod - 1, dev2,
                                                       bpf_filter)

                self.audit_dispatcher = AuditDispatcher(self.linktype, self)

            except socket.error, (errno, err):
                self.summary = self.title + ' (' + str(err) +')'
                log.error(generate_traceback())
                return

            except Exception, err:
                self.summary = self.title + ' (' + str(err) +')'
                log.error(generate_traceback())

        def get_datalink(self):
            return self.linktype

        def get_ip1(self):
            return self._ip1
        def get_mac1(self):
            return self._mac1
        def get_ip2(self):
            return self._ip2
        def get_mac2(self):
            return self._mac2
        def get_mtu(self):
            return self._mtu1
        def get_mtu1(self):
            return self._mtu1
        def get_mtu2(self):
            return self._mtu2

        def get_netmask1(self):
            return get_routes(self._iface1)[1]
        def get_netmask2(self):
            return get_routes(self._iface2)[1]

        def __check_forwarded_single(self, mpkt):
            # Skip forwarded packets (same MAC, different IP)
            if mpkt.l2_src == self._mac1 and \
               mpkt.l3_src != self._ip1:

                mpkt.flags |= MPKT_FORWARDED
                return self.skip_forwarded

            return False

        def __check_forwarded_multi(self, mpkt):
            if mpkt.flags & MPKT_FROMIFACE:
                if mpkt.l2_src in self.iface_origin_table:
                    return False

                if mpkt.l2_src in self.bridge_origin_table:
                    mpkt.flags |= MPKT_FORWARDED
                    return self.skip_forwarded

            elif mpkt.flags & MPKT_FROMBRIDGE:
                if mpkt.l2_src in self.bridge_origin_table:
                    return False

                if mpkt.l2_src in self.iface_origin_table:
                    mpkt.flags |= MPKT_FORWARDED
                    return self.skip_forwarded

            if mpkt.flags & MPKT_FROMIFACE:
                log.info('Adding %s MAC to the IFACE table' % mpkt.l2_src)
                self.iface_origin_table.insert(0, mpkt.l2_src)

            elif mpkt.flags & MPKT_FROMBRIDGE:
                log.info('Adding %s MAC to the BRIDGE table' % mpkt.l2_src)
                self.bridge_origin_table.insert(0, mpkt.l2_src)

            return False

        def __set_forwardable_single(self, mpkt):
            if mpkt.l2_dst == self._mac1 and \
               mpkt.l2_src != self._mac1 and \
               mpkt.l3_dst != self._ip1:

                mpkt.flags |= MPKT_FORWARDABLE

        def __set_forwardable_multi(self, mpkt):
            if mpkt.l2_src == self._mac1 or \
               mpkt.l2_dst == self._mac1:
                return

            if mpkt.l2_src == self._mac2 or \
               mpkt.l2_dst == self._mac2:
                return

            mpkt.flags |= MPKT_FORWARDABLE

        def __forward_single(self, mpkt):
            if self.unoffensive:
                return

            if mpkt.flags & MPKT_DROPPED == 0:
                self.si_l3(mpkt)

            if mpkt.inject:
                self.inject_buffer(mpkt)

        def __forward_multi(self, mpkt):
            if mpkt.flags & MPKT_FROMIFACE:
                self.si_lb(mpkt)
            elif mpkt.flags & MPKT_FROMBRIDGE:
                self.si_l2(mpkt)

        def inject_buffer(self, mpkt):
            while True:
                is_ok, length = self.__inject(mpkt)

                if not is_ok or not length:
                    log.warning("Error while running injectors ok: %s len: %s" % (is_ok, length))
                    break

                self.si_l3(mpkt)

                mpkt.inject_len -= length
                mpkt.inject = mpkt.inject[length:]

                if not mpkt.inject_len:
                    break

            return True

        def __inject(self, mpkt):
            injector = AuditManager().get_injector(1, mpkt.l4_proto)

            if not injector:
                log.warning("No injectors for L4 proto: %d" % mpkt.l4_proto)
                return False, 0

            return injector(self, mpkt, 0)

        ########################################################################
        # Threads callbacks
        ########################################################################

        def _stop(self):
            if not self.internal:
                log.error('Audit is already stopped')
                return False

            self.internal = False
            self.summary = self.title + _(' (stopping)')

            log.debug('Stopping thread pool')
            self.thread_pool.stop()

            log.debug('Joining threads')

            if self.thread1:
                self.thread1.join()

            if self.thread2:
                self.thread2.join()

            self.state = self.NOT_RUNNING

            log.debug('AuditContext succesfully stopped')
            self.summary = self.title + _(' (stopped)')

            return True

        def _start(self):
            if self.internal:
                log.error('Audit is already running')
                return False

            if not self._listen_dev1:
                log.error('We\'ve got an error in __init__. No listen socket')
                return False

            self.internal = True

            log.debug('Spawning capture threads')

            func = (self.capmethod == 0 and \
                    self.__sniff_thread or \
                    self.__helper_thread)

            self.thread1 = Thread(None, func, 'ATK1', (self._listen_dev1, ))
            self.thread1.setDaemon(True)
            self.thread1.start()

            if self._listen_dev2:
                self.thread2 = Thread(None, func, 'ATK2', (self._listen_dev2, ))
                self.thread2.setDaemon(True)
                self.thread2.start()

            log.debug('Spawning thread pool for sending')
            self.thread_pool.start()

            self.state = self.RUNNING

            return True

        def __helper_thread(self, obj):
            errstr = None

            try:
                for reader in bind_reader(obj[0], obj[1]):
                    if not self.internal:
                        break

                    if reader:
                        reader, outfile_size, position = reader
            except OSError, err:
                errstr = err.strerror
                self.internal = False
                log.error(generate_traceback())
            except Exception, err:
                errstr = str(err)
                self.internal = False
                log.error(generate_traceback())

            self.audit_dispatcher = AuditDispatcher(reader.linktype, self)

            log.debug('Entering in the helper mainloop')

            reported_packets = 0
            mflags = (obj is self._listen_dev1) and \
                   MPKT_FROMIFACE and MPKT_FROMBRIDGE

            while self.internal:
                report_idx = get_n_packets(obj[0])

                if report_idx < reported_packets:
                    continue

                while reported_packets < report_idx:
                    r = reader.read_packet()

                    if not r:
                        break

                    self.__manage_mpkt(obj, MetaPacket(r, flags=mflags))

                    reported_packets += 1

                report_idx = reported_packets

            if errstr:
                self.internal = False
                self.state = self.NOT_RUNNING
                self.summary = self.title + ' (' + errstr + ')'

        def __sniff_thread(self, obj):
            errstr = None
            mflags = (obj is self._listen_dev1) and \
                   MPKT_FROMIFACE and MPKT_FROMBRIDGE

            log.debug('Entering in the native mainloop')

            while self.internal:
                r = None

                try:
                    if WINDOWS:
                        try:
                            r = obj.recv(MTU)
                        except PcapTimeoutElapsed:
                            continue
                    else:
                        inmask = [obj]
                        inp, out, err = select.select(inmask, inmask, inmask, None)

                        if obj in inp:
                            r = obj.recv(MTU)

                    if r is None:
                        continue

                    self.__manage_mpkt(obj, MetaPacket(r, flags=mflags))

                except Exception, err:
                    if self.internal:
                        errstr = str(err)
                        log.error(generate_traceback())

                    self.internal = False
                    break

            if errstr:
                self.internal = False
                self.state = self.NOT_RUNNING
                self.summary = self.title + ' (' + errstr + ')'

        def __manage_mpkt(self, obj, mpkt):
            found = False
            layer = 2

            while not found and layer <= 3:
                if layer == 2:
                    cpkt = mpkt.root
                elif is_proto(mpkt.root.payload):
                    cpkt = mpkt.root.payload
                else:
                    break

                idx = 0
                hashret = cpkt.hashret()
                lst = self.ans_dict[hashret]

                if hashret in self.ans_dict:
                    for ans, send, cnt in lst:
                        if cpkt.answers(ans.root):
                            send.ans_left -= 1
                            lst[idx][2] -= 1

                            if lst[idx][2] < 1:
                                del lst[idx]

                                if not lst:
                                    del self.ans_dict[hashret]

                            send.onreply(send, mpkt, ans, send.udata)

                            if send.ans_left == 0 and not send.timeout:
                                log.debug('Stopping SendWorker')
                                self.cancel_send(send)

                            found = True
                            break

                        idx += 1
                layer += 1


            if not found:
                for rcv in self.receivers:
                    if isinstance(rcv, SendWorker):
                        if callable(rcv.onrecv):
                            rcv.onrecv(rcv, mpkt, rcv.udata)
                    elif callable(rcv):
                        rcv((obj is self._listen_dev1 and \
                             self.socket1 or self.socket2), mpkt)


            if not self.check_forwarded(mpkt):
                try:
                    self.audit_dispatcher.feed(mpkt)
                except Exception, exc:
                    log.error(_('Error while feeding audit dispatcher'))
                    log.error(generate_traceback())

        ########################################################################
        # Worker functions
        ########################################################################

        def __worker_thread(self, send):
            while send.repeat != 0 and self.internal:
                send.ans_left = len(send.mpkts)

                for mpkt in send.mpkts:

                    if callable(send.onreply):
                        idx = 0
                        found = False
                        lst = self.ans_dict[mpkt.hashret()]

                        for pmpkt, psend, pcnt in lst:
                            if psend is send and pmpkt is mpkt:
                                found = True
                                break
                            idx += 1

                        if found:
                            lst[idx][2] += 1
                        else:
                            lst.append([mpkt, send, 1])

                    mpkt.root.time = time.time()

                    if callable(send.onsend):
                        send.onsend(send, mpkt, send.udata)

                    send.socket.send(mpkt.root)

                    if send.delay and self.internal:
                        time.sleep(send.delay / 1000.0)

                send.repeat -= 1
                log.debug('%d left' % send.repeat)

            # Now we have sent all the packets. We have to wait for the replies
            # but between timeout.

            if not callable(send.onrecv) and not callable(send.onreply):
                log.debug('Pure send process complete')

                if callable(send.oncomplete):
                    send.oncomplete(send, send.udata)

                return

            if send.timeout > 0:
                # If timeout is not setted we've to leave it
                log.debug('Send complete for %s. Waiting for timeout' % send)

                if send.ans_left > 0 and self.internal:
                    time_left = send.timeout * 1000
                    delay = max(100, send.delay)

                    while time_left > send.delay:
                        if send.ans_left == 0:
                            break

                        time_left -= delay
                        time.sleep(delay / 1000.0)

                if send.ans_left == 0:
                    log.debug('Send process complete')

                    if callable(send.oncomplete):
                        send.oncomplete(send, send.udata)
                else:
                    log.debug('Send process complete with %d pending replies' \
                              % send.ans_left)

                    if callable(send.onerror):
                        send.onerror(send, ERR_TIMEOUT, send.udata)

                self.cancel_send(send)
            else:
                log.debug('No timeout setted. Exiting after completion')

        ########################################################################
        # Public functions
        ########################################################################

        def cancel_send(self, send):
            assert isinstance(send, SendWorker)

            log.debug('Removing %s SendWorker' % send)

            if callable(send.onrecv):
                try:
                    self.receivers.remove(send)
                except ValueError:
                    log.warning('The callback was already removed.')

            if not callable(send.onreply):
                return

            removed = 0

            for mpkt in send.mpkts:
                try:
                    idx = 0
                    lst = self.ans_dict[mpkt.hashret()]
                    for pmpkt, psend, pcnt in lst:
                        if pmpkt is mpkt and psend is send:
                            del lst[idx]
                            break
                        idx = 0
                    removed += 1
                except ValueError:
                    continue

            if removed == len(send.mpkts):
                log.debug('SendWorker object succesfully removed')
            else:
                log.error('It seems that we\'ve leaved it dirty')

            del send

        ########################################################################
        # Pure send functions
        ########################################################################

        def s_l2(self, mpkts, repeat=1, delay=None, onsend=None, \
                 oncomplete=None, onerror=None, udata=None):
            """Send packets at Layer 2"""
            return self.__sendrcv(self.l2_socket, mpkts, repeat, delay, \
                                  onsend, oncomplete, onerror, udata)

        def s_l3(self, mpkts, repeat=1, delay=None, onsend=None, \
                 oncomplete=None, onerror=None, udata=None):
            """Send packets at Layer 3"""
            return self.__sendrcv(self.l3_socket, mpkts, repeat, delay, \
                                  onsend, oncomplete, onerror, udata)

        def s_lb(self, mpkts, repeat=1, delay=None, onsend=None, \
                 oncomplete=None, onerror=None, udata=None):
            """Send packets to the bridge interface at Layer 2"""
            return self.__sendrcv(self.lb_socket, mpkts, repeat, delay, \
                                  onsend, oncomplete, onerror, udata)

        ########################################################################
        # Send and receive functions
        ########################################################################

        def sr_l2(self, mpkts, repeat=1, delay=None, timeout=None, \
                  onsend=None, oncomplete=None, onerror=None, onreply=None, \
                  onrecv=None, udata=None):
            """Send and receive packets at Layer 2"""
            return self.__sendrcv(self.l2_socket, mpkts, repeat, delay, \
                                  onsend, oncomplete, onerror, timeout, \
                                  onrecv, onreply, udata)

        def sr_l3(self, mpkts, repeat=1, delay=None, timeout=None, \
                  onsend=None, oncomplete=None, onerror=None, onreply=None, \
                  onrecv=None, udata=None):
            """Send and receive packets at Layer 3"""
            return self.__sendrcv(self.l3_socket, mpkts, repeat, delay, \
                                  onsend, oncomplete, onerror, timeout, \
                                  onrecv, onreply, udata)

        def sr_lb(self, mpkts, repeat=1, delay=None, timeout=None, \
                  onsend=None, oncomplete=None, onerror=None, onreply=None, \
                  onrecv=None, udata=None):
            """Send and receive packets at Layer 3"""
            return self.__sendrcv(self.lb_socket, mpkts, repeat, delay, \
                                  onsend, oncomplete, onerror, timeout, \
                                  onrecv, onreply, udata)

        def si_l2(self, mpkt):
            """Send immediate at Layer 2"""
            self.l2_socket.send(mpkt.root)
        def si_l3(self, mpkt):
            """Send immediate at Layer 3"""
            pkt = mpkt.root

            if get_proto_layer(pkt) == 1 and is_proto(pkt.payload):
                log.debug('Ignoring L1 before sending to L3')
                pkt = pkt.payload

            self.l3_socket.send(pkt)

        def si_lb(self, mpkt):
            """Send immediate to the bridge Layer 2"""
            self.lb_socket.send(mpkt.root)

        def __sendrcv(self, sck, mpkts, repeat=1, delay=None, onsend=None, \
                      oncomplete=None, onerror=None, timeout=None, \
                      onrecv=None, onreply=None, udata=None):
            """
            General function used by the various s_l{2,3,b} and sr_l{2,3,b}
            public methods.
            """

            assert sck, 'Socket cannot be null'

            timeout = max(0, timeout)
            delay = max(0, delay)
            #repeat = max(1, repeat)

            send = SendWorker(sck, mpkts, repeat, delay, onsend, oncomplete, \
                              onerror, timeout, onrecv, onreply, udata)

            if callable(onrecv):
                log.debug('Appending to the list of receivers')
                self.receivers.append(send)

            # Than put directly on the queue
            self.thread_pool.queue_work(None, None, self.__worker_thread, send)

            return send

    return AuditContext
