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

        sess = sessions.lookup_session(mpkt, SIP_PORTS, SIP_NAME, True)

        conf = manager.get_configuration(SIP_NAME)
        sip_fields = conf['sip_fields']

        payload = mpkt.data
        payload.strip()

        pos = payload.find('Authorization')
        if pos != -1:
            found = 1
            val = payload[pos+13:]
            end = val.find('\r\n')
            val = val[:end]
            val = val.strip(':').strip()
            val = val.strip('Digest').strip()

            for value in val.split(','):
                ret = value.strip().split('=', 1)

                if isinstance(ret, list) and len(ret) == 2:
                    k, v = ret

                    if v[0] == v[-1] and (v[0] == '"' or v[0] == '\''):
                        v = v[1:-1]

                    if k.upper() == 'USERNAME':
                        mpkt.set_cfield(SIP_NAME + '.username', v)
                    elif k.upper() == 'REALM':
                        mpkt.set_cfield(SIP_NAME + '.realm', v)
                    elif k.upper() == 'NONCE':
                        mpkt.set_cfield(SIP_NAME + '.nonce', v)
                    elif k.upper() == 'URI':
                        mpkt.set_cfield(SIP_NAME + '.uri', v)
                    elif k.upper() == 'ALGORITHM':
                        mpkt.set_cfield(SIP_NAME + '.algorithm', v)
                    elif k.upper() == 'RESPONSE':
                        mpkt.set_cfield(SIP_NAME + '.response', v)

            #Here check for sip_fields


            if found:
                manager.user_msg('SIP: %s:%d FOUND %s' % \
                                      (mpkt.l3_src, mpkt.l4_src, val), 6, SIP_NAME)



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

            self.manager.deregister_hook_point('sip')


__plugins__ = [SIPMonitor]
__plugins_deps__ = [('SIPDissector', ['UDPDecoder'], ['SIPDissector-1.0'], []),]
__author__ = ['Guilherme Rezende']
__audit_type__ = 0
__protocols__ = (('udp', 5060), ('udp', 5061), ('sip', None))
__configurations__ = (('global.cfields', {
    SIP_NAME + '.username' : (PM_TYPE_STR, 'SIP username'),
    SIP_NAME + '.request_useragent' : (PM_TYPE_STR, 'SIP request user-agent'),
    SIP_NAME + '.response_useragent' : (PM_TYPE_STR, 'SIP response user-agent'),
    SIP_NAME + '.algorithm' : (PM_TYPE_STR, 'SIP hash algorithm'),
    SIP_NAME + '.realm' : (PM_TYPE_STR, 'SIP authorization param to calculate hash'),
    SIP_NAME + '.nonce' : (PM_TYPE_STR, 'SIP authorization'),
    SIP_NAME + '.uri' : (PM_TYPE_STR, 'SIP field URI requested by the client'),
    SIP_NAME + '.response' : (PM_TYPE_STR, 'SIP password hash'),
    }),

    (SIP_NAME, {
        'sip_fields' : ["Contact,To,Via,From,User-Agent,Server",

                        'A coma separated string of sip fields'],
    }),
)
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