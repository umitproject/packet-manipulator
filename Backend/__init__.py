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

import datetime

from threading import Thread, RLock
from Manager.PreferenceManager import Prefs

class VirtualIFace:
    def __init__(self, name, desc, ip):
        self.name = name
        self.description = desc
        self.ip = ip

class SniffContext(Thread):
    """
    A sniff context for controlling various options.
    """

    def __init__(self, iface, filter=None, maxsize=0, capfile=None, \
                 scount=0, stime=0, ssize=0, real=True, scroll=True, \
                 resmac=True, resname=False, restransport=True, promisc=True):

        self.iface = iface
        self.filter = filter
        self.max_packet_size = maxsize
        self.cap_file = capfile
        self.promisc = promisc

        self.stop_count = scount
        self.stop_time = stime
        self.stop_size = ssize

        self.real_time = real
        self.auto_scroll = scroll

        self.mac_resolution = resmac
        self.name_resolution = resname
        self.transport_resoltioin = restransport

        self.tot_size = 0
        self.tot_time = 0
        self.tot_count = 0

        self.running = True
        self.lock = RLock()
        self.data = []
        self.sniffer = None

        self.socket = None

        super(SniffContext, self).__init__(name="SniffContext")

    def get_data(self):
        with self.lock:
            lst = self.data
            self.data = []
            return lst

    def destroy(self):
        self.running = False

    def run(self):
        # Thread main loop

        packet = None
        prevtime = datetime.datetime.now()

        while self.running:

            while not packet and self.running:
                packet = next_packet(self)

            now = datetime.datetime.now()
            delta = now - prevtime
            prevtime = now

            self.tot_count += 1
            self.tot_size += packet.get_size()

            if delta == abs(delta):
                self.tot_time += delta.seconds
                # Else we are too speedy :D

            with self.lock:
                self.data.append(packet)

            if self.stop_count and self.tot_count >= self.stop_count or \
               self.stop_time and self.tot_time >= self.stop_time or \
               self.stop_size and self.tot_size >= self.stop_size:
                print "out?"
                return

if Prefs()['backend.system'].value.lower() == 'umpa':
    from UMPA import *
elif Prefs()['backend.system'].value.lower() == 'scapy':
    from Scapy import *
