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

class VirtualIFace(object):
    def __init__(self, name, desc, ip):
        self.name = name
        self.description = desc
        self.ip = ip

class BaseContext(object):
    """
    This is a base context for sending/receiving/loading packets
    """

    def __init__(self):
        self.running = False
        self.summary = ''

    def get_data(self):
        return []

    def start(self):
        pass

    def destroy(self):
        self.running = False

    def join(self):
        pass

    def is_alive(self):
        return self.running

    def get_summary(self):
        return self.summary

# Send and receive context

class TimedContext(BaseContext):
    NOT_RUNNING, RUNNING, PAUSED = range(3)

    def __init__(self):
        self._state = TimedContext.NOT_RUNNING
        BaseContext.__init__(self)

    def _start(self):
        "override this"
        pass

    def start(self):
        if self.state != TimedContext.RUNNING:
            if self._start() == True:
                self.state = TimedContext.RUNNING

    def pause(self):
        if self.state == TimedContext.RUNNING:
            self.state = TimedContext.PAUSED

    def stop(self):
        if self.state == TimedContext.RUNNING:
            self.state = TimedContext.NOT_RUNNING

    def restart(self):
        if self.state != TimedContext.RUNNING:
            self.start()

    resume = restart

    def get_state(self):
        return self._state
    def set_state(self, val):
        if val == TimedContext.RUNNING:
            self.running = True
        else:
            self.running = False

        self._state = val

    state = property(get_state, set_state)

class SendContext(TimedContext):
    def __init__(self, metapacket, count, inter, callback, udata=None):
        self.packet = metapacket
        self.tot_count = count
        self.count = 0
        self.inter = inter
        self.callback = callback
        self.udata = udata

        TimedContext.__init__(self)

class SendReceiveContext(TimedContext):
    def __init__(self, metapacket, count, inter, iface, \
                 scallback, rcallback, sudata=None, rudata=None):

        self.packet = metapacket
        self.tot_count = count
        self.count = 0
        self.inter = inter
        self.iface = iface
        self.scallback = scallback
        self.rcallback = rcallback
        self.sudata = sudata
        self.rudata = rudata

        self.remaining = count
        self.answers = 0
        self.received = 0

        self.data = []

        TimedContext.__init__(self)

class SniffContext(BaseContext):
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

        BaseReceiver.__init__(self)

# This is for loading pcap files
FileContext = SniffContext
EditContext = BaseContext

if Prefs()['backend.system'].value.lower() == 'umpa':
    from UMPA import *
elif Prefs()['backend.system'].value.lower() == 'scapy':
    from Scapy import *
