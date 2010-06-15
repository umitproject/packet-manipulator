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
Passive OS fingerprint module

>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip,tcp,fingerprint -sdecoder.ip.checksum_check=0,decoder.tcp.checksum_check=0', 'wrong-checksum.pcap')
fingerprint.notice 127.0.0.1 is running Novell NetWare 3.12 - 5.00 (nearest)
"""

import os.path

from socket import ntohs
from struct import unpack

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.gui.plugins.core import Core
from umit.pm.manager.auditmanager import PassiveAudit, AuditManager
from umit.pm.core.atoms import defaultdict, odict, generate_traceback
from umit.pm.core.netconst import *
from umit.pm.core.const import PM_TYPE_STR, PM_TYPE_LIST

from socket import ntohs
from umit.pm.core.auditutils import BIG_ENDIAN

if not BIG_ENDIAN:
    pntos = ntohs
# TODO: handle BIG_ENDIAN

TCPOPT_EOL       = 0
TCPOPT_NOP       = 1
TCPOPT_MAXSEG    = 2
TCPOPT_WSCALE    = 3
TCPOPT_SACKOK    = 4
TCPOPT_TIMESTAMP = 8

FINGER_LEN = 28
OS_LEN     = 60

def tcp_fp(finger):
    manager = AuditManager()

    def internal(mpkt):
        try:
            finger.push(mpkt, finger.TTL, mpkt.get_field('ip.ttl'))
            finger.push(mpkt, finger.DF, mpkt.get_field('ip.frag', 0) & 0x400)
            finger.push(mpkt, finger.LT, mpkt.get_field('ip.ihl', 0) * 4)

            tcpraw = mpkt.get_field('tcp')
            flags = mpkt.get_field('tcp.flags')

            if flags and finger and flags & TH_SYN:
                opt_start = 20
                opt_end = mpkt.get_field('tcp.dataofs') * 4

                finger.push(mpkt, finger.WINDOW, mpkt.get_field('tcp.window', 0))
                finger.push(mpkt, finger.TCPFLAG, (flags & TH_ACK) and 1 or 0)
                finger.push(mpkt, finger.LT, opt_end)

                while opt_start < opt_end:
                    val = ord(tcpraw[opt_start])

                    if val == TCPOPT_EOL:
                        opt_start = opt_end
                    elif val == TCPOPT_NOP:
                        finger.push(mpkt, finger.NOP, 1)
                        opt_start += 1
                    elif val == TCPOPT_SACKOK:
                        finger.push(mpkt, finger.SACK, 1)
                        opt_start += 2
                    elif val == TCPOPT_MAXSEG:
                        opt_start += 2
                        finger.push(mpkt, finger.MSS, pntos(unpack("H",
                                    tcpraw[opt_start:opt_start + 2])[0]))
                        opt_start += 2
                    elif val == TCPOPT_WSCALE:
                        opt_start += 2
                        finger.push(mpkt, finger.WS, ord(tcpraw[opt_start]))
                        opt_start += 1
                    elif val == TCPOPT_TIMESTAMP:
                        finger.push(mpkt, finger.TIMESTAMP, 1)
                        opt_start +=1
                        opt_start += ord(tcpraw[opt_start]) - 1
                    else:
                        opt_start += 1
                        if opt_start < len(tcpraw):# and ord(tcpraw[opt_start]):
                            opt_start += val - 1

                remote_os = finger.report(mpkt)

                mpkt.set_cfield('remote_os', remote_os)
                manager.user_msg(_('%s is running %s') % (mpkt.get_field('ip.src'),
                                                          remote_os),
                                 5, 'fingerprint')
        except Exception, err:
            log.error('Ignoring exception while setting fingerprint.')
            log.error(generate_traceback())

            log.debug('Clearing fingerprint.')
            finger.clear(mpkt)

    return internal

def ttl_predict(x):
    i = x
    j = 1
    c = 0

    while True:
        c = c + (i & 1)
        j = j << 1

        if i == 1:
            break

        i = i >> 1

    if c == 1:
        return x
    else:
        return j and j or 0xff

class OSFPModule(object):
    WINDOW,    \
    MSS,       \
    TTL,       \
    WS,        \
    SACK,      \
    NOP,       \
    DF,        \
    TIMESTAMP, \
    TCPFLAG,   \
    LT = range(10)

    def __init__(self, contents):
        assert isinstance(contents, basestring), "contents should be a string"

        self._osdb = odict()

        for i in contents.splitlines():
            line = i.strip()

            if line.startswith('#') or not line:
                continue

            try:
                fp = line[0:FINGER_LEN]
                first, second = fp.split(':', 1)

                if first in self._osdb:
                    self._osdb[first][second] = line[FINGER_LEN + 1:]
                else:
                    dct = odict()
                    dct[second] = line[FINGER_LEN + 1:]
                    self._osdb[first] = dct
            except:
                pass

        log.info("%d fingerprints loaded" % len(self._osdb))

    def push(self, mpkt, param, value):
        """
        Push a param value to the fingerprint cfield
        @param mpkt a MetaPacket instance already initialized with init
        @param param a param to set (WINDOW, MSS, TTL, etc.)
        @param value the value to set for the param
        """

        try:
            cfield = mpkt.get_cfield('osfp.passive_fingerprint')
        except KeyError:
            cfield = ['0000', '_MSS', 'TT', 'WS', '0', '0', '0', '0', 'F', 'LT']

        if param == self.WINDOW:
            cfield[0] = ('%04X' % value)[:4]
        elif param == self.MSS:
            cfield[1] = ('%04X' % value)[:4]
        elif param == self.TTL:
            cfield[2] = ('%02X' % ttl_predict(value))[:2]
        elif param == self.WS:
            cfield[3] = ('%02X' % value)[:2]
        elif param == self.SACK:
            cfield[4] = ('%d' % value)[0]
        elif param == self.NOP:
            cfield[5] = ('%d' % value)[0]
        elif param == self.DF:
            cfield[6] = ('%d' % value)[0]
        elif param == self.TIMESTAMP:
            cfield[7] = ('%d' % value)[0]
        elif param == self.TCPFLAG:
            if value == 1: cfield[8] = 'A'
            else: cfield[8] = 'S'
        elif param == self.LT:
            try:
                new_lt = int(cfield[9], 16) + value
            except ValueError:
                new_lt = value

            cfield[9] = ('%02X' % new_lt)[:2]

        mpkt.set_cfield('osfp.passive_fingerprint', cfield)

    def clear(self, mpkt):
        mpkt.unset_cfield('osfp.passive_fingerprint')

    def report(self, mpkt):
        try:
            cfield = ':'.join(mpkt.get_cfield('osfp.passive_fingerprint'))

            log.debug('Looking up for %s' % cfield)

            first, second = cfield.split(':', 1)

            return self._osdb[first][second]
        except KeyError:

            if first in self._osdb:
                # WINDOW match
                last_min_k = first

                for k2 in self._osdb[first]:
                    last_min_k2 = k2

                    if k2 >= second:
                        break
            else:
                last_min_k = None

                for k in self._osdb:
                    last_min_k = k

                    if k > first:
                        break

                last_min_k2 = self._osdb[last_min_k].keys()[0]

                for k2 in self._osdb[last_min_k]:
                    if k2 >= second:
                        break

                    last_min_k2 = k2

            log.debug('Nearest mid values: %s %s' % (last_min_k, last_min_k2))

            if last_min_k and last_min_k2:
                return self._osdb[last_min_k][last_min_k2] + " (nearest)"
            else:
                return 'Unknown fingerprint (%s)' % cfield

class OSFP(PassiveAudit):
    def register_hooks(self):
        AuditManager().add_decoder_hook(PROTO_LAYER, NL_TYPE_TCP,
                                        self._tcp_hook, 1)

    def start(self, reader):
        if reader:
            contents = reader.file.read('data/finger.os.db')
        else:
            contents = open(os.path.join('passive', 'fingerprint', 'data',
                                         'finger.os.db'), 'r').read()

        self.fingerprint = OSFPModule(contents)
        self._tcp_hook = tcp_fp(self.fingerprint)

    def stop(self):
        obj = self.fingerprint
        self.fingerprint = None

        log.debug('Destroying OSFP object %s' % obj)
        del obj

        try:
            AuditManager().remove_decoder_hook(PROTO_LAYER, NL_TYPE_TCP,
                                               self._tcp_hook, 1)
        except:
            pass

__plugins__ = [OSFP]
__plugins_deps__ = [('OSFP', ['IPDecoder', 'TCPDecoder'], ['=OSFP-1.0'], [])]

__audit_type__ = 0
__protocols__ = (('tcp', None), ('icmp', None))
__configurations__ = (('global.cfields', {
    'osfp.passive_fingerprint' : (PM_TYPE_LIST, 'Internal cfield used by OSFP'),
    'remote_os' : (PM_TYPE_STR, 'A string representing the remote OS'),}),
)

__vulnerabilities__ = (
    ('Passive OS fingerprinting',
     {'description' : 'TCP/IP stack fingerprinting is the passive collection '
      'of configuration attributes from a remote device during standard layer '
      '4 network communications. The combination of parameters may then be '
      'used to infer the remote machine\'s operating system (aka, OS '
      'fingerprinting), or incorporated into a device fingerprint.',
      'classes' : ('design error', ),
      'references' : (
          (None, 'http://en.wikipedia.org/wiki/TCP/IP_stack_fingerprinting'),
      )
     }),
)
