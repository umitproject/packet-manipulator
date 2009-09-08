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

from timed import TimedContext
from umit.pm.backend.abstract.context import register_send_context

class BaseSendContext(TimedContext):
    "A context to only send packets"

    def __init__(self, metapacket, count, inter, iface, callback, udata=None):
        """
        Create a BaseSendContext object

        @param metapacket the packet to send
        @param count the n metapacket to send
        @param inter the interval of time between two consecutive send
        @param iface the interface to use for sending
        @param callback the function to call at every send
        @param udata the user data to pass to callback
        """

        self.packet = metapacket
        self.tot_count = count
        self.count = 0
        self.inter = float(inter) / 1000.0
        self.iface = iface
        self.callback = callback
        self.udata = udata

        TimedContext.__init__(self)

SendContext = register_send_context(BaseSendContext)
