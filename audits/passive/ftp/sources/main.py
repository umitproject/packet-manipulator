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
FTP protocol dissector (Passive audit)

>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip,tcp,ftp', 'ftp-login.pcap')
dissector.ftp.info FTP : 127.0.0.1:21 -> USER: anonymous PASS: guest@example.com
"""

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager


def ftp_dissector():
    FTP_NAME = 'dissector.ftp'
    FTP_PORTS = (21, )

    manager = AuditManager()
    sessions = SessionManager()

    def ftp(mpkt):
        if sessions.create_session_on_sack(mpkt, FTP_PORTS, FTP_NAME):
            return

        sess = sessions.is_first_pkt_from_server(mpkt, FTP_PORTS, FTP_NAME)

        if sess and not sess.data:
            payload = mpkt.data

            # Ok we have an FTP banner over here
            if payload and payload.startswith('220'):
                banner = payload[4:].strip()
                mpkt.set_cfield('banner', banner)

                manager.user_msg('FTP : %s:%d banner: %s' % \
                                 (mpkt.l3_src, mpkt.l4_src, banner),
                                 6, FTP_NAME)

            sessions.delete_session(sess)
            return

        # Skip empty and server packets
        if mpkt.l4_dst not in FTP_PORTS or not mpkt.data:
            return

        payload = mpkt.data.strip()

        if payload[:5].upper() == 'USER ':
            sess = sessions.lookup_session(mpkt, FTP_PORTS, FTP_NAME, True)

            if isinstance(sess.data, list):
                sess.data[0] = payload[5:]
            else:
                sess.data = [payload[5:], None]
        elif payload[:5].upper() == 'PASS ':
            sess = sessions.lookup_session(mpkt, FTP_PORTS, FTP_NAME, True)

            if isinstance(sess.data, list):
                sess.data[1] = payload[5:]
            else:
                sess.data = [None, payload[5:]]

            manager.user_msg('FTP : %s:%d -> USER: %s PASS: %s' % \
                             (mpkt.l3_dst, mpkt.l4_dst,
                              sess.data[0] or '',
                              sess.data[1] or ''),
                              6, FTP_NAME)

            mpkt.set_cfield('username', sess.data[0])
            mpkt.set_cfield('password', sess.data[1])

            sessions.delete_session(sess)

    return ftp

class FTPDissector(Plugin, PassiveAudit):
    def start(self, reader):
        self.dissector = ftp_dissector()

    def register_decoders(self):
        AuditManager().add_dissector(APP_LAYER_TCP, 21, self.dissector)

    def stop(self):
        AuditManager().remove_dissector(APP_LAYER_TCP, 21, self.dissector)

__plugins__ = [FTPDissector]
__plugins_deps__ = [('FTPDissector', ['TCPDecoder'], ['FTPDissector-1.0'], []),]

__audit_type__ = 0
__protocols__ = (('tcp', 21), ('ftp', None))
__vulnerabilities__ = (('FTP dissector', {
    'description' : 'File Transfer Protocol (FTP) is a standard network '
                    'protocol used to exchange and manipulate files over an '
                    'Internet Protocol computer network, such as the Internet. '
                    'FTP is built on a client-server architecture and utilizes '
                    'separate control and data connections between the client '
                    'and server applications. Client applications were '
                    'originally interactive command-line tools with a '
                    'standardized command syntax, but graphical user '
                    'interfaces have been developed for all desktop operating '
                    'systems in use today. FTP is also often used as an '
                    'application component to automatically transfer files for '
                    'program internal functions. FTP can be used with '
                    'user-based password a While data is being transferred via '
                    'the data stream, the control stream sits idle. This can '
                    'cause problems with large data transfers through '
                    'firewalls which time out sessions after lengthy periods '
                    'of idleness. While the file may well be successfully '
                    'transferred, the control session can be disconnected by '
                    'the firewall, causing an error to be generated.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'File_Transfer_Protocol'), )
    }),
)
