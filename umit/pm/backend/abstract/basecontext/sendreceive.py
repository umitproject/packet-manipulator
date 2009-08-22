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

from timed import TimedContext
from umit.pm.backend.abstract.context import register_send_receive_context

class BaseSendReceiveContext(TimedContext):
    "A context to send and receive packets"

    def __init__(self, metapacket, count, inter, iface, \
                  strict, report_recv, report_sent, capmethod, \
                  scallback, rcallback, sudata=None, rudata=None):

        """
        Create a BaseSendReceiveContext object

        @param metapacket the packet to send
        @param count the n of metapacket to send
        @param interval the interval between two consecutive send
        @param iface the interface to listen on for replies
        @param strict strict checking for reply
        @param report_recv report received packets
        @param report_sent report sent packets
        @param capmethod 0 for native, 1 for tcpdump, 2 for dumpcap
        @param scallback the send callback to call at each send
        @param rcallback the recv callback to call at each recv
        @param sudata the user data for scallback
        @param rudata the user data for rcallback
        """

        self.packet = metapacket
        self.tot_count = count
        self.count = 0
        self.inter = float(inter) / 1000.0
        self.iface = iface
        self.strict = strict
        self.report_recv = report_recv
        self.report_sent = report_sent
        self.scallback = scallback
        self.rcallback = rcallback
        self.sudata = sudata
        self.rudata = rudata

        self.remaining = count
        self.answers = 0
        self.received = 0
        self.capmethod = capmethod

        TimedContext.__init__(self)

SendReceiveContext = register_send_receive_context(BaseSendReceiveContext)
