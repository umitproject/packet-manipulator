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

from __future__ import with_statement
from threading import Lock

from PM.Core.I18N import _
from PM.Backend.Scapy.utils import execute_sequence

def register_sequence_context(BaseSequenceContext):
    
    class SequenceContext(BaseSequenceContext):
        def __init__(self, seq, count, inter, iface, \
                     scallback, rcallback, sudata=None, rudata=None):

            BaseSequenceContext.__init__(self, seq, count, inter, iface, \
                                         scallback, rcallback, sudata, rudata)

            self.lock = Lock()
            self.thread = None
            self.internal = False
            self.title = _('Executing sequence (%d packets %d times)') % (self.tot_packet_count, count)

        def get_all_data(self):
            with self.lock:
                return BaseSequenceContext.get_all_data(self)

        def get_data(self):
            with self.lock:
                return BaseSequenceContext.get_data(self)

        def set_data(self, val):
            with self.lock:
                self.data = val

        def _start(self):
            if self.tot_packet_count - self.packet_count > 0 or \
               self.tot_loop_count - self.loop_count > 0:

                self.internal = True
                self.state = self.RUNNING

                try:
                    self.thread = execute_sequence(self.seq, max(self.tot_loop_count - self.loop_count, 1), \
                                                   self.inter, self.iface,                     \
                                                   self.__send_callback, self.__recv_callback, \
                                                   self.sudata, self.rudata)
                except Exception, err:
                    self.internal = False
                    self.state = self.NOT_RUNNING
                    self.summary = str(err)

                    return False
                else:
                    return True
            return False

        def _resume(self):
            if self.thread and self.thread.isAlive():
                return False

            return self._start()
        
        def _restart(self):
            if self.thread and self.thread.isAlive():
                return False

            self.packet_count = 0
            self.loop_count = 0
            self.percentage = 0.0
            self.answers = 0
            self.received = 0

            return self._start()

        def _stop(self):
            self.internal = False
            return True

        _pause = _stop

        def __send_callback(self, packet, want_reply, udata):
            if not packet:
                self.loop_count += 1
                self.summary = _('Running sequence %d of %d times') % (self.loop_count, self.tot_loop_count)
            else:
                self.packet_count += 1

                if want_reply:
                    self.summary = _('Sending packet %s and waiting a reply') % packet.summary()
                else:
                    self.summary = _('Sending packet %s') % packet.summary()

            self.percentage = float((float(self.packet_count) / float(self.tot_packet_count)) * \
                                    (float(self.loop_count + 1) / float(self.tot_loop_count + 1))) * 100.0

            if self.scallback:
                # FIXME: THIS FUCKING UDATA also in other files
                self.scallback(packet, want_reply, self.loop_count, self.packet_count, udata)

            if not self.internal:
                self.state = self.NOT_RUNNING

            return self.state == self.NOT_RUNNING or \
                   self.state == self.PAUSED

        def __recv_callback(self, packet, reply, udata):
            if not packet:
                self.internal = False
                self.summary = _('Sequence finished with %d packets sent and %d received') % \
                                (self.packet_count * self.loop_count, self.received * self.loop_count)
            else:
                self.received += 1
                self.summary = _('Received %s') % reply.summary()

                #self.data.append(packet)
                self.data.append(reply)

            if self.rcallback:
                self.rcallback(packet, reply, udata)

            if not self.internal:
                self.state = self.NOT_RUNNING

            return self.state == self.NOT_RUNNING or \
                   self.state == self.PAUSED

        def join(self):
            if self.thread and self.thread.isAlive():
                self.thread.join()

    return SequenceContext
