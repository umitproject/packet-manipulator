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

"""
In this module are defined:
    - register_static_context
    - register_timed_context
    - register_send_context
    - register_send_receive_context
    - register_sniff_context
    - register_sequence_context

respectively to hook the contexts StaticContext, TimedContext,
SendContext, SendReceiveContext, SniffContext and SequenceContext
class creation.

It accepts as argument a BaseContext class objects defined in
Abstact/BaseContext and should return a new class object that
subclass this abstract class passed as argument to be valid.

So in your backend you should override this functions
if you want to customize the base context classes.

See also Scapy directory for reference.
"""

from PM.Core.Logger import log

class SequenceObject(object):
    def __init__(self, packet, inter=0, filter=''):
        self.packet = packet
        self.inter = float(inter / 1000.0)
        self.filter = filter

        self.conditional = []

    def append_condition(self, obj):
        assert (isinstance(obj, SequenceObject))
        self.conditional.append(obj)

    def insert(self, idx, obj):
        assert (isinstance(obj, SequenceObject))
        self.conditional.insert(idx, obj)

    def remove(self, obj):
        assert (isinstance(obj, SequenceObject))
        self.conditional.remove(obj)

    def __len__(self):
        return len(self.conditional)

    def __getitem__(self, x):
        return self.conditional[x]

    def dump(self):
        for i in self.conditional:
            i.dump()

        print self.packet.get_protocol_str()

    def get_length(self):
        tot = 1

        for i in self.conditional:
            tot += i.get_length()

        return tot

class SequencePacket(object):
    def __init__(self):
        self.list = []

    def append(self, obj):
        assert (isinstance(obj, SequenceObject))
        self.list.append(obj)

    def insert(self, idx, obj):
        assert (isinstance(obj, SequenceObject))
        self.list.insert(idx, obj)

    def remove(self, obj):
        assert (isinstance(obj, SequenceObject))
        self.list.remove(obj)

    def __len__(self):
        return len(self.list)

    def __getitem__(self, x):
        return self.list[x]

    def dump(self):
        for i in self.list:
            i.dump()

    def get_length(self):
        tot = 0

        for i in self.list:
            tot += i.get_length()

        return tot

def register_static_context(context_class):
    "Override this to create your own StaticContext"

    log.debug("StaticContext not overloaded")
    return context_class

def register_timed_context(context_class):
    "Override this to create your own TimedContext"

    log.debug("TimedContext not overloaded")
    return context_class

def register_send_context(context_class):
    "Override this to create your own SendContext"

    log.debug("SendContext not overloaded")
    return context_class

def register_send_receive_context(context_class):
    "Override this to create your own SendReceiveContext"

    log.debug("SendReceiveContext not overloaded")
    return context_class

def register_sniff_context(context_class):
    "Override this to create your own SniffContext"

    log.debug("SniffContext not overloaded")
    return context_class

def register_sequence_context(context_class):
    "Override this to create your own SequenceContext"

    log.debug("SequenceContext not overloaded")
    return context_class

from PM.Manager.PreferenceManager import Prefs

if Prefs()['backend.system'].value.lower() == 'umpa':
    from PM.Backend.UMPA.Context import *
else:
    from PM.Backend.Scapy.Context import *
