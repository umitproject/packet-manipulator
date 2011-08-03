#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Adriano Monteiro Marques
#
# Author: Francesco Piccinno <stack.box@gmail.com>
# Author: Guilherme Rezende <guilhermebr@gmail.com>
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
SIP UserEnumeration (Active audit)
"""
import gtk
import gobject
import random

from time import sleep
from threading import Thread

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.atoms import generate_traceback
from umit.pm.core.auditutils import is_ip, random_ip, AuditOperation
from umit.pm.core.const import STATUS_ERR, STATUS_WARNING, STATUS_INFO

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.plugins.core import Core
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *

from umit.pm.backend import MetaPacket

AUDIT_NAME = 'sip-userenum'
AUDIT_MSG = '<tt><b>' + AUDIT_NAME + ':</b> %s</tt>'

def on_response(sippack_dict):
    print sippack_dict

def create_sip_btn():
    utils = Core().get_need(None, 'SipGuiUtils')
    inputs = ('type of message', 'user agent')
    btn = gtk.Button()
    btn.connect('clicked', utils.create_sip_window, inputs, on_response)
    return btn

class SipEnumeration(Plugin, ActiveAudit):
    __inputs__ = (('Sip Pack', (create_sip_btn, "SIP packet")),)


    def start(self, reader):
        a, self.item = self.add_menu_entry('SipEnumeration', 'Sip Enumeration...',
                                           _('A SIP Enumeration'),
                                           gtk.STOCK_EXECUTE)

    def stop(self):
        self.remove_menu_entry(self.item)


    def execute_audit(self, sess, inp_dict):
        target_ip = inp_dict['target ip']
        remote_port = inp_dict['remote port']
        source_port = inp_dict['source port']
        type_of_msg = inp_dict['type of message']
        user_agent = inp_dict['user agent']
        delay = inp_dict['delay']
        source_ip = sess.context.get_ip1()

        resolve = lambda x: is_ip(x) and x or '0.0.0.0'

        targets = target_ip.split(',')
        target_ip = []

        for dip in targets:
            dstip = resolve(dip)
            if dstip == '0.0.0.0':
                sess.output_page.user_msg(_('IP %s not valid') % (dip) ,
                                          STATUS_ERR, AUDIT_NAME)
                pass
            else:
                target_ip.append(dstip)

        if len(target_ip) == 0:
            return False

        return SipPortscanOperation(
            sess, target_ip, remote_port, source_port, type_of_msg, user_agent, delay, source_ip
        )

__plugins__ = [SipEnumeration]
__plugins_deps__ = [('SipEnumeration', ['SipGuiUtils'], ['SipEnumeration-0.1'], [])]

__audit_type__ = 1
__protocols__ = (('udp', 5060), ('udp', 5061), ('sip', None))
__vulnerabilities__ = (('SIP Enumeration', {
    'description' : 'SIP Enumeration plugin'
    'The Session Initiation Protocol (SIP) is an IETF-defined signaling protocol,'
    'widely used for controlling multimedia communication sessions'
    'such as voice and video calls over'
    'Internet Protocol (IP). The protocol can be used for creating,'
    'modifying and terminating two-party (unicast) or multiparty (multicast)'
    'sessions consisting of one or several media streams.'
    'The modification can involve changing addresses or ports, inviting more'
    'participants, and adding or deleting media streams. Other feasible'
    'application examples include video conferencing, streaming multimedia distribution,'
    'instant messaging, presence information, file transfer and online games.'
    'SIP was originally designed by Henning Schulzrinne and Mark Handley starting in 1996.'
    'The latest version of the specification is RFC 3261 from the IETF Network Working'
    'Group. In November 2000, SIP was accepted as a 3GPP signaling protocol and permanent'
    'element of the IP Multimedia Subsystem (IMS) architecture for IP-based streaming'
    'multimedia services in cellular systems.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                     'Session_Initiation_Protocol'), )
    }),
)