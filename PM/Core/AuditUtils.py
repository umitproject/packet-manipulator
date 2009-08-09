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
General purpose functions used by various audit plugins goes here.
"""

import re
import sys
import array
import struct
import subprocess

# Code ripped from scapy
BIG_ENDIAN= struct.pack("H",1) == "\x00\x01"

if BIG_ENDIAN:
    def checksum(pkt):
        if len(pkt) % 2 == 1:
            pkt += "\0"
        s = sum(array.array("H", pkt))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        s = ~s
        return s & 0xffff
else:
    def checksum(pkt):
        if len(pkt) % 2 == 1:
            pkt += "\0"
        s = sum(array.array("H", pkt))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        s = ~s
        return (((s>>8)&0xff)|s<<8) & 0xffff


def audit_unittest(parameters, pcap=None):
    cmd = 'python audittester.py -q %s %s' % (parameters,
                                            (pcap) and 'pcap-tests/%s' % pcap \
                                                   or '')

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    out, err = process.communicate()
    sys.stdout.write(out)

################################################################################
# String utilities
################################################################################

ip_regex = re.compile('\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}' \
                      '(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b')
mac_regex = re.compile('([0-9a-fA-F]{2}([:-]|$)){6}')

def is_ip(txt):
    return ip_regex.match(txt) is not None
def is_mac(txt):
    return mac_regex.match(txt) is not None
