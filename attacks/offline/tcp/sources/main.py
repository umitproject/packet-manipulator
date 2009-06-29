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

from struct import pack
from socket import inet_aton

from PM.Core.Logger import log
from PM.Gui.Plugins.Core import Core
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import AttackManager, OfflineAttack
from PM.Core.NetConst import PROTO_LAYER, NL_TYPE_TCP, NL_TYPE_UDP, \
                              APP_LAYER_TCP, APP_LAYER_UDP, NEED_FRAGMENT
from PM.Core.AttackUtils import checksum

class Reassembler(object):
    def __init__(self):
        pass

    def reassemble_stream(mpkt):
        pass

def tcp_decoder():
    manager = AttackManager()
    conf = manager.get_configuration('decoder.tcp')

    checksum_check, dissectors = \
        conf['checksum_check'], conf['enable_dissectors']

    reas = conf['enable_reassemble'] and Reassembler() or None

    def tcp(mpkt):
        if checksum_check:
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
                        manager.user_msg("Invalid TCP packet from %s to %s : " \
                                         "wrong checksum %s instead of %s" %   \
                                         (ip_src, ip_dst,                      \
                                          hex(mpkt.get_field('tcp.chksum')),   \
                                          hex(chksum)),
                                         5, 'decoder.tcp')

        if not dissectors:
            return None

        # At this point we could look for reasonable dissectors
        if manager.run_decoder(APP_LAYER_TCP, mpkt.get_field('tcp.dport'),
                               mpkt) == NEED_FRAGMENT and reas:

            reas.reassemble_stream(mpkt)

        if manager.run_decoder(APP_LAYER_TCP, mpkt.get_field('tcp.sport'),
                               mpkt) == NEED_FRAGMENT and reas:

            reas.reassemble_stream(mpkt)

        # TODO: Here we've to handle injected buffer and split overflowed
        # data in various packets (check MTU).

        # Nothing to parse at this point
        return None

    return tcp

class TCPDecoder(Plugin, OfflineAttack):
    def register_options(self):
        conf = AttackManager().register_configuration('decoder.tcp')
        conf.register_option('checksum_check', True, bool)
        conf.register_option('enable_dissectors', True, bool)
        conf.register_option('enable_reassemble', True, bool)

    def register_decoders(self):
        AttackManager().add_decoder(PROTO_LAYER, NL_TYPE_TCP, tcp_decoder())

__plugins__ = [TCPDecoder]
__plugins_deps__ = [('TCPDecoder', ['IPDecoder'], [], [])]