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

from Backend.Scapy.packet import MetaPacket
from Backend.Scapy.wrapper import rdpcap, wrpcap

from umitCore.I18N import _

def register_static_context(BaseStaticContext):

    class StaticContext(BaseStaticContext):
        def load(self):
            if not self.cap_file:
                return False

            try:
                data = rdpcap(self.cap_file)
            except IOError, (errno, err):
                self.summary = str(err)
                return False

            self.data = []
            for packet in data:
                self.data.append(MetaPacket(packet))

            self.status = self.SAVED
            self.title = self.cap_file
            self.summary = _('%d packets loaded.') % len(data)
            return True

        def save(self):
            if getattr(self, 'get_all_data', False):
                data = self.get_all_data()
            else:
                data = self.get_data()

            if not self.cap_file and not data:
                return False

            data = [packet.root for packet in data]
            try:
                wrpcap(self.cap_file, data, gz=('gz' in self.cap_file) and (1) or (0))
            except IOError, (errno, err):
                self.summary = str(err)
                return False

            self.status = self.SAVED
            self.title = self.cap_file
            self.summary = _('%d packets written.') % len(data)
            return True

    return StaticContext
