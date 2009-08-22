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

from umit.pm.backend.scapy.utils import send_packet
from umit.pm.core.i18n import _

def register_send_context(BaseSendContext):

    class SendContext(BaseSendContext):
        def __init__(self, metapacket, count, inter, iface, callback, \
                     udata=None):
            BaseSendContext.__init__(self, metapacket, count, inter, iface,
                                     callback, udata)

            self.thread = None
            self.internal = False

        def _start(self):
            if not self.tot_count or self.tot_count - self.count > 0:
                self.state = self.RUNNING
                self.internal = True

                try:
                    self.thread = send_packet(self.packet,
                                              self.tot_count - self.count,
                                              self.inter,
                                              self.iface,
                                              self.__send_callback,
                                              self.udata)
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
            return self._start()

        def _stop(self):
            self.internal = False
            self.thread.terminate()
            return True

        _pause = _stop

        def __send_callback(self, packet, udata):
            if packet and isinstance(packet, Exception):
                self.internal = False
                self.summary = str(packet)
            elif self.tot_count:
                if packet:
                    self.count += 1
                else:
                    self.state = self.NOT_RUNNING

                if self.count == self.tot_count:
                    self.summary = _("%d packet(s) sent.") % self.tot_count
                else:
                    self.summary = _("Sending packet %d of %d") % (self.count, self.tot_count)

                self.percentage = float(self.count) / float(self.tot_count) * 100.0
            else:
                # If we are here we need to pulse the value
                self.summary = _("Sending packet %s") % packet.summary()
                self.percentage = (self.percentage + 536870911) % 2147483647

            if self.callback:
                self.callback(packet, udata)

            if not self.internal:
                self.state = self.NOT_RUNNING

            return self.state == self.NOT_RUNNING or \
                   self.state == self.PAUSED

        def get_percentage(self):
            if self.state == self.NOT_RUNNING:
                return 100.0

            if self.tot_count:
                return self.percentage

            return None

    return SendContext
