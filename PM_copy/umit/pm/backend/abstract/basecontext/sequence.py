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

from umit.pm.core.i18n import _
from timed import TimedContext
from umit.pm.backend.abstract.context import register_sequence_context

class BaseSequenceContext(TimedContext):
    def __init__(self, seq, count=1, inter=0, iface=None, \
                 strict=True, report_recv=False, report_sent=True, capmethod=0,\
                 scallback=None, rcallback=None, sudata=None, rudata=None):

        """
        Create a BaseSequenceContext object

        If seq is a string then the sequence is loaded from file pointed by
        seq variable and you could set the other attributes are ignored except
        [sr]callback and [sr]udata. The others are loaded directly from file.

        @param seq a Sequence object or a string to load from
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

        TimedContext.__init__(self)

        if isinstance(seq, basestring):
            self.cap_file = seq

            self.title = self.cap_file

            self.tot_loop_count = 1
            self.loop_count = 0

            self.tot_packet_count = len(seq)
            self.packet_count = 0

            self.inter = 0
            self.iface = None

            self.strict = True
            self.report_recv = True
            self.report_sent = True
            self.capmethod = 0

        else:
            self.seq = seq
            self.title = _('Unsaved sequence')

            self.tot_loop_count = count
            self.loop_count = 0

            self.tot_packet_count = len(seq)
            self.packet_count = 0

            self.inter = float(inter) / 1000.0
            self.iface = iface

            self.strict = strict
            self.report_recv = report_recv
            self.report_sent = report_sent
            self.capmethod = capmethod

        self.scallback = scallback
        self.rcallback = rcallback
        self.sudata = sudata
        self.rudata = rudata

        self.answers = 0
        self.received = 0

    def get_sequence(self):
        return self.seq
    def set_sequence(self, val):
        self.seq = val

SequenceContext = register_sequence_context(BaseSequenceContext)
