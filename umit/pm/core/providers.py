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
This is the place where interface class are held.
"""

################################################################################
# Profile, Port, Account providers used by Profiler audit plugin
################################################################################

UNKNOWN_TYPE       = 0
HOST_LOCAL_TYPE    = 1
HOST_NONLOCAL_TYPE = 2
GATEWAY_TYPE       = 3
ROUTER_TYPE        = 4

class AccountProvider(object):
    def __init__(self):
        self.username = None
        self.password = None
        self.info = None
        self.failed = False
        self.ip_addr = None

class PortProvider(object):
    def __init__(self):
        self.proto = None
        self.port = None
        self.banner = None
        self.accounts = []

    def get_account(self, user, pwd):
        "@return a AccountProvider object or None"
        raise Exception('Not implemented')

class ProfileProvider(object):
    def __init__(self):
        self.l2_addr = None
        self.l3_addr = None
        self.hostname = None
        self.distance = 0
        self.ports = []
        self.type = UNKNOWN_TYPE
        self.fingerprint = None
        self.vendor = None

    def get_port(self, proto, port):
        "@return a PortProvider object or None"
        raise Exception('Not implemented')

class HostEntry(object):
    def __init__(self, l2_addr=None, l3_addr=None, hostname=None):
        self.l2_addr = l2_addr
        self.l3_addr = l3_addr
        self.hostname = hostname

    def __str__(self):
        out = ''

        if self.l2_addr:
            out += self.l2_addr + ' '
        if self.l3_addr:
            out += self.l3_addr + ' '
        if self.hostname:
            out += self.hostname + ' '

        if not out:
            return super(HostEntry, self).__str__()
        else:
            return out[:-1]
