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
VNC protocol dissector (Passive audit)

>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip,tcp,vnc -sdecoder.tcp.checksum_check=0', 'vnc-session.pcap')
dissector.vnc.info VNC : 172.27.17.2:5900 -> 985878519f9f7ecd7fb97aedaa912b10:ad909a41fb0309fec3772f2860d946c3
"""

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager

WAIT_AUTH      = 1
WAIT_CHALLENGE = 2
WAIT_RESPONSE  = 3
WAIT_RESULT    = 4
NO_AUTH        = 5
LOGIN_OK       = 6
LOGIN_FAILED   = 7
LOGIN_TOOMANY  = 8

RFB_3 = 0
RFB_7 = 1
RFB_8 = 2

class VNCStatus(object):
    def __init__(self, version):
        self.status = WAIT_AUTH
        self.challenge = ''
        self.response = ''
        self.version = version

        if version == RFB_7 or version == RFB_8:
            self.status = WAIT_CHALLENGE

def vnc_dissector():
    VNC_NAME = 'dissector.vnc'
    VNC_PORTS = (5900, 5901, 5902, 5903)

    manager = AuditManager()
    sessions = SessionManager()

    def vnc(mpkt):
        if mpkt.l4_src in VNC_PORTS:
            # Packets from the server
            sess = sessions.lookup_session(mpkt, VNC_PORTS, VNC_NAME)

            if not sess:
                if mpkt.data and mpkt.data.startswith("RFB "):
                    version = mpkt.data.strip()

                    if version.endswith('003.003'):
                        ver = RFB_3
                    elif version.endswith('003.007'):
                        ver = RFB_7
                    elif version.endswith('003.008'):
                        ver = RFB_8
                    else:
                        log.debug('No supported RFB protocol version %s' % version)
                        return

                    mpkt.set_cfield('banner', version)

                    newsess = sessions.lookup_session(mpkt, VNC_PORTS, VNC_NAME, True)
                    newsess.data = VNCStatus(ver)
            else:
                conn_status = sess.data

                if conn_status.status == WAIT_AUTH and mpkt.data:
                    if mpkt.data.startswith("\x00\x00\x00\x01"):
                        conn_status.status = NO_AUTH
                    elif mpkt.data.startswith("\x00\x00\x00\x00"):
                        sessions.delete_session(sess)
                    elif mpkt.data.startswith("\x00\x00\x00\x02"):
                        conn_status.status = WAIT_CHALLENGE


                if conn_status.status == WAIT_CHALLENGE and len(mpkt.data) == 16:
                    conn_status.status = WAIT_RESPONSE
                    conn_status.challenge = mpkt.data
                elif conn_status.status == WAIT_RESULT and mpkt.data:
                    if mpkt.data.startswith("\x00\x00\x00\x00"):
                        conn_status.status = LOGIN_OK
                    elif mpkt.data.startswith("\x00\x00\x00\x01"):
                        conn_status.status = LOGIN_FAILED
                    elif mpkt.data.startswith("\x00\x00\x00\x02"):
                        conn_stauts.status = LOGIN_TOOMANY
        else:
            # Packets from the client
            sess = sessions.lookup_session(mpkt, VNC_PORTS, VNC_NAME)

            if sess:
                conn_status = sess.data

                if conn_status.status == NO_AUTH:
                    mpkt.set_cfield('username', 'vnc')
                    mpkt.set_cfield('password', 'No password')

                    manager.user_msg('VNC : %s:%d -> No authentication' % \
                                     (mpkt.l3_dst, mpkt.l4_dst),
                                     6, VNC_NAME)
                    sessions.delete_session(sess)

                elif conn_status.status >= LOGIN_OK:
                    convert = lambda x:"".join([hex(ord(c))[2:].zfill(2) for c in x])

                    password = convert(conn_status.challenge) + ':' + \
                               convert(conn_status.response)

                    if conn_status.status > LOGIN_OK:
                        manager.user_msg('VNC : %s:%d -> %s (failed)' % \
                                         (mpkt.l3_dst, mpkt.l4_dst, password),
                                         6, VNC_NAME)
                    else:
                        manager.user_msg('VNC : %s:%d -> %s' % \
                                         (mpkt.l3_dst, mpkt.l4_dst, password),
                                         6, VNC_NAME)

                        mpkt.set_cfield('username', 'vnc')
                        mpkt.set_cfield('password', password)

                    sessions.delete_session(sess)
                elif conn_status.status == WAIT_RESPONSE and len(mpkt.data) >= 16:
                    conn_status.status = WAIT_RESULT
                    conn_status.response = mpkt.data[:16]

    return vnc

class VNCDissector(Plugin, PassiveAudit):
    def start(self, reader):
        self.dissector = vnc_dissector()

    def register_decoders(self):
        for port in xrange(5900, 5904):
            AuditManager().add_dissector(APP_LAYER_TCP, port, self.dissector)

    def stop(self):
        for port in xrange(5900, 5904):
            AuditManager().remove_dissector(APP_LAYER_TCP, port, self.dissector)

__plugins__ = [VNCDissector]
__plugins_deps__ = [('VNCDissector', ['TCPDecoder'], ['VNCDissector-1.0'], []),]

__audit_type__ = 0
__protocols__ = (('tcp', 5900), ('tcp', 5901),
                 ('tcp', 5902), ('tcp', 5903), ('vnc', None))
__vulnerabilities__ = (('VNC dissector', {
    'description' : 'Virtual Network Computing (VNC) is a graphical desktop '
                    'sharing system that uses the RFB protocol to remotely '
                    'control another computer. It transmits the keyboard and '
                    'mouse events from one computer to another, relaying the '
                    'graphical screen updates back in the other direction, '
                    'over a network.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'Virtual_Network_Computing'), )
    }),
)
