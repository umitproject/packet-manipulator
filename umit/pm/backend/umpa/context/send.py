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

from umit.pm.backend.umpa import send_packet
from umit.pm.core.i18n import _

def register_send_context(BaseSendContext):

    class SendContext(BaseSendContext):
        def __init__(self, metapacket, count, inter, callback, udata):
            BaseSendContext.__init__(self, metapacket, count, inter, callback, udata)

            self.thread = None
            self.internal = False

        def _start(self):
            if self.tot_count - self.count > 0:
                self.state = self.RUNNING
                self.internal = True
                self.thread = send_packet(self.packet, self.tot_count - self.count, self.inter, \
                                          self.__send_callback, self.udata)
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
            return True

        _pause = _stop

        def __send_callback(self, packet, udata):
            if packet and isinstance(packet, Exception):
                self.internal = False
                self.summary = str(packet)
            else:
                if packet:
                    self.count += 1
                else:
                    self.state = self.NOT_RUNNING

                if self.count == self.tot_count:
                    self.summary = _("%d packet(s) sent.") % self.tot_count
                else:
                    self.summary = _("Sending packet %d of %d") % (self.count, self.tot_count)

                self.percentage = float(self.count) / float(self.tot_count) * 100.0

            if self.callback:
                self.callback(packet, udata)

            if not self.internal:
                self.state = self.NOT_RUNNING

            return self.state == self.NOT_RUNNING or \
                   self.state == self.PAUSED

        #def pause(self):
        #    BaseSendContext.pause(self)
        #    self.thread.join()

        #def stop(self):
        #    BaseSendContext.stop(self)
        #    self.thread.join()

        def join(self):
            self.thread.join()
            self.running = False

    return SendContext
