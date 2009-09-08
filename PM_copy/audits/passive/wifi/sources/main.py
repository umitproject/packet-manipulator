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
Wifi protocol decoder
"""

# Leaves commented for now.
#>>> from umit.pm.core.netconst import IL_TYPE_WIFI
#>>> from umit.pm.core.auditutils import audit_unittest
#>>> audit_unittest('-fwifi', 'wifi.pcap', IL_TYPE_WIFI)

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.core.netconst import *

def wifi_decoder(mpkt):
    if not mpkt.get_field('wifi', None):
        return None

    return NET_LAYER, mpkt.get_field('wifi.proto', 0)

class WifiDecoder(Plugin, PassiveAudit):
    def stop(self):
        AuditManager().remove_decoder(LINK_LAYER, IL_TYPE_WIFI, wifi_decoder)

    def register_decoders(self):
        AuditManager().add_decoder(LINK_LAYER, IL_TYPE_WIFI, wifi_decoder)

__plugins__ = [WifiDecoder]
__plugins_deps__ = [('WifiDecoder', [], ['=WifiDecoder-1.0'], [])]
__audit_type__ = 0
__protocols__ = (('wifi', None), ('802.11', None))
__vulnerabilities__ = (('IEEE 802.11 decoder', {
    'description' : 'IEEE 802.11 is a set of standards carrying out wireless '
                    'local area network (WLAN) computer communication in the '
                    '2.4, 3.6 and 5 GHz frequency bands. They are implemented '
                    'by the IEEE LAN/MAN Standards Committee (IEEE 802).',
    'references' : ((None, 'http://en.wikipedia.org/wiki/IEEE_802.11'), )
    }),
)
