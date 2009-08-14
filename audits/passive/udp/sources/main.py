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

>>> from PM.Core.AuditUtils import audit_unittest
>>> audit_unittest('-f ethernet,ip,udp', 'wrong-checksum-udp.pcap')
decoder.udp.notice Invalid UDP packet from 127.0.0.1 to 127.0.0.1 : wrong checksum 0x29a instead of 0x172
"""

from time import time
from struct import pack
from socket import inet_aton

from PM.Core.I18N import _
from PM.Core.Logger import log
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AuditManager import AuditManager, PassiveAudit
from PM.Core.NetConst import PROTO_LAYER, NET_LAYER, NL_TYPE_UDP, APP_LAYER_UDP
from PM.Core.AuditUtils import checksum

from PM.Backend import MetaPacket

def udp_decoder():
    manager = AuditManager()

    conf = manager.get_configuration('decoder.udp')
    checksum_check, dissectors = conf['checksum_check'], \
                                 conf['enable_dissectors']

    def udp(mpkt):
        if checksum_check:
            udpraw = mpkt.get_field('udp')

            if udpraw:
                ln = mpkt.get_field('ip.len') - 20

                if ln == len(udpraw):
                    ip_src = mpkt.get_field('ip.src')
                    ip_dst = mpkt.get_field('ip.dst')

                    psdhdr = pack("!4s4sHH",
                                  inet_aton(ip_src),
                                  inet_aton(ip_dst),
                                  mpkt.get_field('ip.proto'),
                                  ln)

                    chksum = checksum(psdhdr + udpraw[:6] + \
                                      "\x00\x00" + udpraw[8:])

                    if mpkt.get_field('udp.chksum') != chksum:
                        mpkt.set_cfield('good_checksum', hex(chksum))
                        manager.user_msg(
                            _("Invalid UDP packet from %s to %s : " \
                              "wrong checksum %s instead of %s") %  \
                            (ip_src, ip_dst,                        \
                             hex(mpkt.get_field('udp.chksum')),     \
                             hex(chksum)),                          \
                            5, 'decoder.udp')

            if not dissectors:
                return None

            # TODO: Check for injectors (set l4proto and flags)
            manager.run_decoder(APP_LAYER_UDP,
                                mpkt.get_field('udp.dport'), mpkt)
            manager.run_decoder(APP_LAYER_UDP,
                                mpkt.get_field('udp.sport'), mpkt)

            return None

    return udp

def udp_injector(context, mpkt):
    payload = mpkt.cfields.get('inj::payload', None)

    if not payload:
        return INJ_FORWARD
    else:
        AuditManager().get_injector(0, LL_TYPE_IP)

        if injector(context, mpkt) == INJ_ERROR:
            log.error('Error in underlayer injector')
            return INJ_ERROR

        pkt = mpkt.cfields.get('inj::data', None)

        if not pkt:
            log.error('The underlayer injector returns None as mpkt')
            return INJ_ERROR

        plen = len(payload)
        mtu = context.get_mtu() - pkt.get_size()

        if plen > mtu:
            plen = mtu

        pkt = pkt / MetaPacket.new('udp') / MetaPacket.new('raw')
        pkt.set_field('udp.sport', mpkt.get_field('udp.sport'))
        pkt.set_field('udp.dport', mpkt.get_field('udp.dport'))

        pkt.set_field('raw.load', payload[:plen])

        remaining = payload[plen:]

        if remaining:
            pkt.set_cfield('inj::payload', remaining)

        mpkt.set_cfield('inj::data', pkt)

        return INJ_FORWARD

class UDPDecoder(PassiveAudit):
    def register_decoders(self):
        manager = AuditManager()
        manager.add_decoder(PROTO_LAYER, NL_TYPE_UDP, self.decoder)
        manager.add_injector(0, NL_TYPE_UDP, self.injector)

    def start(self, reader):
        self.decoder = udp_decoder()
        self.injector = udp_injector

    def stop(self):
        manager = AuditManager()
        manager.remove_decoder(PROTO_LAYER, NL_TYPE_UDP, self.decoder)
        manager.remove_injector(PROTO_LAYER, NL_TYPE_UDP, self.injector)

__plugins__ = [UDPDecoder]
__plugins_deps__ = [('UDPDecoder', ['IPDecoder'], ['=UDPDecoder-1.0'], [])]

__audit_type__ = 0
__protocols__ = (('udp', None), )
__configurations__ = (('decoder.udp', {
    'checksum_check' : [True, 'Enable checksum check for IP packets'],
    'enable_dissectors' : [True, 'Enable UDP protocol dissectors'],
    }),
)
