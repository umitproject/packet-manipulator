#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Adriano Monteiro Marques
#
# Author: Tiago Serra <pwerspire@gmail.com>
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

from umit.pm.core.logger import log    
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager
import base64

def smtp_dissector():
    SMTP_NAME = 'dissector.smtp'
    SMTP_PORTS = (25, )

    manager = AuditManager()
    sessions = SessionManager()
    
    
    
    
    
    def smtp(mpkt):
        if sessions.create_session_on_sack(mpkt, SMTP_PORTS, SMTP_NAME):
            return

        sess = sessions.is_first_pkt_from_server(mpkt, SMTP_PORTS, SMTP_NAME)

        if sess and not sess.data:
            payload = mpkt.data

            # Ok we have an SMTP banner over here
            if payload and payload.startswith('220'):
                banner = payload[4:].strip()
                mpkt.set_cfield('banner', banner)

                manager.user_msg('SMTP : %s:%d banner: %s' % \
                                 (mpkt.l3_src, mpkt.l4_src, banner),
                                 6, SMTP_NAME)

            sessions.delete_session(sess)
            return

        # Skip empty and server packets
        if mpkt.l4_dst not in SMTP_PORTS or not mpkt.data:
            return

        payload = mpkt.data.strip()
        sess = sessions.lookup_session(mpkt, SMTP_PORTS, SMTP_NAME, True)
        
        if payload[:10].upper() == 'AUTH PLAIN':
            login=base64.decodestring((payload[11:]))
            login=login.split('\x00')
            
            for str in login:
                
                if not sess.data  and not str =='':
                    sess.data=[str,None]
                   
                if sess.data  and not str =='':
                    sess.data[1]=str
                    
            
            manager.user_msg('SMTP : %s:%d -> USER: %s PASS: %s' % \
                             (mpkt.l3_dst, mpkt.l4_dst,
                              sess.data[0] or '',
                              sess.data[1] or ''),
                              6, SMTP_NAME)

            mpkt.set_cfield('username', sess.data[0])
            mpkt.set_cfield('password', sess.data[1])

            sessions.delete_session(sess)
            
        elif payload.upper() == 'AUTH LOGIN':
            sess.data = ['AUTH LOGIN',None,None]
        
        elif sess.data  and sess.data[0] == 'AUTH LOGIN' and not sess.data[1] :
            sess.data[1]=base64.decodestring(payload)
           
            
        elif sess.data  and sess.data[0] == 'AUTH LOGIN' and  sess.data[1] : 
            sess.data[2]=base64.decodestring(payload)
            
            manager.user_msg('SMTP : %s:%d -> USER: %s PASS: %s' % \
                             (mpkt.l3_dst, mpkt.l4_dst,
                              sess.data[1] or '',
                              sess.data[2] or ''),
                              6, SMTP_NAME)
                
            mpkt.set_cfield('username', sess.data[1])
            mpkt.set_cfield('password', sess.data[2])    
                
            sessions.delete_session(sess)
                
            
            
    return smtp


class SMTPDissector(Plugin, PassiveAudit):
    
    def start(self, reader):
        self.dissector =smtp_dissector()

    def register_decoders(self):
        AuditManager().add_dissector(APP_LAYER_TCP, 25, self.dissector)

    def stop(self):
        AuditManager().remove_dissector(APP_LAYER_TCP, 25, self.dissector)
        
        
__plugins__ = [SMTPDissector]
__plugins_deps__ = [('SMTPDissector', ['TCPDecoder'], ['SMTPDissector-1.0'], []),]
__author__ = ['Tiago Serra']
__audit_type__ = 0
__protocols__ = (('tcp', 25), ('smtp', None))
__vulnerabilities__ = (('SMTP dissector', {
    'description' : 'Simple Mail Transfer Protocol (SMTP) is an Internet standard for electronic mail (e-mail) transmission across Internet Protocol (IP) networks.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol'), )
    }),
)
