#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
#
# Author: Abhiram Kasina <abhiram.casina@gmail.com>
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

import sys, os, os.path
import gtk, gobject

from umit.pm.core.i18n import _
from umit.pm.backend import MetaPacket
from umit.pm.backend.scapy import *

class Filter():
    
    def __init__(self, filter):
        self.filter_string = filter
        
    
    def is_packet_valid(self, packet):
        g = Tokenizer(self.filter_string, ' ')
        while True :
            left = g.next()
            if left == '':
                break
            if left == 'ip.src' or \
               left == 'ip.dst' or \
               left == 'tcp.flags':
                token = g.next()
                if token == '':
                    break
                if token == '==':
                    token = g.next()
                    if token == '':
                        break
                    if str(packet.get_field(left)) != token:
                        return False
                    else:
                        token = g.next()
                        if token == '':
                            return True
                        if token == 'and':
                            continue
                        else :
                            break
        return False
                    
                    
        

class Tokenizer():
    
    def __init__ (self, mstring, delimiter):
        self.mstring = str(mstring)
        self.tokens = self.mstring.split()
        self.index = 0
    
    def next(self):
        if self.index < len(self.tokens):
            self.index = self.index+1
            return self.tokens[self.index-1]
        return ''
    
        
    
if __name__ == "__main__":
    f = Filter("ip.dst  ==")
    m = MetaPacket(Ether() / IP(dst = '144.16.192.247') /  TCP(flags = 'SA'))
    print m.get_field('tcp.flags')
    print f.is_packet_valid(m)
    