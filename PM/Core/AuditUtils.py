#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
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
General purpose functions used by various audit plugins goes here.
"""

import re
import sys

from array import array
from random import randint
from struct import pack, unpack
from subprocess import Popen, PIPE
from socket import inet_ntoa, inet_aton

from PM.Core.NetConst import IL_TYPE_ETH

# Code ripped from scapy
BIG_ENDIAN= pack("H",1) == "\x00\x01"

if BIG_ENDIAN:
    def checksum(pkt):
        if len(pkt) % 2 == 1:
            pkt += "\0"
        s = sum(array("H", pkt))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        s = ~s
        return s & 0xffff
else:
    def checksum(pkt):
        if len(pkt) % 2 == 1:
            pkt += "\0"
        s = sum(array("H", pkt))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        s = ~s
        return (((s>>8)&0xff)|s<<8) & 0xffff


def audit_unittest(parameters, pcap=None, dl=IL_TYPE_ETH):
    cmd = 'python audittester.py -q -t%d %s %s' % (dl, parameters,
                                            (pcap) and 'pcap-tests/%s' % pcap \
                                                   or '')

    process = Popen(cmd, stdout=PIPE, shell=True)

    out, err = process.communicate()
    sys.stdout.write(out)

################################################################################
# Netmask utilities
################################################################################

def itom(x):
    return (0xffffffff00000000L>>x)&0xffffffffL

def atol(x):
    try:
        ip = inet_aton(x)
    except socket.error:
        ip = inet_aton(socket.gethostbyname(x))
    return unpack("!I", ip)[0]

class Netmask(object):
    def __init__(self, netmask):
        if not is_netmask(netmask):
            raise Exception('Not a valid netmask')

        if '/' in netmask:
            dest, netmask = netmask.split('/')
        else:
            dest, netmask = netmask, '24'

        netmask = itom(int(netmask))
        dest += '.0' * (3 - dest.count('.'))
        dest = atol(dest)

        self.net = netmask
        self.dest = dest

        self.netmask = netmask & dest

    def match(self, ip):
        ip = atol(ip)
        return (self.netmask | ip) & self.net == self.netmask

################################################################################
# String utilities
################################################################################

ip_regex = re.compile(
    '\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}' \
    '(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b'
)

mac_regex = re.compile(
    '([0-9a-fA-F]{2}([:-]|$)){6}'
)

netmask_regex = re.compile(
    '\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}' \
    '(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(/[0-3]?[0-9])?\\b'
)

def is_ip(txt):
    return ip_regex.match(txt) is not None
def is_mac(txt):
    return mac_regex.match(txt) is not None
def is_netmask(txt):
    return netmask_regex.match(txt) is not None

def random_ip():
    return inet_ntoa(pack('I', randint(0, 4294967295)))

################################################################################
# Audit operation
################################################################################

class AuditOperation(object):
    """
    Use this class to implement audit operations.

    See also AuditPage.py
    """

    RUNNING, NOT_RUNNING = range(2)

    has_stop = False
    has_pause = False
    has_start = False
    has_restart = False
    has_reconfigure = False

    def __init__(self):
        self._state = self.NOT_RUNNING
        self.percentage = 0
        self._summary = ''

    def activate(self):
        "Fired when the user clicks on Open"
        pass
    def stop(self):
        "Fired when the user clicks on Stop"
        pass
    def start(self):
        "Fired when the user clicks on Start"
        pass
    def restart(self):
        "Fired when the user clicks on Restart"
        pass
    def reconfigure(self):
        "Fired when the user clicks on Reconfigure"
        pass

    def get_state(self):
        return self._state
    def get_summary(self):
        return self._summary
    def get_percentage(self):
        if self.percentage > 100:
            return None # pulse
        return self.percentage

    def set_state(self, value):
        self._state = value
    def set_summary(self, value):
        self._summary = value

    state = property(get_state, set_state)
    summary = property(get_summary, set_summary)
