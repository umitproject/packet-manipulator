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
BOOTP protocol dissector
"""

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager

DHCP_DISCOVER = 0x01
DHCP_REQUEST  = 0x03

def bootp_dissector():
    BOOTP_NAME = 'dissector.bootp'

    manager = AuditManager()

    def bootp(mpkt):
        try:
            for option in mpkt.get_field('dhcp.options'):
                if not isinstance(option, tuple):
                    continue

                name, value = option

                if name == 'message-type':
                    if value == DHCP_DISCOVER:
                        manager.run_hook_point('dhcp-discover', mpkt)
                    elif value == DHCP_REQUEST:
                        manager.run_hook_point('dhcp-request', mpkt)
        except:
            pass

    return bootp

class BOOTPDissector(Plugin, PassiveAudit):
    def start(self, reader):
        self.dissector = bootp_dissector()

    def register_decoders(self):
        for name in ('dhcp-discover', 'dhcp-request'):
            AuditManager().register_hook_point(name)

        AuditManager().add_dissector(APP_LAYER_UDP, 67, self.dissector)

    def stop(self):
        for name in ('dhcp-discover', 'dhcp-request'):
            AuditManager().deregister_hook_point(name)

        AuditManager().remove_dissector(APP_LAYER_UDP, 67, self.dissector)

__plugins__ = [BOOTPDissector]
__plugins_deps__ = [('BOOTPDissector', ['UDPDecoder'], ['BOOTPDissector-1.0', 'DHCPDissector-1.0'], []),]

__audit_type__ = 0
__protocols__ = (('udp', 67), ('bootp', None), ('dhcp', None))
__vulnerabilities__ = (('BOOTP dissector', {
    'description' : 'In computer networking, the Bootstrap Protocol, or '
                    'BOOTP, is a network protocol used by a network client '
                    'to obtain an IP address from a configuration server. '
                    'The BOOTP protocol was originally defined in RFC 951.\n'
                    'BOOTP is usually used during the bootstrap process when '
                    'a computer is starting up. A BOOTP configuration server '
                    'assigns an IP address to each client from a pool of '
                    'addresses. BOOTP uses the User Datagram Protocol (UDP) '
                    'as a transport on IPv4 networks only.\n'
                    'The Dynamic Host Configuration Protocol (DHCP) is a '
                    'more advanced protocol for the same purpose and has '
                    'superseded the use of BOOTP. Most BOOTP servers also '
                    'offer BOOTP support.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'Bootstrap_Protocol'), )
    }),
)
