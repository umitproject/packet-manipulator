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

"""
TCP protocol dissector

>>> from PM.Core.AttackUtils import attack_unittest
>>> attack_unittest('-f ethernet,ip,tcp', 'wrong-checksum.pcap')
decoder.ip.notice Invalid IP packet from 127.0.0.1 to 127.0.0.1 : wrong checksum 0xdead instead of 0x7bce
decoder.tcp.notice Invalid TCP packet from 127.0.0.1 to 127.0.0.1 : wrong checksum 0x29a instead of 0xc86
"""

from datetime import datetime
from struct import pack, unpack
from socket import inet_aton, ntohl, inet_ntoa

from PM.Core.Logger import log
from PM.Gui.Plugins.Core import Core
from PM.Core.Atoms import defaultdict
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import AttackManager, OfflineAttack
from PM.Core.NetConst import *
from PM.Core.AttackUtils import checksum

TCP_ESTABLISHED = 1
TCP_SYN_SENT    = 2
TCP_SYN_RECV    = 3
TCP_FIN_WAIT1   = 4
TCP_FIN_WAIT2   = 5
TCP_TIME_WAIT   = 6
TCP_CLOSE       = 7
TCP_CLOSE_WAIT  = 8
TCP_LAST_ACK    = 9
TCP_LISTEN      = 10
TCP_CLOSING     = 11

FIN_SENT = 120
FIN_CONFIRMED = 121

def get_wscale(mpkt):
    return get_ts(mpkt, 3)

def get_ts(mpkt, opt_type=8):
    opt_start = 20
    opt_end = mpkt.get_field('tcp.dataofs') * 4
    tcpraw = mpkt.get_field('tcp')[:opt_end]

    ret = 0
    out = 0

    while opt_start < opt_end:
        val = ord(tcpraw[opt_start])

        if val == 0:
            return ret, out
        elif val == 1:
            opt_start +=1
            continue
        elif opt_type == 3 and val == 3: # WSCALE
            out = 1 << min(ord(tcpraw[opt_start + 2]), 14)
            ret = 1
        elif opt_type == 8 and val == 8: # TIMESTAMP
            out = unpack("!I", tcpraw[opt_start + 2: opt_start + 2 + 4])[0]
            ret = 1

        if ord(tcpraw[opt_start + 1]) < 2:
            return ret, out

        opt_start += ord(tcpraw[opt_start + 1])

    return ret, out

class Buffer(object):
    def __init__(self):
        self.prev, self.next = None, None
        self.data = ''

        self.fin = None
        self.urg = None
        self.seq = 0
        self.ack = 0

class HalfStream(object):
    def __init__(self):
        self.state = 0
        self.seq = 0
        self.first_data_seq = 0
        self.ack_seq = 0
        self.window = 0

        self.ts_on = 0
        self.wscale_on = 0
        self.curr_ts = 0
        self.wscale = 1
        self.urg_ptr = 0
        self.urg_seen = 0
        self.urg_count = 0

        self.rmem_alloc = 0
        self.count_new = 0
        self.data = ''
        self.urgdata = ''

        self.plist = None
        self.plist_tail = None

    def get_count(self): return len(self.data)

    count = property(get_count)

class TCPStream(object):
    CONN_UNDEFINED        = -1
    CONN_JUST_ESTABLISHED = 0
    CONN_DATA             = 1
    CONN_RESET            = 2
    CONN_CLOSE            = 3
    CONN_TIMED_OUT        = 4

    def __init__(self, source, dest, sport, dport):
        self.reset(source, dest, sport, dport)

    def reset(self, source, dest, sport, dport):
        self.source = source
        self.dest = dest
        self.sport = sport
        self.dport = dport

        self.state = TCPStream.CONN_UNDEFINED

        self.client = HalfStream()
        self.server = HalfStream()

        self.next_node, self.prev_node = None, None
        self.next_time, self.prev_time = None, None
        self.next_free = None

        self.listeners = []

    def __hash__(self):
        return hash(self.source) ^ hash(self.sport) ^ \
               hash(self.dest) ^ hash(self.dport)

class TCPTimeout(object):
    def __init__(self, stream, timeout):
        self.stream = stream
        self.timeout = timeout
        self.next, self.prev = None, None

class Reassembler(object):
    """
    All the code of reassembler is ripped out from libnids-1.23 with minor
    modifications to obtain a light version of it.

    I've to report the copyright of the original author relative to this code:

    Copyright (c) 1999 Rafal Wojtczuk <nergal@avet.com.pl>. All rights reserved.

    The code is released as GPLv2 so no problem about integration.
    """

    def __init__(self, workarounds=True, maxstreams=30):
        self.tcp_workarounds = workarounds
        self.n_streams, self.max_streams = 0, maxstreams
        self.oldest_stream, self.latest_stream = None, None

        self.tcp_streams = {}
        self.free_streams = None
        self.tcp_timeouts = None

        for i in xrange(self.max_streams):
            stream = TCPStream(None, None, None, None)

            if self.free_streams:
                stream.next_free = self.free_streams

            self.free_streams = stream

        self.analyzers = []

    def add_analyzer(self, analyzer):
        self.analyzers.append(analyzer)

    def process_icmp(self, mpkt):
        """
        Process an ICMP packet
        @param mpkt a MetaPacket object
        """
        iplen = mpkt.get_field('ip.len') - (mpkt.get_field('ip.ihl') << 2)

        if iplen < 20:
            return
        ipsrc, ipdst = inet_aton(mpkt.get_field('ip.src')), \
                       inet_aton(mpkt.get_field('ip.dst'))

        # Proto or port unreach
        if mpkt.get_field('ip.code') in (2, 3) and \
           ipsrc != ipdst:
            return

        if mpkt.get_field('ip.proto') != NL_TYPE_TCP:
            return

        is_client, stream = self.find_stream(mpkt)

        if not stream:
            return

        if stream.dest == ipdst:
            hlf = stream.server
        else:
            hlf = stream.client

        if hlf.state not in (TCP_SYN_SENT, TCP_SYN_RECV):
            return

        stream.state = stream.CONN_RESET

        for listener in stream.listeners:
            listener(stream, mpkt, None)

        self.free_tcp_stream(stream)

    def process_tcp(self, mpkt):
        """
        Process a TCP packet
        @param mpkt a MetaPacket object
        """
        datalen = mpkt.get_field('ip.len') - \
                  4 * mpkt.get_field('ip.ihl') - \
                  4 * (mpkt.get_field('tcp.dataofs') or 0)

        if datalen < 0:
            log.warning('Bogus TCP/IP header (datalen < 0)')
            return

        ipsrc, ipdst = inet_aton(mpkt.get_field('ip.src')),\
                       inet_aton(mpkt.get_field('ip.dst'))

        if ipsrc == '\x00\x00\x00\x00' and \
           ipdst == '\x00\x00\x00\x00':
            log.warning('Bogus IP header (src or dst are NULL)')
            return

        tcpflags = mpkt.get_field('tcp.flags')

        if not tcpflags:
            return

        is_client, stream = self.find_stream(mpkt)

        if not stream:
            if tcpflags & TH_SYN and \
               not tcpflags & TH_ACK and not tcpflags & TH_RST:

                self.add_new_tcp(mpkt)
                return is_client, self.latest_stream

            return

        if is_client:
            snd, rcv = stream.client, stream.server
        else:
            snd, rcv = stream.server, stream.client

        tcpseq = mpkt.get_field('tcp.seq')
        tcpack = mpkt.get_field('tcp.ack')

        if tcpflags & TH_SYN:
            if is_client or stream.client.state != TCP_SYN_SENT or \
               stream.server.state != TCP_CLOSE or not tcpflags & TH_ACK:
                return

            if stream.client.seq != tcpack:
                return

            stream.server.state = TCP_SYN_RECV
            stream.server.seq = \
            stream.server.first_data_seq = tcpseq + 1
            stream.server.ack_seq = tcpack
            stream.server.window = mpkt.get_field('tcp.window')

            if stream.client.ts_on:
                stream.server.ts_on, stream.server.curr_ts = get_ts(mpkt)

                if not stream.server.ts_on:
                    stream.client.ts_on = 0
            else:
                stream.server.ts_on = 0

            if stream.client.wscale_on:
                stream.server.wscale_on, stream.server.wscale = get_wscale(mpkt)

                if not stream.server.wscale_on:
                    stream.client.wscale_on = 0
                    stream.client.wscale = 1
                    stream.server.wscale = 1
            else:
                stream.server.wscale_on = 0
                stream.server.wscale = 1

        if not (not datalen and tcpseq == rcv.ack_seq) and \
           (not (tcpseq - (rcv.ack_seq + rcv.window * rcv.wscale) <= 0) or \
            (tcpseq + datalen) - rcv.ack_seq < 0):
            return

        if tcpflags & TH_RST:
            if stream.state == stream.CONN_DATA:
                stream.state = stream.CONN_RESET

                for listener in stream.listeners:
                    listener(stream, mpkt, None)

            self.free_tcp_stream(stream)
            return

        ts_on, ts_val = get_ts(mpkt)
        if rcv.ts_on and ts_on and ts_val - snd.curr_ts < 0:
            return

        if tcpflags & TH_ACK:
            if is_client and stream.client.state == TCP_SYN_SENT and \
               stream.server.state == TCP_SYN_RECV:
                if tcpack == stream.server.seq:
                    stream.client.state = TCP_ESTABLISHED
                    stream.client.ack_seq = tcpack

                    stream.server.state = TCP_ESTABLISHED
                    stream.state = stream.CONN_JUST_ESTABLISHED

                    for callback in self.analyzers:
                        callback(stream, mpkt)

                    if not stream.listeners:
                        self.free_tcp_stream(stream)
                        return

                    stream.state = stream.CONN_DATA

        if tcpflags & TH_ACK:
            if tcpack - snd.ack_seq > 0:
                snd.ack_seq = tcpack

            if rcv.state == FIN_SENT:
                rcv.state = FIN_CONFIRMED
            if rcv.state == FIN_CONFIRMED and snd.state == FIN_CONFIRMED:
                stream.state = stream.CONN_CLOSE

                for listener in stream.listeners:
                    listener(stream, mpkt, None)

                self.free_tcp_stream(stream)
                return

        if (datalen + (tcpflags & TH_FIN)) > 0:
            payload = mpkt.get_field('tcp')[mpkt.get_field('tcp.dataofs') * 4:]

            if payload:
                self.tcp_queue(stream, mpkt, snd, rcv, payload, datalen)

        snd.window = mpkt.get_field('tcp.window')

        if rcv.rmem_alloc > 65535:
            self.prune_queue(rcv)

        return is_client, stream

    def prune_queue(self, rcv):
        """
        Prune a pending queue by freeing all the data
        @param rcv a HalfStream instance
        """

        log.warn('Pruning queue.')

        p = rcv.plist

        while p:
            del p.data
            tmp = p.next
            del p
            p = tmp

        rcv.plist = rcv.plist_tail = None
        rcv.rmem_alloc = 0

    def add2buf(self, mpkt, rcv, data):
        rcv.data += data
        rcv.count_new = len(data)

    def notify(self, mpkt, stream, rcv):
        for listener in stream.listeners:
            ret = listener(stream, mpkt, rcv)

            if ret == INJ_COLLECT_MORE:
                print 'Collecting more packets'
            else:
                rcv.count_new = 0
                rcv.data = ''

            if ret == INJ_MODIFIED:
                # If you want to force the send of dirty packets
                # just modify it and return INJ_FORWARD that sends the packet
                # on L3 without any modifications.
                print 'Recompute checksum here.'

                ret = INJ_FORWARD

            if ret == INJ_FORWARD:
                print 'Forwarding packet'

            print inet_ntoa(stream.source), stream.sport, \
                  inet_ntoa(stream.dest), stream.dport

    def add_from_skb(self, stream, mpkt, rcv, snd, payload, datalen, tcpseq, \
                     fin, urg, urg_ptr):

        """
        @param stream a TCPStream instance
        @param mpkt a MetaPacket object
        @param snd a HalfStream instance
        @param payload the payload of the tcp packet as str
        @param datalen the datalen
        @param tcpseq the tcp sequence
        @param fin tcpflags & TH_FIN
        @param urg tcpflags & TH_URG
        @param urg_ptr the urg pointer of the TCP segment
        """

        exp_seq = (snd.first_data_seq + rcv.count + rcv.urg_count)
        lost = exp_seq - tcpseq

        if urg and urg_ptr - (exp_seq - 1) > 0 and \
           (not rcv.urg_seen or urg_ptr - rcv.urg_ptr > 0):

            rcv.urg_ptr = urg_ptr
            rcv.urg_seen = 1

        if rcv.urg_seen and rcv.urg_ptr + 1 - (tcpseq + lost)  > 0 and \
           rcv.urg_ptr - (tcpseq + datalen) < 0:

            to_copy = rcv.urg_ptr - (tcpseq + lost)

            if to_copy > 0:
                self.add2buf(mpkt, rcv, payload[lost:lost + to_copy])
                self.notify(mpkt, stream, rcv)

            rcv.urgdata = payload[rcv.urg_ptr + tcpseq:]
            rcv.count_new_urg = 1

            self.notify(mpkt, stream, rcv)

            rcv.count_new_urg = 0
            rcv.urg_seen = 0
            rcv.urg_count += 1

            to_copy2 = tcpseq + datalen - rcv.urg_ptr - 1

            if to_copy2 > 0:
                offset = lost + to_copy2 + 1
                self.add2buf(mpkt, rcv, payload[offset:offset + to_copy2])
                self.notify(mpkt, stream, rcv)
        else:
            if datalen - lost > 0:
                self.add2buf(mpkt, rcv, payload[lost:datalen])
                self.notify(mpkt, stream, rcv)

        if fin:
            snd.state = FIN_SENT

            if rcv.state == TCP_CLOSE:
                self.add_tcp_closing_timeout(stream)

    def tcp_queue(self, stream, mpkt, snd, rcv, payload, datalen):
        """
        Append a packet to a tcp queue
        @param stream a TCPStream instance
        @param mpkt a MetaPacket object
        @param snd a HalfStream instance
        @param rcv a HalfStream instance
        @param payload the payload of the tcp packet as str
        @param datalen the datalen
        """
        tcpseq = mpkt.get_field('tcp.seq')
        tcpflags = mpkt.get_field('tcp.flags')

        exp_seq = (snd.first_data_seq + rcv.count + rcv.urg_count)

        if not tcpseq - exp_seq > 0:
            if (tcpseq + datalen + (tcpflags & TH_FIN)) - exp_seq > 0:

                cur_ts = get_ts(mpkt)[1]
                self.add_from_skb(stream, mpkt, rcv, snd, payload, datalen,
                                  tcpseq, tcpflags & TH_FIN, tcpflags & TH_URG,
                                  mpkt.get_field('tcp.urgptr') + tcpseq - 1)

                packet = rcv.plist

                while packet:
                    if packet.seq - exp_seq > 0:
                        break
                    if (packet.seq + packet.len + packet.fin) - exp_seq > 0:
                        self.add_from_skb(stream, mpkt, rcv, snd, packet.data,
                                          packet.len, packet.seq, packet.fin,
                                          packet.urg,
                                          packet.urg_ptr + packet.seq - 1)

                    rcv.rmem_alloc -= packet.truesize

                    if packet.prev:
                        packet.prev.next = packet.next
                    else:
                        packet.plist = packet.next

                    if packet.next:
                        packet.next.prev = packet.prev
                    else:
                        rcv.plist_tail = packet.prev

                    tmp = packet.next
                    del packet.data
                    del packet
                    packet = tmp
            else:
                return
        else:
            p = rcv.plist_tail

            packet = Buffer()
            packet.data = payload[:]
            rcv.rmem_alloc += len(packet.data)
            packet.fin = tcpflags & TH_FIN

            if packet.fin:
                snd.state = TCP_CLOSING

                if rcv.state == FIN_SENT or rcv.state == FIN_CONFIRMED:
                    self.add_closing_timeout(stream, mpkt)

            packet.seq = tcpseq
            packet.urg = tcpflags & TH_URG
            packet.urg_ptr = mpkt.get_field('tcp.urgptr')

            while True:
                if not p or not p.seq - tcpseq > 0:
                    break
                p = p.prev

            if not p:
                packet.prev = None
                packet.next = rcv.plist

                if rcv.plist:
                    rcv.plist.prev = packet

                rcv.plist = packet

                if not rcv.plist_tail:
                    rcv.plist_tail = packet
            else:
                packet.next  = p.next
                p.next = packet
                packet.prev = p

                if packet.next:
                    packet.next.prev = packet
                else:
                    rcv.plist_tail = packet

    def add_new_tcp(self, mpkt):
        """
        @param mpkt a MetaPacket object
        """
        ctup = (inet_aton(mpkt.get_field('ip.src')),
                inet_aton(mpkt.get_field('ip.dst')),
                mpkt.get_field('tcp.sport'), mpkt.get_field('tcp.dport'))

        hash_idx = ':'.join(ctup[0:2])

        if self.n_streams >= self.max_streams:
            orig_client_state = self.oldest_stream.client.state
            self.oldest_stream.state = self.oldest_stream.CONN_TIMED_OUT

            for listener in self.oldest_stream.listeners:
                listener(self.oldest_stream, mpkt, None)

            self.free_tcp_stream(self.oldest_stream)

            if orig_client_state != TCP_SYN_SENT:
                log.debug('Removing last stream. Limit hit.')


        new_stream = self.free_streams

        if not new_stream:
            raise Exception('No mem')

        self.free_streams = new_stream.next_free

        new_stream.reset(*ctup)

        self.n_streams += 1
        tolink = self.tcp_streams.get(hash_idx, None)

        new_stream.client.state = TCP_SYN_SENT
        new_stream.client.seq = \
        new_stream.client.first_data_seq = mpkt.get_field('tcp.seq') + 1
        new_stream.client.window = mpkt.get_field('tcp.window')

        new_stream.client.ts_on, new_stream.client.curr_ts = get_ts(mpkt)
        new_stream.client.wscale_on, new_stream.client.wscale = get_wscale(mpkt)

        new_stream.server.state = TCP_CLOSE
        new_stream.next_node = tolink

        if tolink:
            tolink.prev_node = new_stream

        self.tcp_streams[hash_idx] = new_stream

        new_stream.next_time = self.latest_stream

        if not self.oldest_stream:
            self.oldest_stream = new_stream
        if self.latest_stream:
            self.latest_stream.prev_time = new_stream

        self.latest_stream = new_stream

    def find_stream(self, mpkt):
        """
        @param mpkt a MetaPacket object
        @return a tuple (is_client:bool, TCPStream) or (True, None)
        """
        # First look for client side streams

        ctup = (inet_aton(mpkt.get_field('ip.src')),
                inet_aton(mpkt.get_field('ip.dst')),
                mpkt.get_field('tcp.sport'), mpkt.get_field('tcp.dport'))

        tcp_stream = self.find_tcp_stream(ctup)

        if tcp_stream:
            return (True, tcp_stream)

        stup = (ctup[1], ctup[0], ctup[3], ctup[2])

        tcp_stream = self.find_tcp_stream(stup)

        if tcp_stream:
            return (False, tcp_stream)

        return (False, None)

    def find_tcp_stream(self, tup):
        """
        @param tup a tuple (srcip, dstip, srport, dport)
        @return a TCPStream or None
        """
        it = self.tcp_streams.get(':'.join(tup[0:2]), None)

        while it:
            if it.sport == tup[2] and it.dport == tup[3]:
                return it
            it = it.next_node

    def add_tcp_closing_timeout(self, stream, mpkt):
        """
        @param stream a TCPStream instance
        @param mpkt a MetaPacket object
        """
        if not self.tcp_workarounds:
            return

        newto = TCPTimeout(stream, datetime.timedelta())
        newto.timeout.seconds = mpkt.get_datetime().seconds + 10

        to = self.tcp_timeouts
        newto.next = self.tcp_timeouts

        while to:
            if to.stream is stream:
                del newto

            if to.timeout.seconds > to.timeout.seconds:
                break

            newto.prev = to
            newto.next = to = to.next

        if not newto.prev:
            self.tcp_timeouts = newto
        else:
            newto.prev.next = newto

        if newto.next:
            newto.next.prev = newto

    def del_tcp_closing_timeout(self, stream):
        """
        @param stream a TCPStream instance
        """
        if not self.tcp_workarounds:
            return

        to = self.tcp_timeouts

        while to:
            if to.stream is stream:
                break

            to = to.next

        if not to:
            return

        if not to.prev:
            self.tcp_timeouts = to.next
        else:
            to.prev.next = to.next

        if to.next:
            to.next.prev = to.prev

        del to

    def free_tcp_stream(self, stream):
        """
        @param stream TCPStream instance
        """
        self.del_tcp_closing_timeout(stream)

        self.prune_queue(stream.server)
        self.prune_queue(stream.client)

        hash_idx = stream.source + ":" + stream.dest

        if stream.next_node:
            stream.next_node.prev_node = stream.prev_node
        if stream.prev_node:
            stream.prev_node.next_node = stream.next_node
        else:
            self.tcp_streams[hash_idx] = stream.next_node

        if self.tcp_streams[hash_idx] is None:
            del self.tcp_streams[hash_idx]

        if stream.client.data:
            del stream.client.data
        if stream.server.data:
            del stream.server.data

        if stream.next_time:
            stream.next_time.prev_time = stream.prev_time
        if stream.prev_time:
            stream.prev_time.next_time = stream.next_time

        if stream is self.oldest_stream:
            self.oldest_stream = stream.prev_time
        if stream is self.latest_stream:
            self.latest_stream = stream.next_time

        stream.listeners = []

        stream.next_free = self.free_streams
        self.free_streams = stream

        self.n_streams -= 1

class TCPDecoder(Plugin, OfflineAttack):
    def start(self, reader):
        self.checksum_check = True
        self.dissectors = True
        self.reassembler = None
        self.manager = None

    def register_decoders(self):
        self.manager = AttackManager()
        conf = self.manager.get_configuration('decoder.tcp')

        self.checksum_check = conf['checksum_check']
        self.dissectors = conf['enable_dissectors']

        self.manager.add_decoder(PROTO_LAYER, NL_TYPE_TCP, self._process_tcp)

        if conf['enable_reassemble']:
            self.reassembler = Reassembler(conf['reassemble_workarounds'],
                                           conf['reassemble_maxstreams'])
            self.manager.add_decoder_hook(PROTO_LAYER, NL_TYPE_ICMP,
                                          self.reassembler.process_icmp, 1)

    def _process_tcp(self, mpkt):
        if self.checksum_check:
            # TODO: Handle IPv6 here
            tcpraw = mpkt.get_field('tcp')

            if tcpraw:
                ln = mpkt.get_field('ip.len') - 20

                if ln == len(tcpraw):
                    ip_src = mpkt.get_field('ip.src')
                    ip_dst = mpkt.get_field('ip.dst')

                    psdhdr = pack("!4s4sHH",
                                  inet_aton(ip_src),
                                  inet_aton(ip_dst),
                                  mpkt.get_field('ip.proto'),
                                  ln)

                    chksum = checksum(psdhdr + tcpraw[:16] + \
                                      "\x00\x00" + tcpraw[18:])

                    if mpkt.get_field('tcp.chksum') != chksum:
                        mpkt.set_cfield('good_checksum', hex(chksum))
                        self.manager.user_msg(
                                         "Invalid TCP packet from %s to %s : " \
                                         "wrong checksum %s instead of %s" %   \
                                         (ip_src, ip_dst,                      \
                                          hex(mpkt.get_field('tcp.chksum')),   \
                                          hex(chksum)),
                                         5, 'decoder.tcp')
                    elif self.reassembler:
                        self.reassembler.process_tcp(mpkt)

        if not self.dissectors:
            return None

        ret = self.manager.run_decoder(APP_LAYER_TCP,
                                       mpkt.get_field('tcp.dport'), mpkt)

        ret = self.manager.run_decoder(APP_LAYER_TCP,
                                       mpkt.get_field('tcp.sport'), mpkt)

        # TODO: Here we've to handle injected buffer and split overflowed
        # data in various packets (check MTU).

        # Nothing to parse at this point
        return None

__plugins__ = [TCPDecoder]
__plugins_deps__ = [('TCPDecoder', ['IPDecoder'], ['=TCPDecoder-1.0'], [])]

# Offline attacks fields
__attack_type__ = 0
__protocols__   = (('tcp', None), )
__references__  = (
    (None, 'http://en.wikipedia.org/wiki/Transmission_Control_Protocol'),
)
__configurations__ = (
    ('decoder.tcp', {
        'checksum_check' : [True, 'Cheksum check for TCP segments'],
        'enable_dissectors' : [True, 'Enable TCP protocol dissectors'],
        'enable_reassemble' : [True, 'Enable userland python implementation of '
                               'TCP/IP stack to tracks TCP streams connection. '
                               'You\'ve to enable checksum_check'],
        'reassemble_workarounds' : [True, 'Close a TCP connection after a ' \
                                    'timeout. Not RFC compliant but used in ' \
                                    'many implementations'],
        'reassemble_maxstreams' : [30, 'Max number of streams to follow']
    }),
)
