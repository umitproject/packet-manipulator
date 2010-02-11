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
PPP protocol decoder
"""

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.core.netconst import *

def ppp_decoder(mpkt):
    mpkt.l2_proto = IL_TYPE_PPP
    mpkt.l2_len = 4
    mpkt.l3_proto = LL_TYPE_IP

    if mpkt.get_fields('hdlc', ('address', 'control')) != [255, 3] or \
       mpkt.get_field('ppp.proto', 0) != 33:
        return

    return NET_LAYER, LL_TYPE_IP

class PPPDecoder(Plugin, PassiveAudit):
    def stop(self):
        AuditManager().remove_decoder(LINK_LAYER, IL_TYPE_PPP, ppp_decoder)

    def register_decoders(self):
        AuditManager().add_decoder(LINK_LAYER, IL_TYPE_PPP, ppp_decoder)

__plugins__ = [PPPDecoder]
__plugins_deps__ = [('PPPDecoder', [], ['=PPPDecoder-1.0'], [])]

__audit_type__ = 0
__protocols__ = (('ppp', None), )
__vulnerabilities__ = (('PPP decoder', {
    'description' : 'Point-to-Point Protocol, or PPP, is a data link '
                    'protocol commonly used to establish a direct connection '
                    'between two networking nodes. It can provide connection '
                    'authentication, transmission encryption privacy, and '
                    'compression.\n'
                    'PPP is used over many types of physical networks '
                    'including serial cable, phone line, trunk line, '
                    'cellular telephone, specialized radio links, and fiber '
                    'optic links such as SONET. Most Internet service '
                    'providers (ISPs) use PPP for customer dial-up access to '
                    'the Internet.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                           'Point-to-Point_Protocol'), )
    }),
)
