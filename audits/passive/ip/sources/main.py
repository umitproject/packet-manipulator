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
IP protocol decoder.

These are only doctest strings:

>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip', 'wrong-checksum.pcap')
decoder.ip.notice Invalid IP packet from 127.0.0.1 to 127.0.0.1 : wrong checksum 0xdead instead of 0x7bce

Fragmentation tests.

>>> audit_unittest('-f ethernet,ip -sdecoder.ip.reassemble_max_fragments=1', 'fragmented-ping.pcap')
decoder.ip.debug Dropping out the sequence with ID: 14300 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14300 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14301 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14301 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14302 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14302 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14303 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14303 due reassemble_max_fragments
>>> audit_unittest('-f ethernet,ip -sdecoder.ip.reassemble_max_fragments=2', 'fragmented-ping.pcap')
decoder.ip.debug Dropping out the sequence with ID: 14300 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14301 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14302 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14303 due reassemble_max_fragments
"""

import time

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import AuditManager, PassiveAudit
from umit.pm.manager.sessionmanager import *
from umit.pm.core.netconst import PROTO_LAYER, NET_LAYER, LL_TYPE_IP
from umit.pm.core.auditutils import checksum

from umit.pm.backend import MetaPacket

def ip_decoder():
    manager = AuditManager()

    conf = manager.get_configuration('decoder.ip')
    checksum_check, reassemble, max_len, max_frags = \
        conf['checksum_check'], conf['reassemble'], \
        conf['reassemble_max_fraglist'], conf['reassemble_max_fragments']

    reas_dict = {}

    def ip_reassemble(mpkt):
        # Here we have to check for fragmentation
        # by creating a dict to holds id of ip packets
        # and set mpkt.lock() on it if mpkg is MF
        # until the resegmentation is done.
        # If it's a fragment we have to return None
        # to break the chain.

        # TODO: check ip.flags standard name in UMPA
        ts = time.time()
        mf = mpkt.get_field('ip.flags', 0) & 1
        frag_off = mpkt.get_field('ip.frag', 0) * 8

        if not mf and frag_off == 0:
            return False

        ipid = mpkt.get_field('ip.id')

        if ipid in reas_dict:
            plist = reas_dict[ipid]

            if len(plist) >= max_frags:
                del reas_dict[ipid]
                manager.user_msg(_('Dropping out the sequence with ID: '
                                   '%s due reassemble_max_fragments') %
                                 ipid, 7, 'decoder.ip')

                return False

            ret = 0
            idx = 0
            inserted = False

            while idx < len(plist):
                ts2, frag_off2, mpkt2 = plist[idx]

                if frag_off2 == frag_off:
                    plist[idx] = (ts, frag_off, mpkt.copy())
                    break
                elif frag_off2 < frag_off:
                    ret += frag_off2
                    idx += 1
                    continue

                inserted = True
                plist.insert(idx, (ts, frag_off, mpkt.copy()))
                break

            if not inserted:
                plist.append((ts, frag_off, mpkt.copy()))

            # Now let's get the last packet and see if MF = 0
            # EVASION!
            if plist[-1][-1].get_field('ip.flags') & 1 == 0:

                if idx == len(plist) -1:
                    ret = frag_off - ret
                else:
                    while idx < len(plist) - 1:
                        ts2, frag_off2, mpkt2 = plist[idx]
                        ret += frag_off2
                        idx += 1

                        ret = plist[-1][1] - ret

                if ret == 0:
                    log.debug('Reassembling sequence with ID: %s' % \
                              ipid)

                    reas_payload = ''

                    for ts2, frag_off2, mpkt2 in plist:
                        try:
                            ihl = mpkt2.l3_len
                            reas_payload += mpkt2.get_field('ip')[ihl:]
                        except:
                            pass

                    # Ok check that we have a complete payload
                    ihl = mpkt.l3_len
                    p_len = frag_off + mpkt.get_field('ip.len') - ihl

                    if len(reas_payload) != p_len:
                        mpkt.set_cfield('reassembled_payload', None)
                        manager.user_msg(_('Reassemble of IP packet ' \
                                           'from %s to %s failed') %  \
                                         (mpkt.l3_src, mpkt.l3_dst),  \
                                         4, 'decoder.ip')

                    # Nice drop out everythin!
                    del reas_dict[ipid]

                    mpkt.set_cfield('reassembled_payload', reas_payload)
                    return True
        else:
            if len(reas_dict) >= max_len:
                # Ok just drop the list with the minor ts (the oldest)
                min_k = min([(v, k) for k, v in reas_dict.items()])[1]
                del reas_dict[min_k]

                # Debug
                manager.user_msg(_('Dropping out the oldest sequence '
                                   'with ID: %s') % min_k,
                                 7, 'decoder.ip')

            log.debug('First packet of the sequence with ID: %s' % ipid)
            reas_dict[ipid] = [(ts, frag_off, mpkt)]

        return False

    def ip(mpkt):
        mpkt.l3_src, \
        mpkt.l3_dst, \
        mpkt.l4_proto = mpkt.get_fields('ip', ('src', 'dst', 'proto'))

        # TODO: handle IPv6

        ipraw = mpkt.get_field('ip')

        if not ipraw:
            return

        mpkt.l3_len = mpkt.get_field('ip.ihl') * 4
        mpkt.payload_len = mpkt.get_field('ip.len') - mpkt.l3_len

        if mpkt.context:
            mpkt.context.check_forwarded(mpkt)

            if mpkt.flags & MPKT_FORWARDED:
                return None

            mpkt.context.set_forwardable(mpkt)

        iplen = min(20, len(ipraw))

        if mpkt.get_field('ip.len') > len(ipraw):
            # Probably we are capturing with low snaplen
            # so the packets are not fully captured. Avoid
            # further calculation.
            return PROTO_LAYER, mpkt.l4_proto

        if checksum_check:
            ihl = max(20, mpkt.l3_len)
            pkt = ipraw[:10] + '\x00\x00' + ipraw[12:ihl]

            chksum = checksum(pkt)

            # Probably here it's better to set also a cfield
            # and to turn False the checksum_check default value
            if mpkt.get_field('ip.chksum') != chksum:
                mpkt.set_cfield('good_checksum', hex(chksum))
                manager.user_msg(_("Invalid IP packet from %s to %s : " \
                                   "wrong checksum %s instead of %s") %  \
                                 (mpkt.l3_src, mpkt.l3_dst,          \
                                  hex(mpkt.get_field('ip.chksum')),  \
                                  hex(chksum)),
                                 5, 'decoder.ip')

            elif reassemble:
                ip_reassemble(mpkt)

        ident = IPIdent.create(mpkt)
        sess = SessionManager().get_session(ident)

        if not sess:
            sess = Session(ident)
            sess.data = IPStatus()
            SessionManager().put_session(sess)

        sess.prev = mpkt.session
        mpkt.session = sess

        status = sess.data
        status.last_id = mpkt.get_field('ip.id', 0)

        manager.run_decoder(PROTO_LAYER, mpkt.l4_proto, mpkt)

        if mpkt.flags & MPKT_DROPPED:
            status.id_adj -= 1
        elif mpkt.flags & MPKT_MODIFIED or status.id_adj != 0:
            mpkt.set_field('ip.id', mpkt.get_field('ip.id', 0) + status.id_adj)
            mpkt.set_field('ip.len', mpkt.get_field('ip.len', 0) + mpkt.inj_delta)
            mpkt.set_field('ip.chksum', None)

    return ip

def stateless_ip_injector(context, mpkt, length):
    ident = IPIdent.create(mpkt)
    sess = SessionManager().get_session(ident)

    if not sess:
        return False, length

    mpkt.session = sess

    injector = AuditManager().get_injector(0, LL_TYPE_IP)
    return injector(context, mpkt, length)

def ip_injector(context, mpkt, length):
    if length + 20 > context.get_mtu():
        return False, length

    sess = mpkt.session
    status = sess.data

    mpkt.set_fields('ip', {
        'ihl' : 5,
        'version' : 4,
        'tos' : 0,
        'chksum' : None,
        #'len' : None,
        'flags' : 0,
        'frag' : 0,
        'ttl' : 125,
        'proto' : mpkt.l4_proto,
        'src' : mpkt.l3_src,
        'dst' : mpkt.l3_dst,
        'id' : status.last_id + status.id_adj + 1})

    if not SessionManager().get_session(sess.ident):
        return False, length

    length += 20
    further_len = length

    # TODO: support encapsulated packets

    status.id_adj += 1

    payload_len = context.get_mtu() - length

    if payload_len > mpkt.inject_len:
        payload_len = mpkt.inject_len

    tlen = further_len + payload_len - mpkt.l2_len
    mpkt.set_field('ip.len', tlen)

    mpkt.set_data_len(payload_len)

    return True, length

class IPDecoder(Plugin, PassiveAudit):
    def start(self, reader):
        self.ip_decoder = ip_decoder()

    def register_decoders(self):
        manager = AuditManager()
        manager.add_decoder(NET_LAYER, LL_TYPE_IP, self.ip_decoder)
        manager.add_injector(0, LL_TYPE_IP, ip_injector)
        manager.add_injector(0, STATELESS_IP_MAGIC, stateless_ip_injector)

    def stop(self):
        manager = AuditManager()
        manager.remove_decoder(NET_LAYER, LL_TYPE_IP, self.ip_decoder)
        manager.remove_injector(0, LL_TYPE_IP, ip_injector)
        manager.remove_injector(0, STATELESS_IP_MAGIC, stateless_ip_injector)

        self.decoder = None

__plugins__ = [IPDecoder]
__plugins_deps__ = [('IPDecoder', ['EthDecoder'], ['=IPDecoder-1.0'], [])]

__audit_type__ = 0
__protocols__ = (('ip', None), )
__configurations__ = (('decoder.ip', {
    'checksum_check' : [True, 'Enable checksum check for IP packets'],
    'reassemble' : [True, 'Enable IP fragments reassembling'],
    'reassemble_max_fraglist' : [30, 'Max number of IP flows to follow'],
    'reassemble_max_fragments' : [10, 'Max number of fragments in a flow']}),
)
__vulnerabilities__ = (('IP decoder', {
    'description' : 'The Internet Protocol (IP) is a protocol used for '
                    'communicating data across a packet-switched '
                    'internetwork using the Internet Protocol Suite, also '
                    'referred to as TCP/IP.\n\n'
                    'IP is the primary protocol in the Internet Layer of the '
                    'Internet Protocol Suite and has the task of delivering '
                    'distinguished protocol datagrams (packets) from the '
                    'source host to the destination host solely based on '
                    'their addresses. For this purpose the Internet Protocol '
                    'defines addressing methods and structures for datagram '
                    'encapsulation. The first major version of addressing '
                    'structure, now referred to as Internet Protocol Version '
                    '4 (IPv4) is still the dominant protocol of the Internet, '
                    'although the successor, Internet Protocol Version 6 '
                    '(IPv6) is being deployed actively worldwide.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/Internet_Protocol'),)
    }),
)
