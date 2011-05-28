#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Adriano Monteiro Marques
#
# Author: Francesco Piccinno <stack.box@gmail.com>
# Author: Guilherme Rezende <guilhermebr@gmail.com>
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
SIP protocol dissector (Passive audit)
"""

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager

SIP_NAME = 'dissector.sip'
SIP_PORTS = (5060, 5061)

def sip_dissector():

    manager = AuditManager()
    sessions = SessionManager()
    
    def sip(mpkt):
        
        sess = sessions.is_first_pkt_from_server(mpkt, SIP_PORTS, SIP_NAME)

        if sess and not sess.data:
            payload = mpkt.data

            if payload and payload.startswith('REGISTER'):
                banner = payload[8:].strip()
                manager.user_msg('SIP : %s:%d REGISTER: %s' % \
                                 (mpkt.l3_src, mpkt.l4_src, banner),
                                 6, SIP_NAME)
            sessions.delete_session(sess)
            return
        
         # Skip empty and server packets
        if mpkt.l4_dst not in SIP_PORTS or not mpkt.data:
            return

        payload = mpkt.data.strip()
        manager.user_msg('SIP : %s:%d -> %s' % \
                        (mpkt.l3_dst, mpkt.l4_dst, payload),
                        6, SIP_NAME)
                             
        sessions.delete_session(sess)

        return sip
    
class SIPMonitor(Plugin, PassiveAudit):
    def start(self, reader):
        self.manager = AuditManager()
        self.dissector = sip_dissector()

    def register_decoders(self):

        self.manager.register_hook_point('sip')

        for port in SIP_PORTS:
            self.manager.add_dissector(APP_LAYER_UDP, port,
                                           self.dissector)
        

    def stop(self):
        for port in SIP_PORTS:
            self.manager.remove_dissector(APP_LAYER_UDP, port,
                                           self.dissector)

__plugins__ = [SIPMonitor]
__plugins_deps__ = [('SIPDissector', ['UDPDecoder'], ['SIPDissector-1.0'], []),]
__author__ = ['Guilherme Rezende']
__audit_type__ = 0
__protocols__ = (('udp', 5060), ('udp', 5061), ('sip', None))
__vulnerabilities__ = (('SIP dissector', {
    'description' : 'SIP Monitor plugin'
        'The Session Initiation Protocol (SIP) is an IETF-defined signaling protocol,'
        'widely used for controlling multimedia communication sessions'
        'such as voice and video calls over' 
        'Internet Protocol (IP). The protocol can be used for creating,'
        'modifying and terminating two-party (unicast) or multiparty (multicast)'
        'sessions consisting of one or several media streams.'
        'The modification can involve changing addresses or ports, inviting more' 
        'participants, and adding or deleting media streams. Other feasible'
        'application examples include video conferencing, streaming multimedia distribution,'
        'instant messaging, presence information, file transfer and online games.'
        'SIP was originally designed by Henning Schulzrinne and Mark Handley starting in 1996.'
        'The latest version of the specification is RFC 3261 from the IETF Network Working'
        'Group. In November 2000, SIP was accepted as a 3GPP signaling protocol and permanent'
        'element of the IP Multimedia Subsystem (IMS) architecture for IP-based streaming'
        'multimedia services in cellular systems.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'Session_Initiation_Protocol'), )
    }),
)