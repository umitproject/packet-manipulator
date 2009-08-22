#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
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

class VirtualIFace(object):
    def __init__(self, name, desc, ip):
        self.name = name
        self.description = desc
        self.ip = ip

class SequencePacket(object):
    def __init__(self, packet, filter='', inter=0):
        self.packet = packet
        self.filter = None
        self.inter = inter

# Contexts
from abstract.basecontext.static import StaticContext
from abstract.basecontext.timed import TimedContext
from abstract.basecontext.send import SendContext
from abstract.basecontext.sendreceive import SendReceiveContext
from abstract.basecontext.sniff import SniffContext
from abstract.basecontext.sequence import SequenceContext
from abstract.basecontext.audit import AuditContext

from umit.pm.manager.preferencemanager import Prefs

if Prefs()['backend.system'].value.lower() == 'umpa':
    from umpa import *
else:
    from scapy import *
