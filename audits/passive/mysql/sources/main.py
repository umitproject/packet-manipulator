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
MySQL protocol dissector (Passive audit)

>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip,tcp,mysql', 'mysql.pcap')
decoder.tcp.notice Invalid TCP packet from 10.10.3.60 to 10.10.3.109 : wrong checksum 0x1b1b instead of 0xb328
dissector.mysql.info MYSQL : 10.10.3.60:3306 -> USER: admin HASH: 5f28eeab88bfc739938db314591ff3f9501e8cd5:2e7d4e4f7e4f5126685a6c30465247503a6e4032
decoder.tcp.notice Invalid TCP packet from 10.10.3.60 to 10.10.3.109 : wrong checksum 0x1ae8 instead of 0x56c6
decoder.tcp.notice Invalid TCP packet from 10.10.3.60 to 10.10.3.109 : wrong checksum 0x1aee instead of 0x4eaa
decoder.tcp.notice Invalid TCP packet from 10.10.3.60 to 10.10.3.109 : wrong checksum 0x1b4f instead of 0x9f92
decoder.tcp.notice Invalid TCP packet from 10.10.3.60 to 10.10.3.109 : wrong checksum 0x1b2d instead of 0x3011
decoder.tcp.notice Invalid TCP packet from 10.10.3.60 to 10.10.3.109 : wrong checksum 0x1b9b instead of 0xe53e
decoder.tcp.notice Invalid TCP packet from 10.10.3.60 to 10.10.3.109 : wrong checksum 0x1b19 instead of 0x6374
decoder.tcp.notice Invalid TCP packet from 10.10.3.60 to 10.10.3.109 : wrong checksum 0x1ba6 instead of 0xddd0
"""

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager

MYSQL_NAME = 'dissector.mysql'
MYSQL_PORTS = (3306, )

def mysql_dissector():
    manager = AuditManager()
    sessions = SessionManager()

    def mysql(mpkt):
        if not mpkt.data:
            return

        if mpkt.l4_src in MYSQL_PORTS:
            # Packets from server
            sess = sessions.lookup_session(mpkt, MYSQL_PORTS, MYSQL_NAME)

            if not sess:
                if len(mpkt.data) < 6 or mpkt.data[5] not in ('3', '4', '5', '6'):
                    return

                payload = mpkt.data[5:]
                end = payload.find('\x00')

                version = payload[:end]
                mpkt.set_cfield('banner', version)

                payload = payload[end + 4 + 1:] # Skip thread ID

                end = payload.find('\x00')
                salt = payload[:end]

                # Skip capabilities, charset, status and zero padding
                payload = payload[end + 2 + 1 + 2 + 13 + 1:]

                end = payload.find('\x00')
                salt += payload[:end]

                sess = sessions.lookup_session(mpkt, MYSQL_PORTS, MYSQL_NAME, True)
                sess.data = salt
        else:
            # Packets from client
            sess = sessions.lookup_session(mpkt, MYSQL_PORTS, MYSQL_NAME)

            if sess:
                convert = lambda x: "".join(
                    [hex(ord(c))[2:].zfill(2) for c in x]
                )

                payload = mpkt.data[36:]
                end = payload.find('\x00')

                username = payload[:end]

                password_len = ord(payload[end + 1])
                payload = payload[end + 2:]

                password = payload[:password_len]

                if not password:
                    password = '(no password)'
                else:
                    password = convert(password)

                password += ':' + convert(sess.data)

                mpkt.set_cfield('username', username)
                mpkt.set_cfield('password', password)

                manager.user_msg('MYSQL : %s:%d -> USER: %s HASH: %s' % \
                                 (mpkt.l3_dst, mpkt.l4_dst,
                                  username, password),
                                 6, MYSQL_NAME)

                sessions.delete_session(sess)

    return mysql

class MySQLDissector(Plugin, PassiveAudit):
    def start(self, reader):
        self.dissector = mysql_dissector()

    def register_decoders(self):
        for port in MYSQL_PORTS:
            AuditManager().add_dissector(APP_LAYER_TCP, port, self.dissector)

    def stop(self):
        for port in MYSQL_PORTS:
            AuditManager().remove_dissector(APP_LAYER_TCP, port, self.dissector)

__plugins__ = [MySQLDissector]
__plugins_deps__ = [('MySQLDissector', ['TCPDecoder'], ['MySQLDissector-1.0'], []),]

__audit_type__ = 0
__protocols__ = (('tcp', 3306), ('mysql', None))
__vulnerabilities__ = (('MySQL dissector', {
    'description' : 'MySQL is a relational database management system (RDBMS)'
                    ' that runs as a server providing multi-user access to a '
                    'number of databases.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/MySQL'), )
    }),
)
