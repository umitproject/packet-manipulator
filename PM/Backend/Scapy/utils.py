#!/usr/bin/env python                                   
# -*- coding: utf-8 -*-                                 
# Copyright (C) 2008 Adriano Monteiro Marques           
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
import sys

from datetime import datetime
from threading import Thread, Lock, Condition
from collections import defaultdict

from PM.Core.Logger import log
from PM.Core.Atoms import Node, ThreadPool

from PM.Backend import VirtualIFace
from PM.Backend.Scapy.wrapper import *
from PM.Backend.Scapy.packet import MetaPacket

def get_iface_from_ip(metapacket):
    if metapacket.haslayer(IP):
        iff, a, gw = conf.route.route(metapacket.getlayer(IP).dst)
        log.debug("Using %s interface to send packet to %s" % (iff, metapacket.root.dst))
    else:
        iff = conf.iface
        log.debug("Using default %s interface" % iff)

    return iff

def get_socket_for(metapacket, want_layer_2=False):
    # We should check if the given packet has a IP layer but not an
    # Ether one so we could send it trough layer 3

    iff = get_iface_from_ip(metapacket)

    if not metapacket.haslayer(Ether) and not want_layer_2:
        sock = conf.L3socket(iface=iff)
    else:
        log.debug("Using layer 2 socket (Ether: %s Layer 2: %s)" % \
                 (metapacket.haslayer(Ether), want_layer_2))
        sock = conf.L2socket(iface=iff)

    return sock

###############################################################################
# Analyze functions
###############################################################################

def analyze_connections(pktlist, strict=False):
    # Doesn't work with strict = True :(
    # but without strict is also more speedy so :)

    tree = {}

    for packet in pktlist:
        hashret = packet.root.hashret()
        append = False
        last = 0

        for (idx, hash, pkt) in tree:
            last = max(last, idx)

            if hash == hashret:
                lst = tree[(idx, hash, pkt)]

                if strict:
                    for child in lst:
                        if child.root.answers(packet.root):
                            lst.append(packet)
                            append = True
                            break
                else:
                    lst.append(packet)
                    append = True

                break

        if not append:
            tree[(last + 1, hashret, packet)] = []

    items = tree.items()
    items.sort()

    return [(packet, lst) for (idx, hash, packet), lst in tree.items()]

###############################################################################
# Routing related functions
###############################################################################

def route_resync():
    conf.route.resync()

def route_list():
    for net, msk, gw, iface, addr in conf.route.routes:
        yield (ltoa(net), ltoa(msk), gw, iface, addr)

def route_add(self, host, net, gw, dev):
    conf.route.add({'host':host, 'net':net, 'gw':gw, 'dev':dev})

def route_remove(self, host, net, gw, dev):
    conf.route.delt({'host':host, 'net':net, 'gw':gw, 'dev':dev})

###############################################################################
# Sniffing related functions
###############################################################################

def find_all_devs():
    ifaces = get_if_list()

    ips = []
    hws = []
    for iface in ifaces:
        ip = "0.0.0.0"
        hw = "00:00:00:00:00:00"
        
        try:
            ip = get_if_addr(iface)
        except Exception:
            pass

        try:
            hw = get_if_hwaddr(iface)
        except Exception:
            pass

        ips.append(ip)
        hws.append(hw)

    ret = []
    for iface, ip, hw in zip(ifaces, ips, hws):
        ret.append(VirtualIFace(iface, hw, ip))

    return ret

###############################################################################
# Send Context functions
###############################################################################

def _send_packet(sock, metapacket, count, inter, callback, udata):
    packet = metapacket.root

    try:
        while count > 0:
            sock.send(packet)
            count -= 1

            if callback(metapacket, udata) == True:
                return

            time.sleep(inter)

    except socket.error, (errno, err):
        callback(Exception(err), udata)
        return

    callback(None, udata)

def send_packet(metapacket, count, inter, callback, udata=None):
    """
    Send a metapacket in thread context

    @param metapacket the packet to send
    @param count send n count metapackets
    @param inter interval between two consecutive sends
    @param callback a callback to call at each send (of type packet, udata)
           when True is returned the send thread is stopped
    @param udata the userdata to pass to the callback
    """

    try:
        sock = get_socket_for(metapacket)
    except socket.error, (errno, err):
        raise Exception(err)

    send_thread = Thread(target=_send_packet, args=(sock, metapacket, count, inter, callback, udata))
    send_thread.setDaemon(True) # avoids zombies
    send_thread.start()

    return send_thread

###############################################################################
# SendReceive Context functions
###############################################################################

def _sndrecv_sthread(wrpipe, socket, packet, count, inter, callback, udata):
    try:
        for idx in xrange(count):
            socket.send(packet)

            if callback(MetaPacket(packet), idx, udata):
                break

            time.sleep(inter)
    except SystemExit:
        pass
    except Exception, err:
        print "Error in _sndrecv_sthread(PID: %d EXC: %s)" % (os.getpid(), str(err))
    else:
        cPickle.dump(arp_cache, wrpipe)
        wrpipe.close()

def _sndrecv_rthread(sthread, rdpipe, socket, packet, count, \
                     strict, callback, udata):
    ans = 0
    nbrecv = 0
    notans = count

    force_exit = False
    packet_hash = packet.hashret()

    inmask = [socket, rdpipe]

    while True:
        r = None
        if FREEBSD or DARWIN:
            inp, out, err = select(inmask, [], [], 0.05)
            if len(inp) == 0 or socket in inp:
                r = socket.nonblock_recv()
        elif WINDOWS:
            r = socket.recv(MTU)
        else:
            inp, out, err = select(inmask, [], [], None)
            if len(inp) == 0:
                return
            if socket in inp:
                r = socket.recv(MTU)
        if r is None:
            continue

        if not strict or r.hashret() == packet_hash and r.answers(packet):
            ans += 1

            if notans:
                notans -= 1

            if callback(MetaPacket(r), True, udata):
                force_exit = True
                break
        else:
            nbrecv += 1

            if callback(MetaPacket(r), False, udata):
                force_exit = True
                break

        if notans == 0:
            break
    
    try:
        ac = cPickle.load(rdpipe)
    except EOFError:
        print "Child died unexpectedly. Packets may have not been sent"
    else:
        arp_cache.update(ac)

    if sthread and sthread.isAlive():
        sthread.join()

    if not force_exit:
        callback(None, False, udata)

def send_receive_packet(metapacket, count, inter, iface, strict, \
                        scallback, rcallback, sudata=None, rudata=None):
    """
    Send/receive a metapacket in thread context

    @param metapacket the packet to send
    @param count send n count metapackets
    @param inter interval between two consecutive sends
    @param iface the interface where to wait for replies
    @param strict strict checking for reply
    @param callback a callback to call at each send
           (of type packet, packet_idx, udata)
    @param sudata the userdata to pass to the send callback
    @param callback a callback to call at each receive
          (of type reply_packet, is_reply, received, answers, remaining)
    @param sudata the userdata to pass to the send callback
    """
    packet = metapacket.root

    if not isinstance(packet, Gen):
        packet = SetGen(packet)

    if not count or count <= 0:
        count = 1

    try:
        sock = get_socket_for(metapacket, True)
        sock_send = get_socket_for(metapacket)

        if not sock:
            raise Exception('Unable to create a valid socket')
    except socket.error, (errno, err):
        raise Exception(err)

    rdpipe, wrpipe = os.pipe()
    rdpipe = os.fdopen(rdpipe)
    wrpipe = os.fdopen(wrpipe, 'w')

    send_thread = Thread(target=_sndrecv_sthread,
                           args=(wrpipe, sock_send, packet, count,
                                 inter, scallback, sudata))
    recv_thread = Thread(target=_sndrecv_rthread,
                           args=(send_thread, rdpipe, sock, packet,
                                 count, strict, rcallback, rudata))

    send_thread.setDaemon(True)
    recv_thread.setDaemon(True)

    send_thread.start()
    recv_thread.start()

    return send_thread, recv_thread

###############################################################################
# Sequence Context functions
###############################################################################

class SequenceConsumer(object):
    def __init__(self, tree, count, inter, strict, \
                 scallback, rcallback, sudata, rudata, excback):

        assert len(tree) > 0

        self.tree = tree
        self.count = max(count, 1)
        self.inter = inter
        self.strict = strict
        self.timeout = 10

        self.sockets = []
        self.recv_list = defaultdict(list)
        self.receiving = False

        self.internal = False
        self.running = Condition()

        self.pool = ThreadPool(2, 10)
        self.pool.queue_work(None, self.__notify_exc, self.__check)

        self.scallback = scallback
        self.rcallback = rcallback
        self.excback = excback

        self.sudata, self.rudata = sudata, rudata

        log.debug("%d total packets to send for %d times" % (len(tree), self.count))

    def isAlive(self):
        return self.internal

    def stop(self):
        self.internal = False

        self.pool.stop()
        #self.pool.join_threads()

    def start(self):
        if self.internal or self.receiving:
            log.debug("Pool already started")
            return

        self.receiving = True
        self.internal = True

        self.pool.start()

    def __check(self):
        # This is a function to allow the sequence
        # to be respawned n times

        self.receiving = True
        self.running.acquire()

        while self.internal and self.count > 0:
            log.debug("Next step %d" % self.count)

            self.__notify_send(None)
            self.pool.queue_work(None, self.__notify_exc, self.__recv_worker)

            for node in self.tree.get_children():
                log.debug("Adding first packet of the sequence")
                self.pool.queue_work(None, self.__notify_exc, self.__send_worker, node)
                break

            self.running.wait()

            self.count -= 1

        log.debug("Waiting end..")

        self.running.wait()
        self.running.release()

        if not self.internal:
            log.debug("Stopping the thread pool (async)")
            self.pool.stop()

    def __recv_worker(self):
        # Here we should receive the packet and check against
        # recv_list if the packet match remove from the list
        # and start another send_worker

        if self.timeout is not None:
            stoptime = time.time() + self.timeout

        while self.internal and self.receiving:
            r = []
            inmask = [socket for socket, refcount in self.sockets]

            if self.timeout is not None:
                remain = stoptime - time.time()

                if remain <= 0:
                    self.receiving = False
                    break

            if FREEBSD or DARWIN:
                inp, out, err = select(inmask, [], [], 0.05)

                for sock in inp:
                    r.append(sock.nonblock_recv())

            elif WINDOWS:
                for sock in inmask:
                    r.append(sock.recv(MTU))
            else:
                inp, out, err = select(inmask, [], [], 0.05)

                for sock in inp:
                    r.append(sock.recv(MTU))

            if not r:
                continue

            if self.timeout is not None:
                stoptime = time.time() + self.timeout

            for precv in r:

                if precv is None:
                    continue

                is_reply = True
                my_node = None
                requested_socket = None

                if self.strict:
                    is_reply = False
                    hashret = precv.hashret()

                    if hashret in self.recv_list:
                        for (idx, sock, node) in self.recv_list[hashret]:
                            packet = node.get_data().packet.root

                            if precv.answers(packet):
                                requested_socket = sock
                                my_node = node
                                is_reply = True

                                break

                elif not self.strict and my_node is None:
                    # Get the first packet

                    list = [(v, k) for k, v in self.recv_list.items()]
                    list.sort()

                    requested_socket = list[0][0][0][1]
                    my_node = list[0][0][0][2]
                else:
                    continue

                # Now cleanup the sockets
                for idx in xrange(len(self.sockets)):
                    if self.sockets[idx][0] == requested_socket:
                        self.sockets[idx][1] -= 1

                        if self.sockets[idx][1] == 0:
                            self.sockets.remove(self.sockets[idx])

                        break

                if is_reply:
                    self.__notify_recv(my_node, MetaPacket(precv), is_reply)

                    # Queue another send thread
                    for node in my_node.get_children():
                        self.pool.queue_work(None, self.__notify_exc,
                                             self.__send_worker, node)
                else:
                    self.__notify_recv(None, MetaPacket(precv), is_reply)

        log.debug("Trying to exit")

        self.running.acquire()
        self.running.notify()
        self.running.release()

        self.receiving = False

        self.__notify_recv(None, None, False)

    def __send_worker(self, node):
        if not self.internal:
            log.debug("Discarding packet")
            return

        obj = node.get_data()

        sock = get_socket_for(obj.packet)

        if node.is_parent():
            # Here we should add the node to the dict
            # to check the the replies for a given time
            # and continue the sequence with the next
            # depth.

            try:
                idx = self.sockets.index(sock)
                self.sockets[idx][1] += 1
            except:
                self.sockets.append([sock, 1])

            key = obj.packet.root.hashret()
            self.recv_list[key].append((len(self.recv_list), sock, node))

            log.debug("Adding socket to the list for receiving my packet %s" % sock)

        sock.send(obj.packet.root)

        self.__notify_send(node)

        log.debug("Sleeping %f after send" % self.inter)
        time.sleep(self.inter + obj.inter)

        if self.internal and node.get_parent():

            parent = node.get_parent()
            next = parent.get_next_of(node)

            if next:
                log.debug("Processing next packet")
                self.pool.queue_work(None, self.__notify_exc, self.__send_worker, next)

            else:
                log.debug("Last packet of this level")
        else:
            log.debug("Last packet sent")

    def __notify_exc(self, exc):
        self.scallback = None
        self.rcallback = None

        if isinstance(exc, socket.error):
            exc = Exception(str(exc[1]))

        if self.excback:
            self.excback(exc)
        else:
            log.debug("Exception not properly handled. Dumping:")

            import traceback
            traceback.print_exc(file=sys.stdout)

        self.stop()

    def __notify_send(self, node):
        log.debug("Packet sent")

        if not self.scallback:
            return

        packet = None
        parent = False
        
        if node is not None:
            packet = node.get_data().packet
            parent = node.is_parent()

        if self.scallback(packet, parent, self.sudata):

            log.debug("send_callback want to exit")
            self.internal = False

    def __notify_recv(self, node, reply, is_reply):
        log.debug("Packet received (is reply? %s)" % is_reply)

        if not self.rcallback:
            return

        packet = None
        
        if node is not None:
            packet = node.get_data().packet

        if self.rcallback(packet, reply, is_reply, self.rudata):

            log.debug("recv_callback want to exit")
            self.internal = False

def execute_sequence(sequence, count, inter, strict, iface, \
                     scallback, rcallback, sudata, rudata, excback):

    consumer = SequenceConsumer(sequence, count, inter, strict, \
                                scallback, rcallback, sudata, rudata, excback)
    consumer.start()

    return consumer
