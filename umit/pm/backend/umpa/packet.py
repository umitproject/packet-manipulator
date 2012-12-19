#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
#
# Authors: Francesco Piccinno <stack.box@gmail.com>
#          Luís A. Bastião Silva <luis.kop@gmail.com> 
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

from datetime import datetime

from umit.pm.core.logger import log
from umit.pm.core.atoms import generate_traceback
from umit.pm.core.netconst import IL_TYPE_ETH, IL_TYPE_TR, IL_TYPE_FDDI, \
                             IL_TYPE_RAWIP, IL_TYPE_WIFI, IL_TYPE_COOK, \
                             IL_TYPE_PRISM

from umit.umpa import Packet
from umit.umpa.protocols import Payload
from umit.umpa.utils.exceptions import UMPAException

def get_proto_class_name(protok):
    return protok.__name__

def get_proto_name(proto_inst):
    return get_proto_class_name(proto_inst.__class__)

class MetaPacket:
    def __init__(self, proto=None):
        if isinstance(proto, Packet):
            self.root = proto
        else:
            self.root = Packet(proto, strict=False)
        self.time = "0"

    def insert(self, proto, layer):
        # Only append for the moment
        print "insert"
        if layer == -1:
            self.root.include(proto.root.protos[0])
            return True

        return False

    def get_raw(self):
        # XXX Implement _generate_value in umit/umpa/protocols/_fields.py
        try:
            raw = self.root.get_raw()
        except UMPAException:
            raw = ''
        return raw
    def complete(self):
        return False

    def get_protocol_str(self):
        assert self.root.protos, "No procols in Packet"
        return get_proto_name(self.root.protos[len(self.root.protos)-1])

    def summary(self):
        # We need to ask for a method here
        return "%s packet" % self.get_protocol_str()

    def get_size(self):
        return len(self.root.get_raw())
    
    def get_time(self):
        return str(self.time)

    def get_dest(self):
        try:
            dst = self.root.ip.dst
        except AttributeError:
            try:
                dst = self.root.ethernet.dst
            except:
                dst = "N/A"
        return dst
    

    def get_source(self):
        try:
            src = self.root.ip.src
        except AttributeError:
            try:
                src = self.root.ethernet.src
            except:
                src = "N/A"
        return src
        

    def get_protocols(self):
        return self.root.protos
    
    def get_protocol_bounds(self, proto_inst):
        "@return a tuple (start, len)"

        # XXX Do it
        return None
        
        #start = 0
        #proto = self.root

        #while isinstance(proto, Packet):
            #if isinstance(proto, NoPayload):
                #return None
            #elif proto_inst is proto:
                #return start, start + get_proto_size(proto_inst) / 8

            #start += get_proto_size(proto) / 8
            #proto = proto.payload
