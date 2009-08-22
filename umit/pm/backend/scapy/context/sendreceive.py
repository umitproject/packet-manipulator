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

from threading import Lock
from umit.pm.core.i18n import _
from umit.pm.core.atoms import with_decorator
from umit.pm.backend.scapy.utils import send_receive_packet

def register_send_receive_context(BaseSendReceiveContext):

    class SendReceiveContext(BaseSendReceiveContext):
        def __init__(self, metapacket, count, inter, iface, \
                      strict, report_recv, report_sent, capmethod, \
                      scallback, rcallback, sudata=None, rudata=None):

            BaseSendReceiveContext.__init__(self, metapacket, count,
                                            inter, iface, strict,
                                            report_recv, report_sent, capmethod,
                                            scallback, rcallback,
                                            sudata, rudata)

            self.lock = Lock()
            self.thread = None
            self.internal = False
            self.title = _('Send/receive %s') % metapacket.summary()

        @with_decorator
        def get_all_data(self):
            return BaseSendReceiveContext.get_all_data(self)

        @with_decorator
        def get_data(self):
            return BaseSendReceiveContext.get_data(self)

        @with_decorator
        def set_data(self, val):
            self.data = val

        def __threads_active(self):
            if self.thread and self.thread.isAlive():
                return True
            return False

        def _start(self):
            if not self.tot_count or (self.tot_count - self.count > 0 and \
                                      self.remaining > 0):
                self.internal = True
                self.state = self.RUNNING

                try:
                    self.thread = send_receive_packet( \
                        self.packet, self.tot_count - self.count, self.inter, \
                        self.iface, self.strict, self.capmethod, \
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

            self.count = 0
            self.percentage = 0.0
            self.remaining = self.tot_count
            self.answers = 0
            self.received = 0

            return self._start()

        def _stop(self):
            self.internal = False
            self.thread.terminate()
            return True

        _pause = _stop

        def get_percentage(self):
            if self.state == self.NOT_RUNNING:
                return 100.0
            else:
                return None

        def __send_callback(self, packet, idx, udata):
            self.count += 1

            if self.tot_count:
                self.summary = _('Sending packet %d of %d') % (self.count,
                                                               self.tot_count)
            else:
                self.summary = _('Sending packet %s') % packet.summary()

            self.percentage = (self.percentage + 536870911) % 2147483647

            if self.report_sent:
                self.data.append(packet)

            if self.scallback:
                self.scallback(packet, self.count, udata)

            if not self.internal:
                self.state = self.NOT_RUNNING

            return self.state == self.NOT_RUNNING or \
                   self.state == self.PAUSED

        def __recv_callback(self, packet, is_reply, udata):
            if not packet:
                self.internal = False
                self.summary = _('%d of %d replie(s) received') % \
                                (self.answers, self.received)
            else:
                self.received += 1
                self.summary = _('Received/Answered/Remaining %d/%d/%d') % \
                                (self.received, self.answers, self.remaining)

                if is_reply:
                    self.answers += 1
                    self.remaining -= 1

                if is_reply or self.report_recv:
                    self.data.append(packet)

            self.percentage = (self.percentage + 536870911) % 2147483647

            if self.rcallback:
                self.rcallback(packet, is_reply, udata)

            if not self.internal:
                self.state = self.NOT_RUNNING

            return self.state == self.NOT_RUNNING or \
                   self.state == self.PAUSED

    return SendReceiveContext
