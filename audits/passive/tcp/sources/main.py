#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2010 Adriano Monteiro Marques
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
TCP protocol decoder

>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip,tcp', 'wrong-checksum.pcap')
decoder.ip.notice Invalid IP packet from 127.0.0.1 to 127.0.0.1 : wrong checksum 0xdead instead of 0x7bce
decoder.tcp.notice Invalid TCP packet from 127.0.0.1 to 127.0.0.1 : wrong checksum 0x29a instead of 0xc86
"""

from datetime import datetime
from struct import pack, unpack
from socket import inet_aton, ntohl, inet_ntoa

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.tracing import trace
from umit.pm.gui.plugins.core import Core
from umit.pm.core.atoms import defaultdict
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.sessionmanager import *
from umit.pm.manager.auditmanager import AuditManager, PassiveAudit
from umit.pm.core.netconst import *
from umit.pm.core.auditutils import checksum

from umit.pm.backend import MetaPacket

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
        self.data = ''

        self.fin = 0
        self.urg = 0
        self.seq = 0

        self.prev, self.next = None, None

    def __repr__(self):
        return '<Buffer %.10s seq=%d fin=%d>' \
               % (repr(self.data), self.seq, self.fin)

    def dump(self):
        """
        Debug function that dumps the next elements starting from self
        """

        if not self.next:
            return repr(self)
        else:
            return repr(self) + ' ' + self.next.dump()

class HalfStream(object):
    def __init__(self, name=None):
        self.name = name

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
        self.count = 0
        self.data = ''
        self.urgdata = ''

        self.plist = None
        self.plist_tail = None

    def __repr__(self):
        return '<HalfStream(to=%s) seq=%d ack=%d data=%.10s>' \
               % (self.name, self.seq, self.ack_seq, self.data)

class TCPStream(object):
    def __init__(self, source, dest, sport, dport):
        self.reset(source, dest, sport, dport)

    def reset(self, source, dest, sport, dport):
        self.source = source
        self.dest = dest
        self.sport = sport
        self.dport = dport

        self.state = CONN_UNDEFINED

        self.client = HalfStream(source and inet_ntoa(source) or None)
        self.server = HalfStream(dest and inet_ntoa(dest) or None)

        self.next_node, self.prev_node = None, None
        self.next_time, self.prev_time = None, None
        self.next_free = None

        self.listeners = []

    def get_source(self):
        "@return the dotted decimal form of source IP"
        return inet_ntoa(self.source)
    def get_dest(self):
        "@return the dotted decimal form of destination IP"
        return inet_ntoa(self.dest)
    def get_bytes(self):
        "@return the bytes collected of the session"
        return self.client.count + self.server.count

    def mkhash(self):
        return hash(self.source) ^ hash(self.dest) ^ \
               hash(self.sport ^ self.dport)

    def __repr__(self):
        return '%s:%d <-> %s:%d' % (
            self.get_source(), self.sport,
            self.get_dest(), self.dport
        )

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
    def remove_analyzer(self, analyzer):
        self.analyzers.remove(analyzer)

    def process_icmp(self, mpkt):
        """
        Process an ICMP packet
        @param mpkt a MetaPacket object
        """
        iplen = mpkt.get_field('ip.len') - (mpkt.get_field('ip.ihl') << 2)

        if iplen < 20:
            return
        ipsrc, ipdst = inet_aton(mpkt.l3_src), \
                       inet_aton(mpkt.l3_dst)

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

        stream.state = CONN_RESET

        for listener in stream.listeners:
            listener(stream, mpkt, None)

        self.free_tcp_stream(stream)

    def process_tcp(self, mpkt):
        """
        Process a TCP packet
        @param mpkt a MetaPacket object
        """

        datalen = mpkt.get_field('ip.len') - \
                  mpkt.l3_len - mpkt.l4_len

        if datalen < 0:
            log.warning('Bogus TCP/IP header (datalen < 0)')
            return

        ipsrc, ipdst = inet_aton(mpkt.l3_src), \
                       inet_aton(mpkt.l3_dst)

        if ipsrc == '\x00\x00\x00\x00' and \
           ipdst == '\x00\x00\x00\x00':
            log.warning('Bogus IP header (src or dst are NULL)')
            return

        tcpflags = mpkt.l4_flags

        if not tcpflags:
            return

        is_client, stream = self.find_stream(mpkt)

        if not stream:
            if tcpflags & TH_SYN and \
               not tcpflags & TH_ACK and not tcpflags & TH_RST:

                self.add_new_tcp(mpkt)

            return

        if is_client:
            snd, rcv = stream.client, stream.server
        else:
            snd, rcv = stream.server, stream.client

        tcpseq = mpkt.l4_seq or 0
        tcpack = mpkt.l4_ack or 0

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
            stream.server.window = mpkt.get_field('tcp.window', 0)

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

        #if not (not datalen and tcpseq == (rcv.ack_seq)) and \
        #   (not (tcpseq - (rcv.ack_seq + rcv.window * rcv.wscale) < 0) or \
        #   (tcpseq + datalen) - rcv.ack_seq < 0):
        if tcpseq + datalen - rcv.ack_seq < 0:
            return

        if tcpflags & TH_RST:
            if stream.state == CONN_DATA:
                stream.state = CONN_RESET

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
                    stream.state = CONN_JUST_ESTABLISHED

                    for callback in self.analyzers:
                        callback(stream, mpkt)

                    if not stream.listeners:
                        self.free_tcp_stream(stream)
                        return

                    stream.state = CONN_DATA

        if tcpflags & TH_ACK:
            if tcpack - snd.ack_seq > 0:
                snd.ack_seq = tcpack
            if rcv.state == FIN_SENT:
                rcv.state = FIN_CONFIRMED
            if rcv.state == FIN_CONFIRMED and snd.state == FIN_CONFIRMED:
                stream.state = CONN_CLOSE

                for listener in stream.listeners:
                    listener(stream, mpkt, None)

                self.free_tcp_stream(stream)
                return

        if (datalen + (tcpflags & TH_FIN)) > 0:
            payload = mpkt.data

            if payload:
                self.tcp_queue(stream, mpkt, snd, rcv, payload, datalen)

        snd.window = mpkt.get_field('tcp.window', 0)

        if rcv.rmem_alloc > 65535:
            self.prune_queue(rcv)

    #@trace
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
        rcv.count += rcv.count_new

    def notify(self, mpkt, stream, rcv):
        ret = REAS_SKIP_PACKET

        for listener in stream.listeners:
            ret = max(ret,
                      listener(stream, mpkt, rcv))

        if ret == REAS_COLLECT_STATS:
            log.debug('Collecting stats')
            rcv.data = ''
        elif ret == REAS_SKIP_PACKET:
            log.debug('Skipping packet')
            rcv.count_new = 0
            rcv.data = ''
        else:
            log.debug('Collecting data')

    #@trace
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

        log.debug('exp_seq: %d tcpseq: %d lost: %d' % (exp_seq, tcpseq, lost))

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
                log.debug('add2buf() %d:%d' % (lost, datalen))
                self.add2buf(mpkt, rcv, payload[lost:datalen])
                self.notify(mpkt, stream, rcv)

        if fin:
            snd.state = FIN_SENT

            if rcv.state == TCP_CLOSE:
                self.add_tcp_closing_timeout(stream)

    #@trace
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
        tcpseq = mpkt.l4_seq
        tcpflags = mpkt.l4_flags

        exp_seq = (snd.first_data_seq + rcv.count + rcv.urg_count)

        if not tcpseq - exp_seq > 0:

            # This packet is old because seq < current
            if (tcpseq + datalen + (tcpflags & TH_FIN)) - exp_seq > 0:

                log.debug('Last packet of the window')

                cur_ts = get_ts(mpkt)[1]
                self.add_from_skb(stream, mpkt, rcv, snd, payload, datalen,
                                  tcpseq, tcpflags & TH_FIN, tcpflags & TH_URG,
                                  mpkt.get_field('tcp.urgptr', 0) + tcpseq - 1)

                packet = rcv.plist

                while packet:
                    if packet.seq - exp_seq > 0:
                        break
                    if (packet.seq + len(packet.data) + packet.fin) - \
                       exp_seq > 0:
                        self.add_from_skb(stream, mpkt, rcv, snd, packet.data,
                                          len(packet.data), packet.seq,
                                          packet.fin, packet.urg,
                                          packet.urg_ptr + packet.seq - 1)

                    rcv.rmem_alloc -= len(packet.data)

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
                log.warning('Inconsistent packet (%.10s) ignored.' % payload)
                return
        else:
            log.debug('Standard packet. Looking for the right position')

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
            packet.urg_ptr = mpkt.get_field('tcp.urgptr', 0)

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

                log.debug('Prepending packet %s' % packet)
            else:
                packet.next  = p.next
                p.next = packet
                packet.prev = p

                log.debug('Appending %s after %s' % (packet, p))

                if packet.next:
                    packet.next.prev = packet
                else:
                    rcv.plist_tail = packet

            #log.debug('List: %s' % rcv.plist.dump())

    def add_new_tcp(self, mpkt):
        """
        @param mpkt a MetaPacket object
        """
        ctup = (inet_aton(mpkt.l3_src),
                inet_aton(mpkt.l3_dst),
                mpkt.l4_src, mpkt.l4_dst)

        hash_idx = hash(ctup[0]) ^ hash(ctup[1]) ^ hash(ctup[2] ^ ctup[3])

        if self.n_streams >= self.max_streams:
            orig_client_state = self.oldest_stream.client.state
            self.oldest_stream.state = CONN_TIMED_OUT

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
        new_stream.client.first_data_seq = mpkt.l4_seq + 1
        new_stream.client.window = mpkt.get_field('tcp.window', 0)

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

        ctup = (inet_aton(mpkt.l3_src),
                inet_aton(mpkt.l3_dst),
                mpkt.l4_src, mpkt.l4_dst)

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
        hash_idx = hash(tup[0]) ^ hash(tup[1]) ^ \
                   hash(tup[2] ^ tup[3])

        it = self.tcp_streams.get(hash_idx, None)

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
        hash_idx = stream.mkhash()

        self.del_tcp_closing_timeout(stream)

        self.prune_queue(stream.server)
        self.prune_queue(stream.client)

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

class TCPDecoder(Plugin, PassiveAudit):
    def start(self, reader):
        self.checksum_check = True
        self.reassembler = None
        self.manager = None

    def stop(self):
        manager = AuditManager()
        manager.remove_decoder(PROTO_LAYER, NL_TYPE_TCP, self._process_tcp)
        manager.remove_injector(1, NL_TYPE_TCP, self._inject_tcp)

        try:
            manager.remove_decoder_hook(PROTO_LAYER, NL_TYPE_ICMP,
                                             self.reassembler.process_icmp, 1)
        except:
            pass

    def register_decoders(self):
        self.manager = AuditManager()
        conf = self.manager.get_configuration('decoder.tcp')

        self.checksum_check = conf['checksum_check']

        self.manager.add_decoder(PROTO_LAYER, NL_TYPE_TCP, self._process_tcp)
        self.manager.add_injector(1, NL_TYPE_TCP, self._inject_tcp)

        if conf['enable_reassemble']:
            self.reassembler = Reassembler(conf['reassemble_workarounds'],
                                           conf['reassemble_maxstreams'])
            self.manager.add_decoder_hook(PROTO_LAYER, NL_TYPE_ICMP,
                                          self.reassembler.process_icmp, 1)

    def _inject_tcp(self, context, mpkt, length):
        """
        Function that manages injection of fragments in active TCP connection
        """

        ident = TCPIdent.create(mpkt)
        sess = SessionManager().get_session(ident)

        if not sess:
            log.debug("No TCP session found.")
            return False, length

        if ident.l3_src == sess.ident.l3_src:
            status = sess.data[1]
            ostatus = sess.data[0]
        else:
            status = sess.data[0]
            ostatus = sess.data[1]

        mpkt.set_fields('tcp', {
            'sport' : mpkt.l4_src,
            'dport' : mpkt.l4_dst,
            'dataofs' : 5,
            'chksum' : None,
            'urgptr' : 0,
            'flags' : TH_PSH,
            'options' : {}})

        if status.injectable & INJ_FIN or \
           not status.injectable & INJ_FWD or \
           not ostatus.injectable & INJ_FWD:
            log.debug("Session is not injectable.")
            return False, length

        mpkt.set_fields('tcp', {
            'seq' : status.last_seq + status.seq_adj,
            'ack' : status.last_ack - ostatus.seq_adj})

        if status.last_ack != 0:
            mpkt.set_field('tcp.flags', mpkt.l4_flags | TH_ACK)

        mpkt.session = sess.prev
        length += 20 + mpkt.l2_len

        injector = AuditManager().get_injector(0, mpkt.session.ident.magic)
        is_ok, length = injector(context, mpkt, length)

        if not is_ok:
            return is_ok, length

        length = context.get_mtu() - length

        if length > mpkt.inject_len:
            length = mpkt.inject_len

        payload = mpkt.inject[:length]
        payload_pkt = MetaPacket.new('raw')
        payload_pkt.set_field('raw.load', payload)
        mpkt.add_to('tcp', payload_pkt)

        status.seq_adj += length
        mpkt.data_len = length

        return True, length

    def _process_tcp(self, mpkt):
        mpkt.l4_src, \
        mpkt.l4_dst, \
        mpkt.l4_ack, \
        mpkt.l4_seq, \
        mpkt.l4_flags = mpkt.get_fields('tcp', ('sport', 'dport', 'ack', \
                                                'seq', 'flags'))
        mpkt.l4_len = mpkt.get_field('tcp.dataofs', 5) * 4

        if mpkt.l4_src is None:
            return None

        tcpraw = mpkt.get_field('tcp')

        if tcpraw:
            mpkt.data_len = mpkt.payload_len - mpkt.l4_len
            mpkt.data = tcpraw[mpkt.l4_len:]

        wrong = False

        if self.checksum_check and tcpraw:
            if mpkt.payload_len == len(tcpraw):
                ip_src = mpkt.l3_src
                ip_dst = mpkt.l3_dst

                psdhdr = pack("!4s4sHH",
                              inet_aton(ip_src),
                              inet_aton(ip_dst),
                              mpkt.l4_proto,
                              mpkt.payload_len)

                chksum = checksum(psdhdr + tcpraw[:16] + \
                                  "\x00\x00" + tcpraw[18:])

                if mpkt.get_field('tcp.chksum', 0) != chksum:
                    wrong = True
                    mpkt.set_cfield('good_checksum', hex(chksum))
                    self.manager.user_msg(
                                _("Invalid TCP packet from %s to %s : " \
                                  "wrong checksum %s instead of %s") %  \
                                (ip_src, ip_dst,                        \
                                 hex(mpkt.get_field('tcp.chksum', 0)),  \
                                 hex(chksum)),
                                5, 'decoder.tcp')

        if wrong:
            self.manager.run_decoder(APP_LAYER, PL_DEFAULT, mpkt)
            return None

        if self.reassembler:
            self.reassembler.process_tcp(mpkt)

        ident = TCPIdent.create(mpkt)
        sess = SessionManager().get_session(ident)

        if not sess:
            sess = Session(ident)
            sess.data = (TCPStatus(), TCPStatus())
            SessionManager().put_session(sess)

        sess.prev = mpkt.session
        mpkt.session = sess

        if ident.l3_src == sess.ident.l3_src:
            status = sess.data[1]
            ostatus = sess.data[0]
        else:
            status = sess.data[0]
            ostatus = sess.data[1]

        status.last_seq = mpkt.l4_seq + mpkt.data_len

        if mpkt.l4_flags & TH_ACK:
            status.last_ack = mpkt.l4_ack

        if mpkt.l4_flags & TH_SYN:
            status.last_seq += 1

        if mpkt.l4_flags & TH_RST:
            status.injectable |= INJ_FIN
            ostatus.injectable |= INJ_FIN

        if mpkt.flags & MPKT_FORWARDABLE:
            status.injectable |= INJ_FWD
        elif status.injectable & INJ_FWD:
            status.injectable ^= INJ_FWD

        self.manager.run_decoder(APP_LAYER, PL_DEFAULT, mpkt)

        if mpkt.l4_flags & TH_FIN:
            status.injectable |= INJ_FIN

        if mpkt.flags & MPKT_DROPPED and mpkt.flags & MPKT_FORWARDABLE:
            status.seq_adj += mpkt.inj_delta
        elif (mpkt.flags & MPKT_MODIFIED or \
             status.seq_adj != 0 or ostatus != 0) and \
             mpkt.flags & MPKT_FORWARDABLE:

            mpkt.set_field('tcp.seq', mpkt.l4_seq + status.seq_adj)
            mpkt.set_field('tcp.ack', mpkt.l4_ack - ostatus.seq_adj)

            status.seq_adj += mpkt.inj_delta

            mpkt.set_field('tcp.chksum', None)

        return None

__plugins__ = [TCPDecoder]
__plugins_deps__ = [('TCPDecoder', ['IPDecoder'], ['=TCPDecoder-1.0'], [])]

# Passive audits fields
__audit_type__ = 0
__protocols__   = (('tcp', None), )
__configurations__ = (
    ('decoder.tcp', {
        'checksum_check' : [True, 'Cheksum check for TCP segments'],
        'enable_reassemble' : [True, 'Enable userland python implementation of '
                               'TCP/IP stack to tracks TCP streams connection. '
                               'You\'ve to enable checksum_check'],
        'reassemble_workarounds' : [True, 'Close a TCP connection after a ' \
                                    'timeout. Not RFC compliant but used in ' \
                                    'many implementations'],
        'reassemble_maxstreams' : [30, 'Max number of streams to follow']
    }),
)
__vulnerabilities__ = (('TCP decoder', {
    'description' : 'The Transmission Control Protocol (TCP) is one of the '
                    'core protocols of the Internet Protocol Suite. TCP is '
                    'one of the two original components of the suite (the '
                    'other being Internet Protocol, or IP), so the entire '
                    'suite is commonly referred to as TCP/IP. Whereas IP '
                    'handles lower-level transmissions from computer to '
                    'computer as a message makes its way across the '
                    'Internet, TCP operates at a higher level, '
                    'concerned only with the two end systems, for example '
                    'a Web browser and a Web server. In particular, TCP '
                    'provides reliable, ordered delivery of a stream of '
                    'bytes from a program on one computer to another '
                    'program on another computer. Besides the Web, other '
                    'common applications of TCP include e-mail and file '
                    'transfer. Among its other management tasks, TCP '
                    'controls segment size, the rate at which data are '
                    'exchanged, and network traffic congestion.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                           'Transmission_Control_Protocol'),)
    }),
)
