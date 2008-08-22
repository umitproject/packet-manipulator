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
from threading import Thread, Lock

from PM.Core.Logger import log

from PM.Backend import VirtualIFace
from PM.Backend.Scapy.wrapper import *
from PM.Backend.Scapy.packet import MetaPacket

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

def _send_packet(metapacket, count, inter, callback, udata):
    packet = metapacket.root

    try:
        while count > 0:
            sendp(packet, 0, 0)
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
    send_thread = Thread(target=_send_packet, args=(metapacket, count, inter, callback, udata))
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

            if callback(packet, idx, udata):
                break

            time.sleep(inter)
    except SystemExit:
        pass
    except Exception, err:
        print "Error in _sndrecv_sthread(PID: %d EXC: %s)" % (os.getpid(), str(err))
    else:
        cPickle.dump(arp_cache, wrpipe)
        wrpipe.close()

def _sndrecv_rthread(sthread, rdpipe, socket, packet, count, callback, udata):
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

        if r.hashret() == packet_hash and r.answers(packet):
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

def send_receive_packet(metapacket, count, inter, iface, scallback, rcallback, sudata=None, rudata=None):
    """
    Send/receive a metapacket in thread context

    @param metapacket the packet to send
    @param count send n count metapackets
    @param inter interval between two consecutive sends
    @param iface the interface where to wait for replies
    
    @param callback a callback to call at each send (of type packet, packet_idx, udata)
    @param sudata the userdata to pass to the send callback

    @param callback a callback to call at each receive (of type reply_packet, is_reply, received, answers, remaining)
    @param sudata the userdata to pass to the send callback
    """
    packet = metapacket.root

    if not isinstance(packet, Gen):
        packet = SetGen(packet)

    if not count or count <= 0:
        count = 1

    try:
        sock = conf.L2socket(iface=iface)

        if not sock:
            raise Exception('Unable to create a valid socket')
    except socket.error, (errno, err):
        raise Exception(err)

    rdpipe, wrpipe = os.pipe()
    rdpipe = os.fdopen(rdpipe)
    wrpipe = os.fdopen(wrpipe, 'w')

    send_thread = Thread(target=_sndrecv_sthread,
                                   args=(wrpipe, sock, packet, count, inter, scallback, sudata))
    recv_thread = Thread(target=_sndrecv_rthread,
                                   args=(send_thread, rdpipe, sock, packet, count, rcallback, rudata))

    send_thread.setDaemon(True)
    recv_thread.setDaemon(True)

    send_thread.start()
    recv_thread.start()

    return send_thread, recv_thread

###############################################################################
# Sequence Context functions
###############################################################################

def _next_packet(seq):
    # yeah we love generators

    idx = 0
    path = [0, ]

    while path[0] != len(seq):
        iter = seq

        log.debug("Path is %s" % path)

        for path_idx in xrange(len(path)):
            if path[path_idx] == len(iter):
                path = path[0:path_idx]
                idx = len(path) - 1

                path[idx] += 1

                iter = seq
                for i in path:
                    try:
                        iter = iter[i]
                    except:
                        raise StopIteration

                break
            else:
                iter = iter[path[path_idx]]

        log.debug("Yielding object at path %s" % path)
        yield iter

        if iter.conditional:
            path += [0]
            idx += 1
        else:
            path[idx] += 1

    raise StopIteration

def _execute_sequence(sock, seq, count, inter, strict, scall, rcall, sudata, rudata):
    # So we have to analyze the Sequence extract the current packet
    # send it on the wire and check the reply if conditional is != []

    try:
        for i in xrange(count):
     
            log.debug("Pass %d of %d total loops" % (i, count))
     
            scall(None, None, sudata)
 
            for seq_iter in _next_packet(seq):
 
                packet = seq_iter.packet.root
                filter = seq_iter.filter
 
                want_reply = (seq_iter.conditional != [])
 
                sock.send(packet)

                log.debug("Packet %s sent" % seq_iter.packet.summary())
                log.debug("Sleeping %.2f" % (inter + seq_iter.inter))

                time.sleep(inter + seq_iter.inter)
 
                if scall(seq_iter.packet, want_reply, sudata):
                    log.debug("scallback want to exit")
                    raise StopIteration # ugly :D
 
                if want_reply:
                    # TODO: here we should check for a reply for a given time
                    # passed from the user like the filter? then if the the
                    # reply is received continue else drop the depth child from
                    # the sequence and go with the next

                    log.debug("Waiting a reply ...")
 
                    packet_hash = packet.hashret()
 
                    inmask = [sock]
 
                    while True:
                        r = None
                        if FREEBSD or DARWIN:
                            inp, out, err = select(inmask, [], [], 0.05)
                            if len(inp) == 0 or sock in inp:
                                r = sock.nonblock_recv()
                        elif WINDOWS:
                            r = sock.recv(MTU)
                        else:
                            inp, out, err = select(inmask, [], [], None)
                            if len(inp) == 0:
                                return
                            if sock in inp:
                                r = sock.recv(MTU)
                        if r is None:
                            continue

                        log.debug("Captured a packet %s" % MetaPacket(r).summary())

                        reply = False

                        if (not strict) or \
                           (strict and r.hashret() == packet_hash and r.answers(packet)):
                            reply = True

                        if rcall(seq_iter.packet, MetaPacket(r), reply, rudata):
                            log.debug("rcallback want to exit")
                            raise StopIteration # ugly :D

    except StopIteration:
        log.debug("Stop iteration by user request")
    finally:
        rcall(None, None, False, rudata)

    log.debug("Sequence end")

def execute_sequence(sequence, count, inter, iface, strict,
                        scallback, rcallback, sudata, rudata):

    if not count or count <= 0:
        count = 1

    try:
        sock = conf.L2socket(iface=iface)

        if not sock:
            raise Exception('Unable to create a valid socket')
    except socket.error, (errno, err):
        raise Exception(err)

    thread = Thread(target=_execute_sequence,
                    args=(sock, sequence, count, inter, strict,
                          scallback, rcallback, sudata, rudata))
    thread.setDaemon(True)
    thread.start()

    log.debug("sequence thread created (count: %d interval: %d)" % (count, inter))

    return thread
