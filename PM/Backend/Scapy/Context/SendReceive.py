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
from PM.Backend.Scapy.utils import send_receive_packet

def register_send_receive_context(BaseSendReceiveContext):

    class SendReceiveContext(BaseSendReceiveContext):
        def __init__(self, metapacket, count, inter, iface, \
                     scallback, rcallback, sudata=None, rudata=None):

            BaseSendReceiveContext.__init__(self, metapacket, count,
                                            inter, iface, scallback,
                                            rcallback, sudata, rudata)

            self.lock = Lock()
            self.sthread, self.rthread = None, None
            self.internal = False
            self.title = _('Send/receive %s') % metapacket.summary()

        def get_all_data(self):
            with self.lock:
                return BaseSendReceiveContext.get_all_data(self)

        def get_data(self):
            with self.lock:
                return BaseSendReceiveContext.get_data(self)

        def set_data(self, val):
            with self.lock:
                self.data = val

        def __threads_active(self):
            if self.sthread and self.sthread.isAlive():
                return True
            if self.rthread and self.rthread.isAlive():
                return True
            return False

        def _start(self):
            if self.tot_count - self.count > 0 and self.remaining > 0:
                self.internal = True
                self.state = self.RUNNING

                try:
                    self.sthread, self.rthread = send_receive_packet( \
                                    self.packet, self.tot_count - self.count, self.inter, \
                                    self.iface, self.__send_callback, self.__recv_callback, \
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
            if self.__threads_active():
                return False

            return self._start()
        
        def _restart(self):
            if self.__threads_active():
                return False

            self.count = 0
            self.percentage = 0.0
            self.remaining = self.tot_count
            self.answers = 0
            self.received = 0

            return self._start()

        def _stop(self):
            self.internal = False
            return True

        _pause = _stop

        def get_percentage(self):
            if self.state == self.NOT_RUNNING:
                return 100.0
            else:
                return None

        def __send_callback(self, packet, idx, udata):
            self.count += 1

            self.summary = _('Sending packet %d of %d') % (self.count, self.tot_count)
            self.percentage = (self.percentage + 536870911) % 2147483647

            if self.scallback:
                self.scallback(packet, self.count, udata)

            if not self.internal:
                self.state = self.NOT_RUNNING

            return self.state == self.NOT_RUNNING or \
                   self.state == self.PAUSED

        def __recv_callback(self, packet, is_reply, udata):
            if not packet:
                self.internal = False
                self.summary = _('%d of %d replie(s) received') % (self.answers, self.received)
            else:
                self.received += 1
                self.summary = _('Received/Answered/Remaining %d/%d/%d') % (self.received, self.answers, self.remaining)

                if is_reply:
                    self.answers += 1
                    self.remaining -= 1
                    self.data.append(packet)

            self.percentage = (self.percentage + 536870911) % 2147483647

            if self.rcallback:
                self.rcallback(packet, is_reply, udata)

            if not self.internal:
                self.state = self.NOT_RUNNING

            return self.state == self.NOT_RUNNING or \
                   self.state == self.PAUSED

        #def pause(self):
        #    BaseSendReceiveContext.pause(self)
        #    self.sthread.join()
        #    self.rthread.join()

        #def stop(self):
        #    BaseSendReceiveContext.stop(self)
        #    self.sthread.join()
        #    self.rthread.join()

        def join(self):
            if self.sthread:
                self.sthread.join()

            if self.rthread:
                self.rthread.join()

            self.running = False

    return SendReceiveContext
