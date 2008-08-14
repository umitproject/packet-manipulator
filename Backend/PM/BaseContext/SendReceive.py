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

from Timed import TimedContext
from Backend.PM.Context import register_send_receive_context

class BaseSendReceiveContext(TimedContext):
    "This should be a derived class of TimedContext"

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

        TimedContext.__init__(self)

SendReceiveContext = register_send_receive_context(BaseSendReceiveContext)
