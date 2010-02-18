#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2010 Adriano Monteiro Marques
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
SMB protocol dissector (Passive audit)

>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-t9 -f ppp,ip,tcp,smb -sdecoder.tcp.checksum_check=0', 'smb-ntlmssp-auth.pcap')
dissector.smb.info SMB : 92.41.24.187:445 -> USER: _appowner HASH: _appowner:"":"":dc94e2d626ec44c200000000000000000000000000000000:84ec1f4fc3a5b08df6ec858e25b2b9a121caa83c0e234897:118cd5f944f353d4 DOMAIN: AUTOCHAP1 (failed)
dissector.smb.info SMB : 92.41.24.187:445 -> USER: _appowner HASH: _appowner:"":"":b228016a5678070d00000000000000000000000000000000:ffdd852dcd17dc9ec0a7d9bd55656d094c504cdc2a94cefb:a1e96d8f82855097 DOMAIN: AUTOCHAP1 (failed)
dissector.smb.info SMB : 92.41.24.187:445 -> USER: _appowner HASH: _appowner:"":"":c1903dc4ceccd00c00000000000000000000000000000000:263f025e78368a8985aed22e7111cbd507bd2a71f5124784:5db22c042e46cfe0 DOMAIN: AUTOCHAP1 (failed)
"""

import struct

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager

from umit.pm.backend import MetaPacket

WAITING_PLAIN_TEXT      = 1
WAITING_CHALLENGE       = 2
WAITING_RESPONSE        = 3
WAITING_ENCRYPT         = 4
WAITING_LOGON_RESPONSE  = 5
LOGON_COMPLETED_OK      = 6
LOGON_COMPLETED_FAILURE = 7

PLAIN_TEXT_AUTH         = 1
CHALLENGE_RESPONSE_AUTH = 2
NTLMSSP_AUTH            = 3

SMB_NAME = 'dissector.smb'
SMB_PORTS = (139, 445)

class SMBSession(object):
    def __init__(self):
        self.challenge = ''
        self.response1 = ''
        self.response2 = ''
        self.user = ''
        self.domain = ''
        self.status = 0
        self.auth_type = 0

    def __str__(self):
        return 'Challenge: %s Response1: %s Response2: %s ' \
               'User: %s Domain: %s' % \
               (self.challenge, self.response1,
                self.response2, self.user, self.domain)

    def report(self, mpkt, manager):
        #if self.status not in (LOGON_COMPLETED_OK, LOGON_COMPLETED_FAILURE):
        #    return

        username = self.user or 'anonymous'
        mpkt.set_cfield('username', username)

        domain = self.domain or ''

        if domain:
            domain = ' DOMAIN: %s' % domain

        if self.status == LOGON_COMPLETED_FAILURE:
            domain += ' (failed)'

        if self.auth_type  == PLAIN_TEXT_AUTH:
            password = self.response1

            if self.status == LOGON_COMPLETED_FAILURE:
                mpkt.set_cfield('password', password + ' (failed)')
            else:
                mpkt.set_cfield('password', password)

            manager.user_msg('SMB : %s:%d -> USER: %s PASS: %s%s' % \
                             (mpkt.l3_dst, mpkt.l4_dst,
                              username, password, domain), 6, SMB_NAME)
        else:
            convert = lambda x: "".join(
                [hex(ord(c))[2:].zfill(2) for c in x]
            )

            hash = '%s:"":"":%s:%s:%s' % (username,
                                          convert(self.response1[:24]),
                                          convert(self.response2[:24]),
                                          convert(self.challenge))

            if self.status == LOGON_COMPLETED_FAILURE:
                mpkt.set_cfield('password', hash + ' (failed)')
            else:
                mpkt.set_cfield('password', hash)

            manager.user_msg('SMB : %s:%d -> USER: %s HASH: %s%s' % \
                             (mpkt.l3_src, mpkt.l4_src,
                              username, hash, domain), 6, SMB_NAME)

def smb_dissector():
    manager = AuditManager()
    sessions = SessionManager()

    def smb(mpkt):
        try:
            nbt = MetaPacket.new_from_str('nbt', mpkt.data)
        except:
            return

        sess = sessions.lookup_session(mpkt, SMB_PORTS, SMB_NAME)

        if not sess:
            if nbt.get_field('smb.Start', '') != '\xffSMB':
                return

            # From server
            if mpkt.l4_src in SMB_PORTS and \
               nbt.get_field('smb.Command', 0) == 0x72:

                mpkt.set_cfield('banner', 'SMB')

                # Negotiate response
                sess = sessions.lookup_session(mpkt, SMB_PORTS, SMB_NAME, True)

                session_data = SMBSession()
                sess.data = session_data

                if nbt.get_field('smbneg_resp.SecurityMode', None) == 0:
                    session_data.auth_type = PLAIN_TEXT_AUTH
                    session_data.status = WAITING_PLAIN_TEXT
                else:
                    keylength, challenge = nbt.get_fields(
                        'smbneg_resp', ('EncryptionKeyLength', 'EncryptionKey')
                    )

                    if challenge:
                        keylength -= 1

                        while keylength >= 0:
                            session_data.challenge += struct.pack("B",
                                (challenge >> (8 * keylength)) & 255
                            )
                            keylength -= 1

                        session_data.status = WAITING_ENCRYPT
                        session_data.auth_type = CHALLENGE_RESPONSE_AUTH
                    else:
                        session_data.status = WAITING_CHALLENGE
                        session_data.auth_type = NTLMSSP_AUTH

            # From client
            if mpkt.l4_dst in SMB_PORTS and \
                 nbt.get_field('smb.Command', 0) == 0x73:

                blob = nbt.get_field('smbsax_req_as.SecurityBlob', '')
                idx = blob.find("NTLMSSP")

                if idx < 0:
                    return

                blob = blob[idx:]

                if blob[8] != '\x01':
                    return

                sess = sessions.lookup_session(mpkt, SMB_PORTS, SMB_NAME, True)

                session_data = SMBSession()
                session_data.status = WAITING_CHALLENGE
                session_data.auth_type = NTLMSSP_AUTH

                sess.data = session_data

        else:
            session_data = sess.data

            # Client packets
            if mpkt.l4_dst in SMB_PORTS:
                if session_data.auth_type == NTLMSSP_AUTH and \
                   session_data.status == LOGON_COMPLETED_FAILURE:

                    session_data.status = WAITING_CHALLENGE

                if nbt.get_field('smb.Start', '') != '\xffSMB':
                    return

                if nbt.get_field('smb.Command', 0) == 0x73:
                    if session_data.status == WAITING_PLAIN_TEXT or \
                       session_data.status == WAITING_ENCRYPT:

                        resp1, resp2, user, domain, os = \
                            nbt.get_fields('smbsax_req',
                                           ('ANSIPassword',
                                            'UnicodePassword',
                                            'Account',
                                            'PrimaryDomain',
                                            'NativeOS'))

                        path = nbt.get_field('smbtcax_req.Path', '')

                        session_data.response1 = resp1
                        session_data.response2 = resp2
                        session_data.user = user
                        session_data.domain = domain

                        if os:
                            session_data.domain += ' OS: %s' % os
                        if path:
                            session_data.domain += ' PATH: %s' % path

                        # Empty session
                        if not resp1.replace('\x00', '') and \
                           not resp2.replace('\x00', ''):
                            session_data.response1 = ''
                            session_data.response2 = ''
                            session_data.user = ''
                            #session_data.domain = ''

                        session_data.status = WAITING_LOGON_RESPONSE

                    elif session_data.status == WAITING_RESPONSE:
                        blob = nbt.get_field('smbsax_req_as.SecurityBlob', '')
                        idx = blob.find("NTLMSSP")

                        if idx < 0:
                            return

                        blob = blob[idx:]

                        if blob[8] == '\x03':
                            lm_len = ord(blob[12])
                            lm_off = ord(blob[16])
                            nt_len = ord(blob[20])
                            nt_off = ord(blob[24])
                            dm_len = ord(blob[28])
                            dm_off = ord(blob[32])
                            un_len = ord(blob[36])
                            un_off = ord(blob[40])

                            if nt_len != 24:
                                session_data.status = WAITING_CHALLENGE
                                return

                            session_data.user = blob[un_off:un_off + un_len].replace('\x00', '')
                            session_data.domain = blob[dm_off:dm_off + dm_len].replace('\x00', '')

                            if lm_len == 24:
                                session_data.response1 = blob[lm_off:lm_off + 24]

                            session_data.response2 = blob[nt_off:nt_off + 24]
                            session_data.status = WAITING_LOGON_RESPONSE


            else:
                # Server packets
                if nbt.get_field('smb.Command', 0) == 0x73:
                    if session_data.status == WAITING_CHALLENGE:
                        blob = nbt.get_field('smbsax_resp_as.SecurityBlob', '')
                        idx = blob.find('NTLMSSP')

                        if idx < 0:
                            return

                        blob = blob[idx:]

                        if blob[8] == '\x02':
                            session_data.challenge = blob[8 + 16:8 + 16 + 8]
                            session_data.status = WAITING_RESPONSE

                    elif session_data.status == WAITING_LOGON_RESPONSE:
                        if mpkt.get_field('smb.Error_Class', 0) == 0:
                            session_data.status = LOGON_COMPLETED_OK
                            session_data.report(mpkt, manager)

                            sessions.delete_session(sess)
                        else:
                            session_data.status = LOGON_COMPLETED_FAILURE
                            session_data.report(mpkt, manager)

                            if session_data.auth_type == CHALLENGE_RESPONSE_AUTH:
                                session_data.status = WAITING_ENCRYPT

    return smb

class SMBDissector(Plugin, PassiveAudit):
    def start(self, reader):
        self.dissector = smb_dissector()

    def register_decoders(self):
        for port in (139, 445):
            AuditManager().add_dissector(APP_LAYER_TCP, port, self.dissector)

    def stop(self):
        for port in (139, 445):
            AuditManager().remove_dissector(APP_LAYER_TCP, port, self.dissector)

__plugins__ = [SMBDissector]
__plugins_deps__ = [('SMBDissector', ['TCPDecoder'], ['SMBDissector-1.0'], []),]

__audit_type__ = 0
__protocols__ = (('tcp', 139), ('tcp', 445), ('smb', None))
__vulnerabilities__ = (('SMB dissector', {
    'description' : 'In computer networking, Server Message Block (SMB, also '
                    'known as Common Internet File System, CIFS) operates as '
                    'an application-layer network protocol[1] mainly used to '
                    'provide shared access to files, printers, serial ports, '
                    'and miscellaneous communications between nodes on a '
                    'network. It also provides an authenticated inter-process'
                    ' communication mechanism. Most usage of SMB involves '
                    'computers running Microsoft Windows, where it is often '
                    'known as "Microsoft Windows Network.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'Server_Message_Block'), )
    }),
)
