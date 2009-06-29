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
A traffic profiler and collector module.

>>> from PM.Core.AttackUtils import attack_unittest
>>> attack_unittest('-f ethernet,ip,tcp,ftp,profiler', 'ftp-login.pcap')
MAC: 06:05:04:03:02:01 (UNKNW) IP: 127.0.0.1 1 service(s) (0 accounts for port 21)
dissector.ftp.info FTP : 127.0.0.1:21 -> USER: anonymous PASS: guest@example.com
MAC: 06:05:04:03:02:01 (UNKNW) IP: 127.0.0.1 1 service(s) (1 accounts for port 21)

>>> attack_unittest('-f ethernet,ip,tcp,ftp,fingerprint,profiler', 'ftp-login.pcap')
fingerprint.notice 127.0.0.1 is running Novell NetWare 3.12 - 5.00 (nearest)
MAC: 01:02:03:04:05:06 (UNKNW) IP: 127.0.0.1 OS: Novell NetWare 3.12 - 5.00 (nearest)
fingerprint.notice 127.0.0.1 is running Novell NetWare 3.12 - 5.00 (nearest)
MAC: 06:05:04:03:02:01 (UNKNW) IP: 127.0.0.1 OS: Novell NetWare 3.12 - 5.00 (nearest) 1 service(s) (0 accounts for port 21)
dissector.ftp.info FTP : 127.0.0.1:21 -> USER: anonymous PASS: guest@example.com
MAC: 06:05:04:03:02:01 (UNKNW) IP: 127.0.0.1 1 service(s) (1 accounts for port 21)
"""

import os.path

from PM.Core.I18N import _
from PM.Core.Atoms import defaultdict
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import *

UNKNOWN_TYPE       = 0
HOST_LOCAL_TYPE    = 1
HOST_NONLOCAL_TYPE = 2
GATEWAY_TYPE       = 3
ROUTER_TYPE        = 4

class Account(object):
    def __init__(self):
        self.username = None
        self.passwrod = None
        self.info = None
        self.failed = None
        self.ip_addr = None

class Port(object):
    def __init__(self):
        self.proto = None
        self.port = None
        self.banner = None
        self.accounts = []

    def get_account(self, user, pwd):
        for a in self.accounts:
            if a.username == user and a.password == pwd:
                return a

        a = Account()
        self.accounts.append(a)
        return a

class Profile(object):
    def __init__(self):
        self.l2_addr = None
        self.l3_addr = None
        self.hostname = None
        self.distance = None
        self.ports = []
        self.type = None
        self.fingerprint = None
        self.vendor = None

    def get_port(self, proto, port):
        for p in self.ports:
            if p.proto == proto and p.port == port:
                return p

        p = Port()
        p.port = port
        p.proto = proto
        self.ports.append(p)
        return p

    def __repr__(self):
        s = ''

        if self.l2_addr:
            s += "MAC: %s " % self.l2_addr
        if self.vendor:
            s += "(%s) " % self.vendor
        if self.l3_addr:
            s += "IP: %s " % self.l3_addr
        if self.distance:
            s += "%d hop(s) " % self.distance
        if self.fingerprint:
            s += "OS: %s " % self.fingerprint
        if self.ports:
            s += "%d service(s) " % len(self.ports)

            for p in self.ports:
                s += "(%d accounts for port %d) " % (len(p.accounts), p.port)

        return s[:-1]

class Profiler(Plugin, OfflineAttack):
    def start(self, reader):
        # We sae profile with l3_addr as key (IP address)
        # and the overflowed items as a list. So we use a defaultdict
        self.profiles = defaultdict(list)

        conf = AttackManager().get_configuration('offline.profiler')

        if conf['mac_fingerprint']:
            if reader:
                contents = reader.file.read('data/finger.mac.db')
            else:
                contents = open(os.path.join('offline', 'profiler', 'data',
                                             'finger.mac.db'), 'r').read()

            self.macdb = {}

            for line in contents.splitlines():
                if not line or line[0] == '#':
                    continue

                try:
                    mac_pref, vendor = line.split(' ', 1)
                    self.macdb[mac_pref] = vendor
                except:
                    continue

            log.info('Loaded %d MAC fingerprints.' % len(self.macdb))
        else:
            self.macdb = None

    def register_options(self):
        conf = AttackManager().register_configuration('offline.profiler')
        conf.register_option('mac_fingerprint', True, bool)

    def register_hooks(self):
        manager = AttackManager()

        manager.add_decoder_hook(PROTO_LAYER, NL_TYPE_TCP,
                                 self._parse_tcp, 1)

        manager.add_decoder_hook(NET_LAYER, LL_TYPE_ARP,
                                 self._parse_arp, 1)

        manager.add_decoder_hook(PROTO_LAYER, NL_TYPE_ICMP,
                                 self._parse_icmp, 1)

    def _parse_tcp(self, mpkt):
        sport = mpkt.get_field('tcp.sport')
        dport = mpkt.get_field('tcp.dport')
        tcpflags = mpkt.get_field('tcp.flags')

        if not tcpflags:
            return

        prof = None
        port = None

        # Simple open port

        if (tcpflags & TH_SYN and tcpflags & TH_ACK):
            prof = self.get_or_create(mpkt)
            port = prof.get_port(APP_LAYER_TCP, sport)

        # Dissector exposed banner

        banner = mpkt.cfields.get('banner', None)

        if banner:
            if not prof:
                prof = self.get_or_create(mpkt)
                port = prof.get_port(APP_LAYER_TCP, sport)

            port.banner = banner

        # Fingerprint of fingerprint plugin

        fingerprint = mpkt.cfields.get('remote_os', None)

        if fingerprint:
            if not prof:
                prof = self.get_or_create(mpkt)

            prof.fingerprint = fingerprint

        # Username or password exposed by a dissector

        username = mpkt.cfields.get('username', None)
        password = mpkt.cfields.get('password', None)

        if username or password:
            if not prof:
                prof = self.get_or_create(mpkt, True)
                port = prof.get_port(APP_LAYER_TCP, dport)

            account = port.get_account(username, password)
            account.username = username
            account.passwrod = password

        if prof:
            print prof

    def _parse_arp(self, mpkt):
        prof = self.get_or_create(mpkt)
        prof.type = HOST_LOCAL_TYPE
        prof.distance = 1 # we are in LAN so distance is 1

        # TODO: we have to check the interface ip with the ip of mpkt
        # and if equal set distance to 0

    def _parse_icmp(self, mpkt):
        prof = self.get_or_create(mpkt)

        icmp_type = mpkt.get_field('icmp.type')

        if icmp_type == ICMP_TYPE_DEST_UNREACH:
            icmp_code = mpkt.get_field('icmp.code')

            if icmp_code == ICMP_CODE_HOST_UNREACH or \
               icmp_code == ICMP_CODE_NET_UNREACH:

                prof.type = ROUTER_TYPE

        elif icmp_type == ICMP_TYPE_REDIRECT or \
             icmp_type == ICMP_TYPE_TIME_EXCEEDED:

            prof.type = ROUTER_TYPE

    def get_or_create(self, mpkt, clientside=False):
        if not clientside:
            ip = mpkt.get_field('ip.src')
            mac = mpkt.get_field('eth.src')
        else:
            ip = mpkt.get_field('ip.dst')
            mac = mpkt.get_field('eth.dst')

        for prof in self.profiles[ip]:
            if not mac:
                return prof
            elif prof.l2_addr == mac:
                return prof
        else:
            prof = Profile()
            prof.l2_addr = mac
            prof.l3_addr = ip

            if self.macdb:
                prof.vendor = self.macdb.get(mac[:8].replace(':', '').upper(),
                                             _('UNKNW'))

            log.info('Adding a new profile -> %s' % prof)

            return prof

__plugins__ = [Profiler]
__plugins_deps__ = [('Profiler', [], ['=Profiler-1.0'], [])]