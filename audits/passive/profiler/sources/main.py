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

>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip,tcp,ftp,profiler', 'ftp-login.pcap')
MAC: 06:05:04:03:02:01 (UNKNW) IP: 127.0.0.1 1 service(s) (0 accounts for port 21)
dissector.ftp.info FTP : 127.0.0.1:21 -> USER: anonymous PASS: guest@example.com
MAC: 06:05:04:03:02:01 (UNKNW) IP: 127.0.0.1 1 service(s) (1 accounts for port 21)

>>> audit_unittest('-f ethernet,ip,tcp,ftp,fingerprint,profiler', 'ftp-login.pcap')
fingerprint.notice 127.0.0.1 is running Novell NetWare 3.12 - 5.00 (nearest)
MAC: 01:02:03:04:05:06 (UNKNW) IP: 127.0.0.1 OS: Novell NetWare 3.12 - 5.00 (nearest)
fingerprint.notice 127.0.0.1 is running Novell NetWare 3.12 - 5.00 (nearest)
MAC: 06:05:04:03:02:01 (UNKNW) IP: 127.0.0.1 OS: Novell NetWare 3.12 - 5.00 (nearest) 1 service(s) (0 accounts for port 21)
dissector.ftp.info FTP : 127.0.0.1:21 -> USER: anonymous PASS: guest@example.com
MAC: 06:05:04:03:02:01 (UNKNW) IP: 127.0.0.1 OS: Novell NetWare 3.12 - 5.00 (nearest) 1 service(s) (1 accounts for port 21)
"""

import os.path

from umit.pm.core.i18n import _
from umit.pm.gui.core.app import PMApp
from umit.pm.core.atoms import defaultdict
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *

from umit.pm.core.bus import unbind_function, implements
from umit.pm.core.providers import AccountProvider, PortProvider, \
     ProfileProvider, \
     UNKNOWN_TYPE, HOST_LOCAL_TYPE, HOST_NONLOCAL_TYPE, \
     GATEWAY_TYPE, ROUTER_TYPE

################################################################################
# Provider implementation
################################################################################

Account = AccountProvider

class Port(PortProvider):
    def get_account(self, user, pwd):
        for a in self.accounts:
            if a.username == user and a.password == pwd:
                return a

        a = Account()
        self.accounts.append(a)
        return a

class Profile(ProfileProvider):
    def get_port(self, proto, port):
        for p in self.ports:
            if p.proto == proto and p.port == port:
                return p

        p = Port()
        p.port = port
        p.proto = proto
        self.ports.append(p)
        return p

    def __str__(self):
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

@implements('pm.hostlist')
class Profiler(Plugin, PassiveAudit):
    def start(self, reader):
        # We see profile with l3_addr as key (IP address)
        # and the overflowed items as a list. So we use a defaultdict
        self.profiles = defaultdict(list)

        conf = AuditManager().get_configuration('passive.profiler')

        self.maxnum = max(conf['cleanup_hit'], 10)
        self.keep_local = conf['keep_local']

        if conf['mac_fingerprint']:
            if reader:
                contents = reader.file.read('data/finger.mac.db')
            else:
                contents = open(os.path.join('passive', 'profiler', 'data',
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

        if reader:
            self.debug = False
        else:
            self.debug = True

    @unbind_function('pm.hostlist', ('get', 'info', 'populate', 'get_target'))
    def stop(self):
        try:
            manager.add_decoder_hook(PROTO_LAYER, NL_TYPE_TCP,
                                     self._parse_tcp, 1)
        except:
            pass

        try:
            manager.add_decoder_hook(NET_LAYER, LL_TYPE_ARP,
                                     self._parse_arp, 1)
        except:
            pass

        try:
            manager.add_decoder_hook(PROTO_LAYER, NL_TYPE_ICMP,
                                     self._parse_icmp, 1)
        except:
            pass

    def __impl_info(self, intf, ip, mac):
        """
        @return a ProfileProvider object or None if not found
        """

        for prof in self.profiles[ip]:
            if prof.l2_addr == mac:
                return prof

    def __impl_populate(self, interface):
        # This signal is triggered when the user change the interface
        # combobox selection and we have to repopulate the tree

        log.debug('Profiler is going to repopulate the hostlist for %s intf' % \
                  interface)

        ret = []

        for ip in self.profiles:
            for prof in self.profiles[ip]:
                ret.append((ip, prof.l2_addr, prof.hostname))

        return ret

    def __impl_get(self):
        return self.profiles

    def __impl_get_target(self, **kwargs):
        ret = []
        l2_addr, l3_addr, hostname, netmask = None, None, None, None

        if 'l2_addr' in kwargs:
            l2_addr = kwargs.pop('l2_addr')
        if 'l3_addr' in kwargs:
            l3_addr = kwargs.pop('l3_addr')
        if 'hostname' in kwargs:
            hostname = kwargs.pop('hostname')
        if 'netmask' in kwargs:
            netmask = kwargs.pop('netmask')

        log.debug('Looking for a profile matching l2_addr=%s l3_addr=%s '
                  'hostname=%s netmask=%s' % \
                  (l2_addr, l3_addr, hostname, netmask))

        check_validity = lambda prof: \
               (not l2_addr or (l2_addr and prof.l2_addr == l2_addr)) and \
               (not hostname or (hostname and prof.hostname == hostname))

        if l3_addr:
            if l3_addr not in self.profiles:
                return None

            for prof in self.profiles[l3_addr]:
                if check_validity(prof):
                    ret.append(prof)
        else:
            if netmask:
                valid_ip = filter(netmask.match_strict, self.profiles.keys())
            else:
                valid_ip = self.profiles.keys()

            for ip in valid_ip:
                for prof in self.profiles[ip]:
                    if check_validity(prof):
                        ret.append(prof)

        log.debug('Returning %s' % ret)
        return ret

    def register_hooks(self):
        manager = AuditManager()

        # TODO: also handle UDP when UDP dissectors will be ready.
        manager.add_decoder_hook(PROTO_LAYER, NL_TYPE_TCP,
                                 self._parse_tcp, 1)

        manager.add_decoder_hook(NET_LAYER, LL_TYPE_ARP,
                                 self._parse_arp, 1)

        manager.add_decoder_hook(PROTO_LAYER, NL_TYPE_ICMP,
                                 self._parse_icmp, 1)

    def _parse_tcp(self, mpkt):
        if mpkt.flags & MPKT_FORWARDED or \
           mpkt.flags & MPKT_IGNORE:
            return

        sport = mpkt.l4_src
        dport = mpkt.l4_dst
        tcpflags = mpkt.l4_flags

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
            account.password = password

        if self.debug and prof:
            print prof

    def _parse_arp(self, mpkt):
        if mpkt.context:
            mpkt.context.check_forwarded(mpkt)

        if mpkt.flags & MPKT_FORWARDED or \
           mpkt.flags & MPKT_IGNORE:
            return

        prof = self.get_or_create(mpkt)
        prof.type = HOST_LOCAL_TYPE
        prof.distance = 1 # we are in LAN so distance is 1

        # TODO: we have to check the interface ip with the ip of mpkt
        # and if equal set distance to 0

    def _parse_icmp(self, mpkt):
        if mpkt.flags & MPKT_FORWARDED or \
           mpkt.flags & MPKT_IGNORE:
            return

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

    def cleanup(self):
        # Yes this is really a mess. But it is for performance :)
        log.info('Cleaning up all collected profiles')

        if self.keep_local:
            not_interesting = lambda p: p.type != HOST_LOCAL_TYPE
        else:
            not_interesting = lambda p: True

        ipidx = 0
        ips = self.profiles.keys()

        while ipidx < len(ips):
            ipkey = ips[ipidx]
            profiles = self.profiles[ipkey]

            profidx = 0
            proflen = len(profiles)

            while profidx < proflen:
                profile = profiles[profidx]

                if not_interesting(profile):
                    if profile.fingerprint or profile.ports:
                        AuditManager().user_msg(str(profile), 6, 'profiler')

                    # Delete the profile
                    profile = None
                    del profiles[profidx]
                    proflen -= 1
                else:
                    profidx += 1

            if not profiles:
                del self.profiles[ipkey]

            ipidx += 1

    def get_or_create(self, mpkt, clientside=False):
        if len(self.profiles) >= self.maxnum:
            self.cleanup()

        if not clientside:
            ip = mpkt.l3_src
            mac = mpkt.l2_src
        else:
            ip = mpkt.l3_dst
            mac = mpkt.l2_dst

        for prof in self.profiles[ip]:
            if not mac:
                return prof
            elif prof.l2_addr == mac:
                return prof
        else:
            prof = Profile()
            prof.l2_addr = mac
            prof.l3_addr = ip

            self.profiles[ip].append(prof)

            if self.macdb:
                prof.vendor = self.macdb.get(mac[:8].replace(':', '').upper(),
                                             _('UNKNW'))

            log.info('Adding a new profile -> %s' % prof)

            return prof

__plugins__ = [Profiler]
__plugins_deps__ = [('Profiler', ['=TCPDecoder-1.0'], ['=Profiler-1.0'], [])]

__audit_type__ = 0
__protocols__ = (('icmp', None), ('eth', None))
__configurations__ = (('passive.profiler', {
    'mac_fingerprint' : [True, 'Enable MAC lookup into DB to report NIC '
                         'vendor'],
    'keep_local' : [True, 'Keep only reserved addresses (127./172./10.)'],
    'cleanup_hit' : [60, 'Purge local cache after cleanup_timeout seconds.' \
                     'All sensible information will be printed before real '
                     'deletion. Values should be >= 10'],
    }),
)
