#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
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

from datetime import datetime
from threading import Thread, Lock

import gobject

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.atoms import with_decorator
from umit.pm.manager.preferencemanager import Prefs
from umit.pm.manager.auditmanager import AuditDispatcher

from umit.pm.backend.scapy import *

import select

def register_sniff_context(BaseSniffContext):
    class SniffContext(BaseSniffContext):
        """
        A sniff context for controlling various options.
        """
        has_stop = True
        has_pause = False
        has_restart = True

        def __init__(self, *args, **kwargs):
            BaseSniffContext.__init__(self, *args, **kwargs)

            self.lock = Lock()
            self.prevtime = None
            self.socket = None
            self.internal = True
            self.process = None

            self.title = _('%s capture') % self.iface
            self.summary = _('Sniffing on %s') % self.iface
            self.thread = None
            self.priv = []

            self.audit_dispatcher = None

        @with_decorator
        def get_all_data(self):
            return BaseSniffContext.get_all_data(self)

        @with_decorator
        def get_data(self):
            return BaseSniffContext.get_data(self)

        @with_decorator
        def set_data(self, val):
            self.data = val

        def get_percentage(self):
            if self.state != self.RUNNING:
                return 100.0
            else:
                if self.stop_count or \
                   self.stop_time or \
                   self.stop_size or \
                   self.capmethod == 1:
                    return self.percentage
                else:
                    return None

        def _start(self):
            self.prevtime = datetime.now()

            if self.iface and self.capmethod == 0:
                try:
                    self.socket = conf.L2listen(type=ETH_P_ALL,
                                                iface=self.iface,
                                                filter=self.filter)

                    if self.audits:
                        try:
                            if self.socket.LL in conf.l2types.layer2num:
                                linktype = \
                                         conf.l2types.layer2num[self.socket.LL]
                            elif self.socket.LL in conf.l3types.layer2num:
                                linktype = \
                                         conf.l3types.layer2num[self.socket.LL]
                            else:
                                log.debug('Falling back to IL_TYPE_ETH as DL')
                                linktype = IL_TYPE_ETH
                        except:
                            try:
                                linktype = self.socket.ins.datalink()
                            except:
                                log.debug('It seems that we\'re using PF_PACKET'
                                          ' socket. Using IL_TYPE_ETH as DL')
                                linktype = IL_TYPE_ETH

                        self.audit_dispatcher = AuditDispatcher(linktype)

                except socket.error, (errno, err):
                    self.summary = str(err)
                    return False
                except Exception, err:
                    self.summary = str(err)
                    return False

            self.state = self.RUNNING
            self.internal = True
            self.data = []

            if self.capmethod == 0:
                self.thread = Thread(target=self.run)

            elif self.capmethod == 1 or \
                 self.capmethod == 2 or \
                 self.capmethod == 3:

                self.thread = Thread(target=self.run_helper)

            self.thread.setDaemon(True)
            self.thread.start()

            return True

        def _stop(self):
            if self.internal:
                self.internal = False

                if self.socket:
                    self.socket.close()

                # We have to kill the process directly from here because the
                # select function is blocking to avoid CPU burning.

                if self.process:
                    kill_helper(self.process)
                    self.process = None

                return True
            else:
                return False

        def _restart(self):
            if self.thread and self.thread.isAlive():
                return False

            # Ok reset the counters and begin a new sniff session
            self.tot_size = 0
            self.tot_time = 0
            self.tot_count = 0

            return self._start()

        def run_helper(self):
            """
            This function is the thread main procedure for the thread that spawn
            a new process like tcpdump to avoid packet loss and reads MetaPacket
            from the pcap file managed from a private process.
            """

            errstr = reader = None

            try:
                if self.capmethod == 1:
                    log.debug("I'm using virtual interface method")
                    outfile = self.cap_file
                else:
                    # Run tcpdump or dumpcap
                    self.process, outfile = run_helper(self.capmethod - 2,
                                                       self.iface,
                                                       self.filter,
                                                       self.stop_count,
                                                       self.stop_time,
                                                       self.stop_size)

                for reader in bind_reader(self.process, outfile):
                    if not self.internal:
                        break

                    if reader:
                        reader, outfile_size, position = reader

            except OSError, err:
                errstr = err.strerror
                self.internal = False
            except Exception, err:
                errstr = str(err)
                self.internal = False

            reported_packets = 0

            log.debug("Entering in the main loop")

            if self.audits:
                self.audit_dispatcher = AuditDispatcher(reader.linktype)

            while self.internal:

                if self.capmethod != 1:
                    report_idx = get_n_packets(self.process)

                    if report_idx < reported_packets:
                        continue

                while self.capmethod == 1 or reported_packets < report_idx:

                    pkt = reader.read_packet()

                    if not pkt:
                        break

                    pkt = MetaPacket(pkt)
                    packet_size = pkt.get_size()

                    if not pkt:
                        continue

                    if self.max_packet_size and \
                       packet_size - self.max_packet_size > 0:

                        log.debug("Skipping current packet (max_packet_size)")
                        continue

                    if self.min_packet_size and \
                       packet_size - self.min_packet_size < 0:

                        log.debug("Skipping current packet (min_packet_size)")
                        continue

                    self.tot_count += 1
                    self.tot_size += packet_size

                    now = datetime.now()
                    delta = now - self.prevtime
                    self.prevtime = now

                    if delta == abs(delta):
                        self.tot_time += delta.seconds

                    self.data.append(pkt)
                    reported_packets += 1

                    if self.audit_dispatcher:
                        self.audit_dispatcher.feed(pkt)

                    if self.callback:
                        self.callback(pkt, self.udata)

                    lst = []

                    # tcpdump and dumpcap offers this
                    if self.capmethod < 2 and self.stop_count:
                        lst.append(float(float(self.tot_count) /
                                         float(self.stop_count)))
                    # Only dumpcap here
                    if self.capmethod != 3 and self.stop_time:
                        lst.append(float(float(self.tot_time) /
                                         float(self.stop_time)))
                    if self.capmethod != 3 and self.stop_size:
                        lst.append(float(float(self.tot_size) /
                                         float(self.stop_size)))

                    if self.capmethod == 1:
                        lst.append(position() / outfile_size)

                    if lst:
                        self.percentage = float(float(sum(lst)) /
                                                float(len(lst))) * 100.0

                        if self.percentage >= 100:
                            self.internal = False
                    else:
                        # ((goject.G_MAXINT / 4) % gobject.G_MAXINT)
                        self.percentage = (self.percentage + 536870911) % \
                                          gobject.G_MAXINT

                report_idx = reported_packets

            log.debug("Exiting from thread")

            if self.process:
                kill_helper(self.process)

            self.exit_from_thread(errstr)

        def run(self):
            errstr = None

            while self.internal and self.socket is not None:
                r = None
                inmask = [self.socket]

                try:
                    if WINDOWS:
                        try:
                            r = self.socket.recv(MTU)
                        except PcapTimeoutElapsed:
                            continue
                    else:
                        inp, out, err = select.select(inmask, inmask, inmask, None)
                        if self.socket in inp:
                            r = self.socket.recv(MTU)
                    if r is None:
                        continue

                    self.priv.append(r)
                except Exception, err:
                    # Ok probably this is an exception raised when the select
                    # is runned on already closed socket (see also _stop)
                    # so avoid throwing this exception.

                    if self.internal:
                        errstr = str(err)

                    self.internal = False
                    self.socket = None
                    break

            self.exit_from_thread(errstr)

        def exit_from_thread(self, errstr=None):
            log.debug("Exiting from thread")

            self.priv = []

            self.state = self.NOT_RUNNING
            self.percentage = 100.0
            status = ""

            if self.tot_size >= 1024 ** 3:
                status = "%.1f GB/" % (self.tot_size / (1024.0 ** 3))
            elif self.tot_size >= 1024 ** 2:
                status = "%.1f MB/" % (self.tot_size / (1024.0 ** 2))
            else:
                status = "%.1f KB/" % (self.tot_size / (1024.0))

            if self.tot_time >= 60 ** 2:
                status += "%d h/" % (self.tot_time / (60 ** 2))
            elif self.tot_time >= 60:
                status += "%d m/" % (self.tot_time / 60)
            else:
                status += "%d s/" % (self.tot_time)

            status += "%d pks" % (self.tot_count)

            if errstr:
                self.summary = _('Error: %s (%s)') % (errstr, status)
            else:
                self.summary = _('Finished sniffing on %s (%s)') % (self.iface,
                                                                    status)

            if self.callback:
                self.callback(None, self.udata)

        def check_finished(self):
            if self.capmethod != 0:
                return

            priv = self.priv
            self.priv = []

            for r in priv:
                # This code should not be in the thread and called in the
                # main thread of the GUI so we can avoid packet loss.
                # It's better to have a temporary list object to store raw
                # packets captured from socket.recv(MTU) function and then joins
                # everything in self.data

                packet = MetaPacket(r)
                packet_size = packet.get_size()

                if self.max_packet_size and \
                   packet_size - self.max_packet_size > 0:

                    log.debug("Skipping current packet (max_packet_size)")
                    continue

                if self.min_packet_size and \
                   packet_size - self.min_packet_size < 0:

                    log.debug("Skipping current packet (min_packet_size)")
                    continue

                self.tot_count += 1
                self.tot_size += packet.get_size()

                now = datetime.now()
                delta = now - self.prevtime
                self.prevtime = now

                if delta == abs(delta):
                    self.tot_time += delta.seconds

                self.data.append(packet)

                if self.audit_dispatcher:
                    self.audit_dispatcher.feed(packet)

                # FIXME: This probably should be moved inside the run() function
                if self.callback:
                    self.callback(packet, self.udata)

                lst = []

                if self.stop_count:
                    lst.append(float(float(self.tot_count) /
                                     float(self.stop_count)))
                if self.stop_time:
                    lst.append(float(float(self.tot_time) /
                                     float(self.stop_time)))
                if self.stop_size:
                    lst.append(float(float(self.tot_size) /
                                     float(self.stop_size)))

                if lst:
                    self.percentage = float(float(sum(lst)) /
                                            float(len(lst))) * 100.0

                    if self.percentage >= 100:
                        self.internal = False
                else:
                    # ((goject.G_MAXINT / 4) % gobject.G_MAXINT)
                    self.percentage = (self.percentage + 536870911) % 2147483647

    return SniffContext
