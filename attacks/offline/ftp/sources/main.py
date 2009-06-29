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
FTP protocol dissector (Offline attack)

>>> from PM.Core.AttackUtils import attack_unittest
>>> attack_unittest('-f ethernet,ip,tcp,ftp', 'ftp-login.pcap')
dissector.ftp.info FTP : 127.0.0.1:21 -> USER: anonymous PASS: guest@example.com
"""

from PM.Core.Logger import log
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import *
from PM.Manager.SessionManager import SessionManager


def ftp_dissector():
    FTP_NAME = 'dissector.ftp'
    FTP_PORTS = (21, )

    manager = AttackManager()
    sessions = SessionManager()

    def ftp(mpkt):
        sess = sessions.create_session(mpkt, FTP_PORTS, FTP_NAME)

        # This is a SYN/ACK packet.
        if sess:
            return None

        sess = sessions.is_first_mpkt_from_server(mpkt, FTP_PORTS, FTP_NAME)

        if sess:
            if not sess.data:
                payload = mpkt.get_field('raw.load')

                # Ok we have an FTP banner over here
                if payload and payload.startswith('220'):
                    banner = payload[4:].strip()
                    mpkt.set_cfield('banner', banner)

                    manager.user_msg('FTP : %s:%d banner: %s' % \
                                     (mpkt.get_field('ip.src'),
                                      mpkt.get_field('tcp.sport'),
                                      banner),
                                      6, 'dissector.ftp')

            if not sess.data:
                sessions.delete_session(sess)
                return None

        if mpkt.get_field('tcp.dport') not in FTP_PORTS:
            return None

        payload = mpkt.get_field('raw.load')

        if not payload:
            return None

        payload = payload.strip()

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
                             (mpkt.get_field('ip.dst'),
                              mpkt.get_field('tcp.dport'),
                              sess.data[0] or '',
                              sess.data[1] or ''),
                              6, 'dissector.ftp')

            mpkt.set_cfield('username', sess.data[0])
            mpkt.set_cfield('password', sess.data[1])

            sessions.delete_session(sess)

    return ftp

class FTPDissector(Plugin, OfflineAttack):
    def register_decoders(self):
        AttackManager().add_dissector(APP_LAYER_TCP, 21, ftp_dissector())

__plugins__ = [FTPDissector]