#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Adriano Monteiro Marques
# Author: Tiago Serra <pwerspire@gmail.com>
# Based in FTP audit code by Francesco Piccinno <stack.box@gmail.com>
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
POP3 protocol dissector (Passive audit).

This module uses TCP reassembler exposed in TCP decoder.
>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip,tcp,pop3', 'pop3.pcap')
dissector.pop3.info POP3 : 192.168.7.140:110 -> USER: test PASS: testing123
dissector.pop3.info POP3 CRAM-MD5: 127.0.0.1:110 -> USER:  Digest: 1ae0dcf86f1147802ab636f75e10ff8e

"""
from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager
import base64

def pop3_dissector():
    POP3_NAME = 'dissector.pop3'
    POP3_PORTS = (110, )

    manager = AuditManager()
    sessions = SessionManager()

    def pop3(mpkt):
        if sessions.create_session_on_sack(mpkt, POP3_PORTS, POP3_NAME):
            return

        # Skip empty and server packets
        if mpkt.l4_dst not in POP3_PORTS or not mpkt.data:
            return

        payload = mpkt.data.strip()
        
        sess = sessions.lookup_session(mpkt, POP3_PORTS, POP3_NAME, True)
        
        if payload.upper() == 'AUTH CRAM-MD5' :
            sess.data = ['AUTH CRAM-MD5', None,None]
            return
       
       
        if isinstance(sess.data, list) and sess.data[0].upper() == 'AUTH CRAM-MD5' :
            str = base64.decodestring(payload)
            str = str.split(' ')
            sess.data[1] = str[0]
            sess.data[2] = str[1]
            
            manager.user_msg('POP3 CRAM-MD5: %s:%d -> USER: %s Digest: %s' % \
                             (mpkt.l3_dst, mpkt.l4_dst,
                              sess.data[1] or '',
                              sess.data[2] or ''),
                              6, POP3_NAME)
            mpkt.set_cfield('username', sess.data[1])
            sessions.delete_session(sess)
            return

        if payload[:5].upper() == 'USER ':
            
            if isinstance(sess.data, list):
                sess.data[0] = payload[5:]
            else:
                sess.data = [payload[5:], None]
        elif payload[:5].upper() == 'PASS ':
            
            if isinstance(sess.data, list):
                sess.data[1] = payload[5:]
            else:
                sess.data = [None, payload[5:]]

            manager.user_msg('POP3 : %s:%d -> USER: %s PASS: %s' % \
                             (mpkt.l3_dst, mpkt.l4_dst,
                              sess.data[0] or '',
                              sess.data[1] or ''),
                              6, POP3_NAME)

            mpkt.set_cfield('username', sess.data[0])
            mpkt.set_cfield('password', sess.data[1])

            sessions.delete_session(sess)

    return pop3







class POP3Dissector(Plugin, PassiveAudit):
    
    def start(self, reader):
        self.dissector =pop3_dissector()

    def register_decoders(self):
        AuditManager().add_dissector(APP_LAYER_TCP, 110, self.dissector)

    def stop(self):
        AuditManager().remove_dissector(APP_LAYER_TCP, 110, self.dissector)
        
        
__plugins__ = [POP3Dissector]
__plugins_deps__ = [('POP3Dissector', ['TCPDecoder'], ['POP3Dissector-0.1'], []),]

__audit_type__ = 0
__protocols__ = (('tcp', 110), ('pop3', None))
__vulnerabilities__ = (('POP3 dissector', {
    'description' : 'n computing, the Post Office Protocol (POP) is an application-layer Internet standard protocol used by local e-mail clients to retrieve e-mail from a remote server over a TCP/IP connection',
    'references' : ((None, 'http://en.wikipedia.org/wiki/Post_Office_Protocol'), )
    }),
)