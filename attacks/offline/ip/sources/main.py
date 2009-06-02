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
IP protocol decoder
"""

import array
import struct

from PM.Backend import checksum, hexdump
from PM.Core.Logger import log
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import *
from PM.Core.NetConst import *

# Code ripped from scapy
BIG_ENDIAN= struct.pack("H",1) == "\x00\x01"

if BIG_ENDIAN:
    def checksum(pkt):
        if len(pkt) % 2 == 1:
            pkt += "\0"
        s = sum(array.array("H", pkt))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        s = ~s
        return s & 0xffff
else:
    def checksum(pkt):
        if len(pkt) % 2 == 1:
            pkt += "\0"
        s = sum(array.array("H", pkt))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        s = ~s
        return (((s>>8)&0xff)|s<<8) & 0xffff

@coroutine
def ip_decoder():
    try:
        while True:
            mpkt = (yield)

            ipraw = mpkt.get_field('ip')
            iplen = min(20, len(ipraw))

            pkt = ipraw[:10] + '\x00\x00' + ipraw[12:iplen]

            chksum = checksum(pkt)

            if mpkt.get_field('ip.chksum') != chksum:
                print "Wrong checksum"

            AttackManager().run_decoder(PROTO_LAYER,
                                        mpkt.get_field('ip.proto'),
                                        mpkt)
    except GeneratorExit:
        pass

class IPDecoder(Plugin, OfflineAttack):
    def start(self, reader):
        self._decoder = ip_decoder()

    def stop(self):
        pass

    def register_decoders(self):
        AttackManager().add_decoder(NET_LAYER, LL_TYPE_IP, self._decoder)

__plugins__ = [IPDecoder]