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
ICMP decoder

>>> from PM.Core.AuditUtils import audit_unittest
>>> audit_unittest('-f ethernet,ip,icmp', 'wrong-checksum-icmp.pcap')
decoder.icmp.notice Invalid ICMP packet from 127.0.0.1 to 127.0.0.1 : wrong checksum 0x29a instead of 0xfde3
decoder.icmp.notice Invalid ICMP packet from 127.0.0.1 to 127.0.0.1 : wrong checksum 0x7a69 instead of 0x5e4
"""

from struct import unpack
from PM.Core.I18N import _
from PM.Core.AuditUtils import checksum
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AuditManager import AuditManager, PassiveAudit, \
                                       PROTO_LAYER, NL_TYPE_ICMP
def icmp_decoder():
    manager = AuditManager()

    conf = manager.get_configuration('decoder.icmp')
    checksum_check = conf['checksum_check']

    def icmp(mpkt):
        if not checksum_check:
            return None

        if mpkt.get_field('ip.flags') & 1:
            # Only a fragment
            return None

        payload = mpkt.cfields.get('reassembled_payload', None)

        if not payload:
            payload = mpkt.get_field('icmp')

            if not payload:
                return None

        cur_chksum = hex(unpack("!H", payload[2:4])[0])
        icmpraw = payload[0:2] + '\x00\x00' + payload[4:]
        com_chksum = hex(checksum(icmpraw))

        if com_chksum != cur_chksum:
            mpkt.set_cfield('good_checksum', com_chksum)
            manager.user_msg(_("Invalid ICMP packet from %s to %s : " \
                               "wrong checksum %s instead of %s") %  \
                             (mpkt.get_field('ip.src'),          \
                              mpkt.get_field('ip.dst'),          \
                              cur_chksum, com_chksum),
                             5, 'decoder.icmp')

        return None

    return icmp

class ICMPDecoder(Plugin, PassiveAudit):
    def register_decoders(self):
        AuditManager().add_decoder(PROTO_LAYER, NL_TYPE_ICMP, icmp_decoder())

__plugins__ = [ICMPDecoder]
__audit_type__ = 0
__protocols__ = (('icmp', None), )
__configurations__ = (('decoder.icmp', {
    'checksum_check' : ['True', 'Check for correct checksum of ICMP packets'],}),
)
