#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Adriano Monteiro Marques
#Author: Tiago Serra <pwerspire@gmail.com>
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
IMAP protocol dissector (Passive audit).

This module uses TCP reassembler exposed in TCP decoder.
>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip,tcp,imap', 'imap.pcap')
dissector.imap.info IMAP CRAM-MD5 : 10.0.1.102:143 -> USER: hemmingway Digest: 29f20b669347aa081749065d903a49e4
dissector.imap.info IMAP : 127.0.0.1:143 -> USER: fred PASS: flinstone
"""

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager
import base64 


def imap_dissector():
    IMAP_NAME = 'dissector.imap'
    IMAP_PORTS = (143, )

    manager = AuditManager()
    sessions = SessionManager()
    
    def imap(mpkt):
        
        
        if sessions.create_session_on_sack(mpkt, IMAP_PORTS, IMAP_NAME):
            return

        # Skip empty and server packets
        if mpkt.l4_dst not in IMAP_PORTS or not mpkt.data:
            return
        
        payload = mpkt.data.strip()
        str = payload.split(' ')
        
        sess = sessions.lookup_session(mpkt, IMAP_PORTS, IMAP_NAME, True)
        
        if isinstance(str, list) and str[0].upper() == 'A0001' or str[0].upper() == 'A001' or str[0].upper() == 'A00001':
            
            if str[1].upper() == 'AUTHENTICATE' and str[2].upper() == 'CRAM-MD5' :
                sess.data = ['AUTHENTICATE CRAM-MD5', None,None]
                return
            
            elif str[1].upper()  =='LOGIN':
                sess.data = [str[2],str[3]]
                manager.user_msg('IMAP : %s:%d -> USER: %s PASS: %s' % \
                                 (mpkt.l3_dst, mpkt.l4_dst,
                                  sess.data[0] or '',
                                  sess.data[1] or ''),
                                  6, IMAP_NAME)
                
                mpkt.set_cfield('username', sess.data[0])
                mpkt.set_cfield('password', sess.data[1])
        
                sessions.delete_session(sess)
            
        elif isinstance(sess.data, list) and sess.data[0] == 'AUTHENTICATE CRAM-MD5':
            str = base64.decodestring(payload)
            str = str.split(' ')
            sess.data[1] = str[0]
            sess.data[2] = str[1]
            manager.user_msg('IMAP CRAM-MD5 : %s:%d -> USER: %s Digest: %s' % \
                              (mpkt.l3_dst, mpkt.l4_dst,
                               sess.data[1] or '',
                               sess.data[2] or ''),
                               6, IMAP_NAME)
                    
                    
            mpkt.set_cfield('username', sess.data[1])
            mpkt.set_cfield('password', sess.data[1])
            sessions.delete_session(sess)
            return
                
    return imap



class IMAPDissector(Plugin, PassiveAudit):
    
    def start(self, reader):
        self.dissector =imap_dissector()

    def register_decoders(self):
        AuditManager().add_dissector(APP_LAYER_TCP, 143, self.dissector)

    def stop(self):
        AuditManager().remove_dissector(APP_LAYER_TCP, 143, self.dissector)
        
        
__plugins__ = [IMAPDissector]
__plugins_deps__ = [('IMAPDissector', ['TCPDecoder'], ['IMAPDissector-0.4'], []),]

__audit_type__ = 0
__protocols__ = (('tcp', 143), ('imap', None))
__vulnerabilities__ = (('IMAP dissector', {
    'description' : 'The Internet Message Access Protocol (commonly known as IMAP) is an Application Layer Internet protocol that allows an e-mail client to access e-mail on a remote mail server',
    'references' : ((None, 'http://en.wikipedia.org/wiki/Internet_Message_Access_Protocol'), )
    }),
)