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
Ethernet protocol decoder
"""

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.core.netconst import *

def eth_decoder(mpkt):
    mpkt.l2_proto = IL_TYPE_ETH
    mpkt.l2_len = 14
    mpkt.l2_src, \
    mpkt.l2_dst, \
    mpkt.l3_proto = mpkt.get_fields('eth', ('src', 'dst', 'type'))

    # Also handle ARP assignment
    if mpkt.l3_proto == LL_TYPE_ARP:
        mpkt.l3_src, \
        mpkt.l3_dst = mpkt.get_fields('arp', ('psrc', 'pdst'))

    return NET_LAYER, mpkt.l3_proto

class EthDecoder(Plugin, PassiveAudit):
    def stop(self):
        AuditManager().remove_decoder(LINK_LAYER, IL_TYPE_ETH, eth_decoder)

    def register_decoders(self):
        AuditManager().add_decoder(LINK_LAYER, IL_TYPE_ETH, eth_decoder)

__plugins__ = [EthDecoder]
__plugins_deps__ = [('EthDecoder', [], ['=EthDecoder-1.0'], [])]

__audit_type__ = 0
__protocols__ = (('eth', None), )
__vulnerabilities__ = (('Ethernet decoder', {
    'description' : 'Ethernet is a family of frame-based computer networking '
                    'technologies for local area networks (LANs). The name '
                    'comes from the physical concept of the ether. It defines '
                    'a number of wiring and signaling standards for the '
                    'Physical Layer of the OSI networking model, through '
                    'means of network access at the Media Access Control '
                    '(MAC) /Data Link Layer, and a common addressing format.'
                    '\n\n'
                    'Ethernet is standardized as IEEE 802.3. The combination '
                    'of the twisted pair versions of Ethernet for connecting '
                    'end systems to the network, along with the fiber optic '
                    'versions for site backbones, is the most widespread '
                    'wired LAN technology. It has been in use from around '
                    '1980[1] to the present, largely replacing competing LAN '
                    'standards such as token ring, FDDI, and ARCNET.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/Ethernet'), )
    }),
)
