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

from Manager.PreferenceManager import Prefs

class VirtualIFace:
    def __init__(self, name, desc, ip):
        self.name = name
        self.description = desc
        self.ip = ip

class SniffContext:
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

        self.exception = None

    def start(self):
        pass

    def get_data(self):
        return []

    def destroy(self):
        pass

    def join(self):
        pass

    def is_alive(self):
        return True

if Prefs()['backend.system'].value.lower() == 'umpa':
    from UMPA import *
elif Prefs()['backend.system'].value.lower() == 'scapy':
    from Scapy import *
