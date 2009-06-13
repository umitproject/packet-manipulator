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

>>> from PM.Core.AttackUtils import attack_unittest
>>> attack_unittest('-f ethernet,ip', 'wrong-checksum.pcap')
decoder.ip.notice Invalid IP packet from 127.0.0.1 to 127.0.0.1 : wrong checksum 0xdead instead of 0x7bce
"""
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import AttackManager, OfflineAttack
from PM.Core.NetConst import PROTO_LAYER, NET_LAYER, LL_TYPE_IP
from PM.Core.AttackUtils import checksum

def ip_decoder():
    manager = AttackManager()
    checksum_check = manager.get_configuration('decoder.ip')['checksum_check']

    def internal(mpkt):
        if checksum_check:
            ipraw = mpkt.get_field('ip')
            iplen = min(20, len(ipraw))

            pkt = ipraw[:10] + '\x00\x00' + ipraw[12:iplen]

            chksum = checksum(pkt)

            if mpkt.get_field('ip.chksum') != chksum:
                manager.user_msg("Invalid IP packet from %s to %s : " \
                                 "wrong checksum %s instead of %s" %  \
                                 (mpkt.get_field('ip.src'),          \
                                  mpkt.get_field('ip.dst'),          \
                                  hex(mpkt.get_field('ip.chksum')),  \
                                  hex(chksum)),
                                 5, 'decoder.ip')

        return PROTO_LAYER, mpkt.get_field('ip.proto')

    return internal

class IPDecoder(Plugin, OfflineAttack):
    def register_options(self):
        conf = AttackManager().register_configuration('decoder.ip')
        conf.register_option('checksum_check', True, bool)

    def register_decoders(self):
        AttackManager().add_decoder(NET_LAYER, LL_TYPE_IP, ip_decoder())

__plugins__ = [IPDecoder]
__plugins_deps__ = [('IPDecoder', [], [], [])]
