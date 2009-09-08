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
from PM.Core.AttackUtils import is_ip, is_mac

from PM.Gui.Core.App import PMApp
from PM.Gui.Plugins.Core import Core
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import *

from PM.Backend import MetaPacket

class ARPPing(Plugin, OnlineAttack):
    __inputs__ = (
        ('target', ('0.0.0.0', _('IP address or hostname of the target.'))),
        ('probes', (1, _('Number of packets to send. -1 for infinite'))),
        ('delay', (300, _('Delay in msec between sends'))),
        ('report', (True, _('Print a message in the StatusTab')))
    )

    def start(self, reader):
        self.status = PMApp().main_window.get_tab('StatusTab').status

        a, self.item = self.add_menu_entry('ARPPing', 'ARP ping ...',
                                           _('Ping a target using ARP request'),
                                           gtk.STOCK_EXECUTE)

    def stop(self):
        self.remove_menu_entry(self.item)

    def on_resolved(self, send, mpkt, reply, udata):
        if udata:
            el = time.time() - reply.get_cfield('arpping.time')

            print el
            el *= 100.0

            self.status.info(_('Reply from %s [%s] %.2fms') \
                             % (reply.get_field('arp.pdst'),
                                reply.get_field('arp.hwsrc'),
                                el))

            reply.set_cfield('arpping.time', time.time())

    def on_error(self, send, status, udata):
        if udata:
            self.status.warning(_('Unable to resolve %s (Errno: %d)') \
                                % (send.mpkts[0].get_field('arp.pdst'), status))

    def execute_attack(self, sess, inp_dict):
        target = inp_dict['target']

        if is_ip(target):
            ip = target
        else:
            ip = gethostbyname(target)
            log.debug('%s is %s' % (target, ip))

        pkt = MetaPacket.new('arp')
        pkt.set_field('arp.pdst', ip)
        pkt.set_cfield('arpping.time', time.time())

        if ip == '0.0.0.0':
            return False

        sess.context.sr_l3(pkt, timeout=4,
                           delay=inp_dict['delay'], repeat=inp_dict['probes'],
                           onerror=self.on_error,
                           onreply=self.on_resolved, udata=inp_dict['report'])

        return True

__plugins__ = [ARPPing]
__plugins_deps__ = []

__attack_type__ = 1
__protocols__ = (('arp', None), )

