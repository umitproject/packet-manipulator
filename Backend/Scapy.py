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
from scapy import *

def load_scapy_protocols():
    import __builtin__
    all = __builtin__.__dict__.copy()
    all.update(globals())
    objlst = filter(lambda (n,o): isinstance(o,type) and issubclass(o,Packet), all.items())
    objlst.sort(lambda x,y:cmp(x[0],y[0]))

    ret = []

    for n,o in objlst:
        ret.append(o)

    return ret

gprotos = load_scapy_protocols()

def get_protocols():
    return gprotos

def get_proto_class_name(protok):
    if not protok.name or protok.name == "":
        return protok.__name__

    return protok.name

def get_proto_name(proto_inst):
    return get_proto_class_name(proto_inst)

def get_proto(proto_name):
    for proto in gprotos:
        if proto.name == proto_name:
            return proto
        if proto.__name__ == proto_name:
            return proto

    print "Protocol named %s not found." % proto_name
    return None

def get_proto_layer(proto):
    return None


def get_packet_raw(metapack):
    if metapack.root:
        return str(metapack.root)
    else:
        return ""

def get_proto_fields(proto_inst):
    if isinstance(proto_inst, type) and isinstance(proto_inst, Packet):
        for f in proto_inst.fields_desc:
            yield f

    elif isinstance(proto_inst, Packet):
        for f in proto_inst.fields_desc:
            yield f

        if not isinstance(proto_inst.payload, NoPayload):
            get_proto_fields(proto_inst.payload)

def get_field_desc(field):
    if not field:
        return "No description"

    return field.__class__.__name__

def get_packet_protos(metapack):
    if not metapack.root:
        raise StopIteration

    obj = metapack.root

    while isinstance(obj, Packet):
        yield obj

        if not isinstance(obj.payload, NoPayload):
            obj = obj.payload
        else:
            raise StopIteration

class MetaPacket:
    def __init__(self, proto=None):
        self.root = proto

    def include(self, proto):
        if self.root:
            self.root = self.root / proto
        else:
            self.root = proto

print ">>> %d protocols registered." % len(gprotos)


# Fields section

def get_field_name(field):
    return field.name

def get_field_value(proto, field):
    return getattr(proto, field.name)

def set_field_value(proto, field, value):
    return setattr(proto, field.name, value)

def get_field_value_repr(proto, field):
    return field.i2repr(proto, getattr(proto, field.name))

def get_field_size(proto, field):
    if hasattr(field, 'size'):
        return field.size
    else:
        return field.sz * 8

def get_field_offset(proto, field):
    bits = 0

    for f in proto.fields_desc:
        if f == field:
            break

        bits += get_field_size(proto, f)

    return bits

def get_field_enumeration_s2i(field):
    return field.s2i.items()

def get_field_enumeration_i2s(field):
    return field.i2s.items()

def set_keyflag_value(proto, flag, key, value):
    if value == get_keyflag_value(proto, flag, key):
        return
    else:
        ret = get_field_value_repr(proto, flag)
        
        if flag.multi:
            if value:
                ret += "+" + key
            else:
                ret = ret.replace(key, "").replace("++", "+")

            if ret and ret[0] == '+':
                ret = ret[1:]
            if ret and ret[-1] == '+':
                ret = ret[:len(ret)-1]

            set_field_value(proto, flag, ret)
        else:
            if value:
                set_field_value(proto, flag, "%s%s" % (ret, key))
            else:
                set_field_value(proto, flag, ret.replace(key, ""))


def get_keyflag_value(proto, flag, key):
    return key in get_field_value_repr(proto, flag)

def is_field_autofilled(field):
    # If the field is setted to None it's calculated
    # automatically
    return field.default == None

def get_flag_keys(field):
    assert isinstance(field, FlagsField)

    if field.multi:
        return map(lambda x: x[0], field.names)
    else:
        return list(field.names)

# Checking stuff

def is_field(field):
    if isinstance(field, Emph):
        return True

    return isinstance(field, Field)

def is_flags(field):
    return isinstance(field, FlagsField)

def is_proto(proto):
    return isinstance(proto, Packet)

def implements(obj, klass):
    if isinstance(obj, Emph):
        return isinstance(obj.fld, klass)

    return isinstance(obj, klass)

# Sniff stuff

from Backend import VirtualIFace

def find_all_devs():
    ifaces = get_if_list()

    ips = []
    hws = []
    for iface in ifaces:
        ip = "0.0.0.0"
        hw = "00:00:00:00:00:00"
        
        try:
            ip = get_if_addr(iface)
        except Exception:
            pass

        try:
            hw = get_if_hwaddr(iface)
        except Exception:
            pass

        ips.append(ip)
        hws.append(hw)

    ret = []
    for iface, ip, hw in zip(ifaces, ips, hws):
        ret.append(VirtualIFace(iface, hw, ip))

    return ret

# Routes stuff

PMField             = Field
PMFlagsField        = FlagsField

PMBitField          = None
PMIPField           = IPField
PMByteField         = ByteField
PMShortField        = ShortField
PMLEShortField      = LEShortField
PMIntField          = IntField
PMSignedIntField    = SignedIntField
PMLEIntField        = LEIntField
PMLESignedIntField  = LESignedIntField
PMLongField         = LongField
PMLELongField       = LELongField
PMStrField          = StrField
PMLenField          = LenField
PMRDLenField        = RDLenField
PMFieldLenField     = FieldLenField
PMBCDFloatField     = BCDFloatField
PMBitField          = BitField
PMEnumField         = EnumField
