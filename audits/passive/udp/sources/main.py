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
UDP protocol decoder.

>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip,udp', 'wrong-checksum-udp.pcap')
decoder.udp.notice Invalid UDP packet from 127.0.0.1 to 127.0.0.1 : wrong checksum 0x29a instead of 0x172
"""

from time import time
from struct import pack
from socket import inet_aton

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import AuditManager, PassiveAudit
from umit.pm.manager.sessionmanager import STATELESS_IP_MAGIC
from umit.pm.core.netconst import *
from umit.pm.core.auditutils import checksum

from umit.pm.backend import MetaPacket

UDP_LENGTH = 8
UDP_NAME = 'decoder.udp'

def udp_decoder():
    manager = AuditManager()

    conf = manager.get_configuration(UDP_NAME)
    checksum_check = conf['checksum_check']

    def udp(mpkt):
        mpkt.l4_len = UDP_LENGTH
        mpkt.l4_src, \
        mpkt.l4_dst = mpkt.get_fields('udp', ('sport', 'dport'))

        load = mpkt.get_field('udp')[mpkt.l4_len:]

        if load:
            mpkt.data = load

        if checksum_check:
            udpraw = mpkt.get_field('udp')

            if udpraw:
                if mpkt.payload_len == len(udpraw):
                    psdhdr = pack("!4s4sHH",
                                  inet_aton(mpkt.l3_src),
                                  inet_aton(mpkt.l3_dst),
                                  mpkt.l4_proto,
                                  mpkt.payload_len)

                    chksum = checksum(psdhdr + udpraw[:6] + \
                                      '\x00\x00' + udpraw[8:])

                    if mpkt.get_field('udp.chksum') != chksum:
                        mpkt.set_cfield('good_checksum', hex(chksum))
                        manager.user_msg(
                            _("Invalid UDP packet from %s to %s : " \
                              "wrong checksum %s instead of %s") %  \
                            (mpkt.l3_src, mpkt.l3_dst,              \
                             hex(mpkt.get_field('udp.chksum', 0)),  \
                             hex(chksum)),                          \
                            5, UDP_NAME)

        manager.run_decoder(APP_LAYER, PL_DEFAULT, mpkt)

        if mpkt.flags & MPKT_MODIFIED and \
           mpkt.flags & MPKT_FORWARDABLE:

            mpkt.set_field('udp.chksum', None)

        return None

    return udp

def udp_injector(context, mpkt, length):
    mpkt.set_fields('udp', {
        'sport' : mpkt.l4_src,
        'dport' : mpkt.l4_dst,
        'chksum' : None})

    length += UDP_LENGTH
    mpkt.session = None

    injector = AuditManager().get_injector(0, STATELESS_IP_MAGIC)
    is_ok, length = injector(context, mpkt, length)

    length = context.get_mtu() - length

    if length > mpkt.inject_len:
        length = mpkt.inject_len

    payload = mpkt.inject[:length]
    payload_pkt = MetaPacket.new('raw')
    payload_pkt.set_field('raw.load', payload)
    mpkt.add_to('udp', payload_pkt)

    return True, length

class UDPDecoder(PassiveAudit):
    def register_decoders(self):
        manager = AuditManager()
        manager.add_decoder(PROTO_LAYER, NL_TYPE_UDP, self.decoder)
        manager.add_injector(1, NL_TYPE_UDP, self.injector)

    def start(self, reader):
        self.decoder = udp_decoder()
        self.injector = udp_injector

    def stop(self):
        manager = AuditManager()
        manager.remove_decoder(PROTO_LAYER, NL_TYPE_UDP, self.decoder)
        manager.remove_injector(1, NL_TYPE_UDP, self.injector)

__plugins__ = [UDPDecoder]
__plugins_deps__ = [('UDPDecoder', ['IPDecoder'], ['=UDPDecoder-1.0'], [])]

__audit_type__ = 0
__protocols__ = (('udp', None), )
__configurations__ = (('decoder.udp', {
    'checksum_check' : [True, 'Enable checksum check for IP packets'],
    }),
)
__vulnerabilities__ = (('UDP decoder', {
    'description' : 'The User Datagram Protocol (UDP) is one of the core '
                    'members of the Internet Protocol Suite, the set of '
                    'network protocols used for the Internet. With UDP, '
                    'computer applications can send messages, in this case '
                    'referred to as datagrams, to other hosts on an Internet '
                    'Protocol (IP) network without requiring prior '
                    'communications to set up special transmission channels '
                    'or data paths. UDP is sometimes called the Universal '
                    'Datagram Protocol. The protocol was designed by David P. '
                    'Reed in 1980 and formally defined in RFC 768.\n\n'
                    'UDP uses a simple transmission model without implicit '
                    'hand-shaking dialogues for guaranteeing reliability, '
                    'ordering, or data integrity. Thus, UDP provides an '
                    'unreliable service and datagrams may arrive out of '
                    'order, appear duplicated, or go missing without notice. '
                    'UDP assumes that error checking and correction is either '
                    'not necessary or performed in the application, avoiding '
                    'the overhead of such processing at the network interface '
                    'level. Time-sensitive applications often use UDP because '
                    'dropping packets is preferable to using delayed packets. '
                    'If error correction facilities are needed at the network '
                    'interface level, an application may use the Transmission '
                    'Control Protocol (TCP) or Stream Control Transmission '
                    'Protocol (SCTP) which are designed for this purpose.\n\n'
                    'UDP\'s stateless nature is also useful for servers that '
                    'answer small queries from huge numbers of clients. '
                    'Unlike TCP, UDP is compatible with packet broadcast '
                    '(sending to all on local network) and multicasting '
                    '(send to all subscribers).\n\n'
                    'Common network applications that use UDP include: the '
                    'Domain Name System (DNS), streaming media applications '
                    'such as IPTV, Voice over IP (VoIP), Trivial File '
                    'Transfer Protocol (TFTP) and many online games.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                           'User_Datagram_Protocol'), )
    }),
)
