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

from threading import Thread
from struct import pack, unpack
from socket import gethostbyname, inet_aton, inet_ntoa

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.auditutils import is_ip, is_mac
from umit.pm.core.const import STATUS_ERR, STATUS_WARNING, STATUS_INFO

from umit.pm.gui.core.app import PMApp
from umit.pm.higwidgets.higdialogs import HIGAlertDialog

from umit.pm.manager.auditmanager import *

from umit.pm.backend import MetaPacket

AUDIT_NAME = 'arp-ping'
AUDIT_MSG = '<tt><b>' + AUDIT_NAME + ':</b> %s</tt>'

class ARPScanOperation(AuditOperation):
    def __init__(self, sess, iface, ip, netmask):
        AuditOperation.__init__(self)

        self.sess = sess

        self.iface = iface
        self.ip = ip
        self.netmask = netmask

        self.internal = True
        self.thread = None

        self.percentage = 0
        self.summary = AUDIT_MSG % _('idle')

    def start(self):
        if self.state == self.RUNNING or self.thread:
            return False

        self.internal = True
        self.percentage = 0
        self.summary = AUDIT_MSG % _('Scanning for hosts ...')

        self.thread = Thread(target=self.__ping_thread, name='ARPING')
        self.thread.setDaemon(True)
        self.thread.start()

        self.sess.output_page.user_msg(
            _('Scanning for hosts on iface %s with IP: %s and Netmask: %s') \
            % (self.iface, self.ip, self.netmask), STATUS_INFO, AUDIT_NAME)

        return True

    def stop(self):
        if self.state == self.NOT_RUNNING or not self.thread:
            return False

        self.internal = False
        self.summary = AUDIT_MSG % _('stopping')

        return True

    def __ping_thread(self):
        # TODO: maybe will be better to use IPy or something
        #       like that to handle also IPv6

        ip = unpack('!I', inet_aton(self.ip))[0]
        nm = unpack('!I', inet_aton(self.netmask))[0]
        last = unpack('!I', '\xff\xff\xff\xff')[0]

        start = ip & nm
        end = (last ^ nm) | ip

        sent = 0
        totals = float(end - start)

        # NB: With this method we ping also broadcast and reserved
        # addresses

        pkt = MetaPacket.new('eth') / MetaPacket.new('arp')
        pkt.set_field('eth.src', self.sess.context.get_mac1())
        pkt.set_field('eth.dst', 'ff:ff:ff:ff:ff:ff')
        pkt.set_field('arp.hwsrc', self.sess.context.get_mac1())
        pkt.set_field('arp.hwdst', '00:00:00:00:00:00')
        pkt.set_field('arp.psrc', self.sess.context.get_ip1())

        while self.internal and start <= end:
            pkt.set_field('arp.pdst', inet_ntoa(pack('!I', start)))
            self.sess.context.si_l2(pkt)
            time.sleep(0.01)
            self.percentage = (sent / totals) * 100.0
            start += 1
            sent += 1

        if not self.internal:
            self.summary = AUDIT_MSG % _('stopped')
            self.sess.output_page.user_msg(
                _('Scanning for hosts on iface %s with IP: %s and Netmask: %s stopped') \
                % (self.iface, self.ip, self.netmask), STATUS_WARNING, AUDIT_NAME)
        else:
            self.summary = AUDIT_MSG % _('finished')
            self.sess.output_page.user_msg(
                _('Scanning for hosts on iface %s with IP: %s and Netmask: %s finished') \
                % (self.iface, self.ip, self.netmask), STATUS_INFO, AUDIT_NAME)

        self.internal = False
        self.state = self.NOT_RUNNING
        self.percentage = 100.0

class ARPPingOperation(AuditOperation):
    has_stop = True
    has_start = True

    def __init__(self, sess, ip, delay, probes, report):
        AuditOperation.__init__(self)

        self.session = sess

        self.pkt = MetaPacket.new('arp')
        self.pkt.set_field('arp.pdst', ip)

        self.delay = delay
        self.probes = probes
        self.report = report
        self.packets = 0
        self.times = []

        self.sender = None

    def start(self):
        if self.state == self.RUNNING or self.sender:
            return False

        self.packets = 0
        self.times = []
        self.state = self.RUNNING
        self.sender = self.session.context.sr_l3(
            self.pkt, timeout=4,
            delay=self.delay, repeat=self.probes,
            onerror=self.on_error,
            onreply=self.on_resolved,
            oncomplete=self.on_complete,
            onsend=self.on_send)

        return True

    def stop(self):
        if self.state == self.NOT_RUNNING or not self.sender:
            return False

        self.session.context.cancel_send(self.sender)

    def on_complete(self, send, udata):
        if self.probes > 0:
            self.summary = AUDIT_MSG % (_('Finished with %d of %d sent') % \
                                        (self.packets, self.probes))
        else:
            self.summary = AUDIT_MSG % (_('Finished with %d sent') % \
                                        self.packets)

        self.percentage = 100.0

        self.sender = None
        self.state = self.NOT_RUNNING

    def on_send(self, send, mpkt, udata):
        self.times.append(mpkt.get_rawtime())

    def on_resolved(self, send, mpkt, reply, udata):
        if self.report:
            diff = None
            now = time.time()

            while self.times:
                tm = self.times.pop(0)
                diff = now - tm
                diff *= 100.0

                if diff > 0 and diff < self.delay:
                    break
                else:
                    diff = None # Too fast :)

            if diff is not None:
                self.session.output_page.user_msg(
                    _('Reply from %s [%s] %.2fms') % \
                    (reply.get_field('arp.pdst'),
                     reply.get_field('arp.hwsrc'),
                     diff), STATUS_INFO, AUDIT_NAME
                )

        self.packets += 1

        if self.probes > 0:
            self.percentage = (self.packets / float(self.probes)) * 100.0
            self.summary = AUDIT_MSG % _('%d of %d sent') % (self.packets, self.probes)
        else:
            self.summary = AUDIT_MSG % _('%d sent' % self.packets)
            self.percentage = (self.percentage + 536870911) % \
                              gobject.G_MAXINT

    def on_error(self, send, status, udata):
        if self.report:
            self.session.output_page.user_msg(
                _('Unable to resolve %s (Errno: %d)') \
                % (send.mpkts[0].get_field('arp.pdst'), status),
                STATUS_WARNING, AUDIT_NAME)

        self.state = self.NOT_RUNNING
        self.sender = None
        self.percentage = 100.0

class ARPScan(ActiveAudit):
    def start(self, reader):
        a, self.item = self.add_menu_entry('ARPScan', 'Scan for hosts...',
                                           _('Scan for hosts using ARP ping'),
                                           gtk.STOCK_FIND)

    def stop(self):
        self.remove_menu_entry(self.item)

    def execute_audit(self, sess, inp_dict):
        if not self.ping_scan(sess,
                              sess.context.get_iface1(),
                              sess.context.get_ip1(),
                              sess.context.get_netmask1()):
            sess.output_page.user_msg(_('Could not perform an ARP scan.'),
                                     STATUS_ERR, AUDIT_NAME)
        else:
            self.ping_scan(sess,
                           sess.context.get_iface2(),
                           sess.context.get_ip2(),
                           sess.context.get_netmask2())

    def ping_scan(self, sess, iface, ip, netmask):
        if not iface or not ip or not netmask:
            return False

        sess.audit_page.tree.append_operation(
            ARPScanOperation(sess, iface, ip, netmask)
        )

        return True

class ARPPing(ActiveAudit):
    __inputs__ = (
        ('target', ('0.0.0.0', _('IP address or hostname of the target.'))),
        ('probes', (1, _('Number of packets to send. -1 for infinite'))),
        ('delay', (300, _('Delay in msec between sends'))),
        ('report', (True, _('Print a message in the StatusTab')))
    )

    def start(self, reader):
        a, self.item = self.add_menu_entry('ARPPing', 'ARP ping ...',
                                           _('Ping a target using ARP request'),
                                           gtk.STOCK_EXECUTE)

    def stop(self):
        self.remove_menu_entry(self.item)

    def execute_audit(self, sess, inp_dict):
        target = inp_dict['target']
        probes = inp_dict['probes']

        if probes < 1 and probes != -1:
            sess.output_page.user_msg(_('Probes could be -1 or > 0'), STATUS_ERR,
                                     AUDIT_NAME)
            return False

        if is_ip(target):
            ip = target
        else:
            ip = gethostbyname(target)
            sess.output_page.user_msg(_('Hostname %s solved as %s') \
                                      % (target, ip), STATUS_INFO, AUDIT_NAME)
        if ip == '0.0.0.0':
            sess.output_page.user_msg(_('Not a valid target'), STATUS_ERR,
                                     AUDIT_NAME)
            return False

        return ARPPingOperation(sess, ip, max(inp_dict['delay'], 0),
                                probes, inp_dict['report'])

__plugins__ = [ARPPing, ARPScan]
__plugins_deps__ = []

__audit_type__ = 1
__protocols__ = (('arp', None), )

