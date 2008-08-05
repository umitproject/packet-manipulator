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

import os, os.path

from umpa import protocols
from umpa.packets import Packet
from umpa.protocols import Protocol
from umpa.protocols._fields import *

from inspect import isclass

# Globals UMPA protocols
gprotos = []

# Locals User defined protocols
lprotos = []

# We need to get all the protocols from the __path__
# of protocols and also import the protocols defined
# by the user from the .umit/umpa/ directory

def load_gprotocols():
    path = protocols.__path__[0]
    glob = []

    for fname in os.listdir(path):
        if not fname.lower().endswith(".py") or fname[0] == "_":
            continue

        try:
            # We'll try to load this
            module = __import__(
                "%s.%s" % (protocols.__name__, fname.replace(".py", "")),
                fromlist=[protocols]
            )

            glob.extend(
                filter(lambda x: not isinstance(x, Protocol), module.protocols)
            )

        except Exception, err:
            print "Ignoring exception", err

    return glob

def get_protocols():
    """
    @return a list of type [(Protocol, name)]
    """
    return gprotos

def get_proto(proto_name):
    for proto in gprotos:
        if proto.__name__ == proto_name:
            return proto

    for proto in lprotos:
        if proto.__name__ == proto_name:
            return proto

    print "Protocol named %s not found." % proto_name
    return None

def get_proto_class_name(protok):
    return protok.__name__

def get_proto_name(proto_inst):
    return get_proto_class_name(proto_inst.__class__)

# Fields section

def get_field_name(field):
    return field.name

def get_field_value(proto, field):
    return field.get()

def set_field_value(proto, field, value):
    field.set(value)

def get_field_value_repr(proto, field):
    ret = get_field_value(proto, field)
    out = ""

    if isinstance(ret, dict):
        for it in ret:
            if ret[it].get():
                out += "+%s" % it 

        return out[1:]

    if isinstance(ret, (list, tuple)):
        for it in ret:
            out += "+%s" % it

        return out[1:]

    return str(ret)

def get_field_size(proto, field):
    return field.bits

def get_field_offset(proto, field):
    return proto.get_offset(field)

def get_field_enumeration_s2i(field):
    return field.enumerable.items()

def get_field_enumeration_i2s(field):
    return [(v, k) for (k, v) in field.enumerable.items()]

def get_keyflag_value(proto, flag, key):
    return flag.get()[key].get()

def set_keyflag_value(proto, flag, key, value):
    return flag.get()[key].set(value)

def is_field_autofilled(field):
    return field.auto

def get_field_desc(field):
    return field.__doc__

def get_flag_keys(flag_inst):
    for key in flag_inst._ordered_fields:
        yield key

def get_field_key(proto_inst, field_inst):
    for key in proto_inst.__class__.get_fields_keys():
        if field_inst == getattr(proto_inst, key, None):
            return key

    return None

def get_proto_fields(proto_inst):
    return proto_inst.get_fields()

def get_packet_protos(packet):
    for proto in packet.root.protos:
        yield proto

def get_proto_layer(proto):
    return proto.layer

def get_packet_raw(metapack):
    return metapack.root.get_raw()

# Checking stuff

def is_field(field):
    return isinstance(field, Field)

def is_flags(field):
    return isinstance(field, Flags)

def is_proto(proto):
    return isinstance(proto, Protocol)

def implements(obj, klass):
    return isinstance(obj, klass)


class MetaPacket:
    def __init__(self, proto=None):
        self.root = Packet(proto)

    def include(self, proto):
        self.root.include(proto)

from Backend import VirtualIFace

def find_all_devs():
    "@return a list of avaiable devices to sniff from"
    return []


gprotos = load_gprotocols()

PMField = Field
PMFlagsField = Flags

PMBitField          = BitField
PMIPField           = IPv4AddrField
PMByteField         = None
PMShortField        = None
PMLEShortField      = None
PMIntField          = IntField
PMSignedIntField    = None
PMLEIntField        = None
PMLESignedIntField  = None
PMLongField         = None
PMLELongField       = None
PMStrField          = None
PMLenField          = None
PMRDLenField        = None
PMFieldLenField     = None
PMBCDFloatField     = None
PMEnumField         = EnumField
