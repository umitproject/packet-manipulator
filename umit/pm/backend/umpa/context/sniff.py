#!/usr/bin/env python                                   
# -*- coding: utf-8 -*-                                 
# Copyright (C) 2009 Adriano Monteiro Marques           
#                                                       
# Authors: Francesco Piccinno <stack.box@gmail.com>
#          Luís A. Bastião Silva <luis.kop@gmail.com> 
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

from datetime import datetime
from threading import Thread, Lock

from umit.pm.core.i18n import _
from umit.pm.backend.umpa import *

import umit.umpa.sniffing

def register_sniff_context(BaseSniffContext):
    class SniffContext(BaseSniffContext):
        """
        A sniff context for controlling various options.
        """
        has_stop = False
        has_pause = False
        has_restart = False

        def __init__(self, *args, **kwargs):
            BaseSniffContext.__init__(self, *args, **kwargs)

            self.title = _('%s capture') % self.iface
            self.priv = []
            self.lock = Lock()

        #@with_decorator
        def get_all_data(self):
            return BaseSniffContext.get_all_data(self)

        #@with_decorator
        def get_data(self):
            return BaseSniffContext.get_data(self)

        #@with_decorator
        def set_data(self, val):
            self.data = val
            
        def get_percentage(self):
            return 100.0
        def run(self):
            received_packets = umit.umpa.sniffing.sniff_loop(0, 
                                                            device=self.iface,
                                                            filter=self.filter,
                                                            callback=self._call)
        def _start(self):
            
            self.prevtime = datetime.now()
            if self.iface and self.capmethod == 0:

                
                self.thread = Thread(target=self.run)

                self.thread.setDaemon(True)
                self.thread.start()

                

                
                self.state = self.RUNNING
                
                self.internal = True
                self.data = []
                            
                self.summary = _('Sniffing')
                return True
           
            self.summary = _('Sniff is not avaiable with this backend')
            
            return False
        def _call(self, timestamp, pkt, *args):
            """
            @timestamp:
            @pkt:
            """
            
            self.priv.append((pkt,timestamp))
            if self.callback:
                self.callback(pkt, self.udata)
                
                
        def _stop(self):
            self.state = self.NOT_RUNNING
            
        def check_finished(self):
            if self.capmethod != 0:
                return

            priv = self.priv
            self.priv = []

            for r,t in priv:
                # This code should not be in the thread and called in the
                # main thread of the GUI so we can avoid packet loss.
                # It's better to have a temporary list object to store raw
                # packets captured from socket.recv(MTU) function and then joins
                # everything in self.data

                packet = MetaPacket(r)
                packet.time = t
                packet_size = packet.get_size()

                if self.max_packet_size and \
                   packet_size - self.max_packet_size > 0:

                    log.debug("Skipping current packet (max_packet_size)")
                    continue

                if self.min_packet_size and \
                   packet_size - self.min_packet_size < 0:

                    log.debug("Skipping current packet (min_packet_size)")
                    continue

                self.tot_count += 1
                self.tot_size += packet.get_size()

                now = datetime.now()
                delta = now - self.prevtime
                self.prevtime = now

                if delta == abs(delta):
                    self.tot_time += delta.seconds

                self.data.append(packet)

                #if self.audit_dispatcher:
                #    self.audit_dispatcher.feed(packet)

                # FIXME: This probably should be moved inside the run() function
                if self.callback:
                    self.callback(packet, self.udata)

                lst = []
    return SniffContext
