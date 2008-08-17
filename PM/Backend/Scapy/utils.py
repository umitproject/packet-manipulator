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

from PM.Backend import VirtualIFace
from PM.Backend.Scapy.wrapper import *
from PM.Backend.Scapy.packet import MetaPacket

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
