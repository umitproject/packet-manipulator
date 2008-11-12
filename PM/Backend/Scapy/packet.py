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

from PM.Backend.Scapy.wrapper import Packet, NoPayload, Raw, Ether, IP

class MetaPacket:
    def __init__(self, proto=None):
        self.root = proto

    def insert(self, proto, layer):
        if layer == -1:
            # Append
            packet = self.root / proto.root
            self.root = packet

            return True
        else:
            # We have to insert proto at position layer

            first = None
            last = self.root

            while layer > 0 and last:
                first = last
                last = last.payload
                layer -= 1

            ret = proto.root / last

            if first:
                first.payload = ret
            else:
                self.root = ret

            return True
    def complete(self):
        # Add missing layers (Ethernet and IP)

        if not self.root.haslayer(Ether):
            if not self.root.haslayer(IP):
                self.root = IP() / self.root

            self.root = Ether() / self.root
            
            return True

        return False

    def remove(self, rproto):
        first = None
        last = self.root

        if isinstance(self.root.payload, NoPayload):
            return False

        while isinstance(last, Packet):

            if last == rproto:
                if first:
                    first.payload = last.payload
                else:
                    self.root = last.payload

                return True

            first = last
            last = last.payload

        return False

    def get_size(self):
        return len(str(self.root))

    def summary(self):
        return self.root.summary()

    def get_time(self):
        #self.root.time
        return self.root.sprintf("%.time%")

    def get_source(self):
        ip = self.root.sprintf("{IP:%IP.src%}")
        hw = self.root.sprintf("{Ether:%Ether.src%}")

        if ip:
            return ip

        if hw:
            return hw

        return "N/A"

    def get_dest(self):
        ip = self.root.sprintf("{IP:%IP.dst%}")
        hw = self.root.sprintf("{Ether:%Ether.dst%}")

        if ip:
            return ip

        if hw:
            return hw

        return "N/A"

    def get_protocol_str(self):
        proto = self.root

        while isinstance(proto, Packet):
            if isinstance(proto.payload, NoPayload) or \
               isinstance(proto.payload, Raw):
                return proto.name

            proto = proto.payload
    
    def get_protocols(self):
        "@returns a list containing the name of protocols"

        lst = []
        proto = self.root

        while isinstance(proto, Packet):
            if isinstance(proto, NoPayload):
                break

            lst.append(proto)

            proto = proto.payload

        return lst
    
    def reset(self, protocol=None, startproto=None, field=None):
        """
        Reset the packet

        @param protocol the protocol to reset or None to match all
        @param startproto the start protocolo to start from
        @param field the field to reset or None to match all
        @return True if reset is ok or False
        """

        protocol_found = False
        current = (startproto is not None) and (startproto) or (self.root)

        while isinstance(current, Packet) and \
              not isinstance(current, NoPayload):

            if protocol is not None and \
               protocol is current:
                protocol_found = True

            elif protocol is not None and not protocol_found:
                # We could skip the entire body of function because
                # proto filtering is active and the current is not
                # the target protocol.

                current = find.payload
                continue

            if field is not None:
                # We should look for field in the current protocol

                if field in current.fields_desc:
                    delattr(current, field.name)

                    # Ok. Let's return because we have reached our
                    # field!

                    return
            else:
                # If we are here we should reset all the fields!
                # kill them all man!
                
                for k in current.fields.keys():
                    delattr(current, k)

            # If we have reached our proto we are sure that
            # we have resetted the selected fields correctly 
            # at this point so it's safe to return

            if protocol_found:
                return

            current = current.payload
    
    def haslayer(self, layer):
        return bool(self.root.haslayer(layer))

    def getlayer(self, layer):
        return self.root.getlayer(layer)

    def get_raw(self):
        return str(self.root)
