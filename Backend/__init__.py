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

class StaticContext(object):
    def __init__(self):
        self._summary = ''
        self._data = []

    def get_summary(self):
        return self._summary
    def set_summary(self, val):
        self._summary = val

    def get_data(self):
        return self._data
    def set_data(self, val):
        self._data = val

    data = property(get_data, set_data)
    summary = property(get_summary, set_summary)
    
class BaseContext(StaticContext):
    NOT_RUNNING, RUNNING, PAUSED = range(3)

    # Select the suport operations
    has_stop = True
    has_pause = True
    has_restart = True

    def __init__(self):
        self._state = self.NOT_RUNNING

        self._summary = ''
        self._percentage = 0.0

        self._data = []
        self._last = 0

        StaticContext.__init__(self)

    def _start(self):
        self.state = self.RUNNING
        return True
    _resume = _start
    _restart = _start

    def _stop(self):
        self.state = self.NOT_RUNNING
        return True

    def _pause(self):
        self.state = self.PAUSED
        return True

    def join(self):
        pass
    
    def is_alive(self):
        return self._state != self.NOT_RUNNING

    def start(self):
        print "Start():",
        if self.state != self.RUNNING:
            if self._start():
                print "True"
                return True
        print "False"
        return False

    def pause(self):
        print "Pause():",
        if self.state == self.RUNNING:
            if self._pause():
                print "True"
                return True
        print "False"
        return False

    def stop(self):
        print "Stop():",
        if self.state == self.RUNNING:
            if self._stop():
                print "True"
                return True
        print "False"
        return False

    def restart(self):
        print "Restart()",
        if self.state != self.RUNNING:
            if self._restart():
                print "True"
                return True
        print "False"
        return False

    def resume(self):
        print "Resume()",
        if self.state != self.RUNNING:
            if self._resume():
                print "True"
                return True
        print "False"
        return False

    def get_state(self):
        return self._state
    def set_state(self, val):
        self._state = val

    def get_percentage(self):
        return self._percentage
    def set_percentage(self, val):
        self._percentage = val

    # Returns the last data
    def get_data(self):
        end = len(self._data)
        lst = self._data[self._last:]
        self._last = end
        return lst
    
    def get_all_data(self):
        return self._data

    state = property(get_state, set_state)
    percentage = property(get_percentage, set_percentage)

class SendContext(BaseContext):
    def __init__(self, metapacket, count, inter, callback, udata=None):
        self.packet = metapacket
        self.tot_count = count
        self.count = 0
        self.inter = float(inter) / 1000.0
        self.callback = callback
        self.udata = udata

        BaseContext.__init__(self)

class SendReceiveContext(BaseContext):
    def __init__(self, metapacket, count, inter, iface, \
                 scallback, rcallback, sudata=None, rudata=None):

        self.packet = metapacket
        self.tot_count = count
        self.count = 0
        self.inter = float(inter) / 1000.0
        self.iface = iface
        self.scallback = scallback
        self.rcallback = rcallback
        self.sudata = sudata
        self.rudata = rudata

        self.remaining = count
        self.answers = 0
        self.received = 0

        self.data = []

        BaseContext.__init__(self)

class SniffContext(BaseContext):
    """
    A sniff context for controlling various options.
    """
    
    has_stop = True
    has_resume = False
    has_restart = True

    def __init__(self, iface, filter=None, maxsize=0, capfile=None, \
                 scount=0, stime=0, ssize=0, real=True, scroll=True, \
                 resmac=True, resname=False, restransport=True, promisc=True, \
                 background=False, callback=None, udata=None):

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

        self.background = background
        self.callback = callback
        self.udata = udata

        self.tot_size = 0
        self.tot_time = 0
        self.tot_count = 0

        BaseContext.__init__(self)


# This is an edit session
EditContext = StaticContext

# These are for loading pcap files
class FileContext(StaticContext):
    def __init__(self, fname):
        StaticContext.__init__(self)

        self.fname = fname
        self.summary = fname

FileLoaderContext = FileContext
FileWriterContext = FileContext

if Prefs()['backend.system'].value.lower() == 'umpa':
    from UMPA import *
elif Prefs()['backend.system'].value.lower() == 'scapy':
    from Scapy import *
