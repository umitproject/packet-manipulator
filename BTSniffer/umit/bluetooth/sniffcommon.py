#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
#
# Author: Quek Shu Yang <quekshuy@gmail.com>
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

MAX_SNIFF_TYPES = 16

#Frontline specific constants
FP_CLOCK_MASK = 0xFFFFFFF
FP_SLAVE_MASK = 0x02
FP_STATUS_SHIFT = 28
FP_TYPE_SHIFT = 3
FP_TYPE_MASK = 0xF
FP_ADDR_MASK = 7

FP_LEN_LLID_SHIFT = 2
FP_LEN_LLID_MASK = 3
FP_LEN_SHIFT = 5

LMP_TID_MASK = 1
LMP_OP1_SHIFT = 1

# Constants specific to our purposes
_FILTER_ALL = 7


try:
    from PM.Core.Logger import log
except ImportError:
    class log(object):
        
        @staticmethod
        def debug(debug_str):
            print debug_str

#class SniffSession(object):
#    """
#        Stores the state of the sniff session.
#        Attributes:
#            state (State), master (list), slave (list), 
#            device (string), dump (string), filter (int)
#            pindata (PinCrackData)
#    """
#    def __init__(self, state, master, slave, 
#                 device, dump, filter = _FILTER_ALL):
#        self.state = state
#        self.master, self.slave = master, slave
#        self.device, self.dump = device, dump        
#        self.filter = filter
#        self.pindata = None


