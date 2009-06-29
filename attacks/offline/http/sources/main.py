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
HTTP protocol dissector (Offline attack)
"""

from PM.Core.Logger import log
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import *
from PM.Manager.SessionManager import SessionManager

HTTP_NAME = 'dissector.http'
HTTP_PORTS = (80, 8080)
HTTP_TRAILER = '\r\n\r\n'

def http_dissector():
    conf = AttackManager().get_configuration('dissector.http')
    reassemble = conf['reassemble']

    sessions = SessionManager()

    def http(mpkt):
        if mpkt.get_field('tcp.dport') not in HTTP_PORTS:
            return None

        payload = mpkt.get_field('raw.load')

        if not payload:
            return None

        if mpkt.get_field('tcp.dport') in HTTP_PORTS:
            # Client side

            idx = payload.find(HTTP_TRAILER)

            if idx >= 0:
                header_part = payload[:idx]
                body_part = payload[idx + 4:]

                headers = {}

                for line in header_part.splitlines():
                    if not line:
                        break

                    key, value = line.split(' ', 1)

                    if key[-1] == ':':
                        headers[key[:-1].lower()] = value
                    else:
                        headers[key.lower()] = value.rsplit(' ', 1)

                if 'user-agent' in headers:
                    mpkt.set_cfield(HTTP_NAME + '.browser',
                                    headers['user-agent'])

                if 'accept-language' in headers:
                    mpkt.set_cfield(HTTP_NAME + '.language',
                                    headers['accept-language'])

                if 'content-length' in headers:
                    try:
                        req_len = int(headers['content-length'])

                        if req_len < len(body_part):
                            return NEED_FRAGMENT

                    except ValueError:
                        pass
        else:
            # Server side
            pass

        return None

    return http

class HTTPDissector(Plugin, OfflineAttack):
    def register_options(self):
        conf = AttackManager().register_configuration('dissector.http')
        conf.register_option('reassemble', True, bool)
        conf.register_option('extract_files', True, bool)

    def register_decoders(self):
        AttackManager().add_dissector(APP_LAYER_TCP, 80, http_dissector())

__plugins__ = [HTTPDissector]