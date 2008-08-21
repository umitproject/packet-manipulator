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
from PM.Backend.Abstract.Context import register_sequence_context

class BaseSequenceContext(TimedContext):
    def __init__(self, seq, count, inter, iface, \
                 scallback, rcallback, sudata=None, rudata=None):

        """
        Create a BaseSequenceContext object

        @param seq a Sequence object
        @param count the n of metapacket to send
        @param interval the interval between two consecutive send
        @param iface the interface to listen on for replies
        @param scallback the send callback to call at each send
        @param rcallback the recv callback to call at each recv
        @param sudata the user data for scallback
        @param rudata the user data for rcallback
        """

        self.seq = seq
        
        self.tot_loop_count = count
        self.loop_count = 0

        self.tot_packet_count = seq.get_length()
        self.packet_count = 0

        self.inter = float(inter) / 1000.0
        self.iface = iface
        self.scallback = scallback
        self.rcallback = rcallback
        self.sudata = sudata
        self.rudata = rudata

        self.answers = 0
        self.received = 0

        TimedContext.__init__(self)

SequenceContext = register_sequence_context(BaseSequenceContext)
