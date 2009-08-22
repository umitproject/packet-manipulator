#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
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
from threading import Thread

import umpa
import umpa.utils.security

from umpa import protocols
from umpa import Packet
from umpa.protocols._protocols import Protocol
from umpa.protocols._fields import *

from umpa.extensions.XML import load as xml_load
from umpa.extensions.XML import save as xml_save

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

gprotos = load_gprotocols()

###############################################################################
# Protocols functions
###############################################################################
def get_protocols():
    return gprotos

def get_proto_class_name(protok):
    return protok.__name__

def get_proto_name(proto_inst):
    return get_proto_class_name(proto_inst.__class__)

def get_proto(proto_name):
    for proto in gprotos:
        if proto.__name__ == proto_name:
            return proto

    for proto in lprotos:
        if proto.__name__ == proto_name:
            return proto

    print "Protocol named %s not found." % proto_name
    return None

def get_proto_layer(proto):
    return proto.layer

def get_proto_fields(proto_inst):
    return proto_inst.get_fields()

###############################################################################
# Packet functions
###############################################################################

def get_packet_protos(packet):
    for proto in packet.root.protos:
        yield proto

def get_packet_raw(metapack):
    return metapack.root.get_raw()

###############################################################################
# Fields functions
###############################################################################

def get_field_desc(field):
    return field.__doc__

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

def get_field_offset(packet, proto, field):
    return proto.get_offset(field)

def get_field_enumeration_s2i(field):
    return field.enumerable.items()

def get_field_enumeration_i2s(field):
    return [(v, k) for (k, v) in field.enumerable.items()]

def is_field_autofilled(field):
    return field.auto

###############################################################################
# Flag fields functions
###############################################################################

def set_keyflag_value(proto, flag, key, value):
    return flag.get()[key].set(value)

def get_keyflag_value(proto, flag, key):
    return flag.get()[key].get()

def get_flag_keys(flag_inst):
    for key in flag_inst._ordered_fields:
        yield key

###############################################################################
# Checking functions
###############################################################################

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
        self.root = Packet(proto, strict=False)

    def insert(self, proto, layer):
        # Only append for the moment
        if layer == -1:
            self.root.include(proto.root.protos[0])
            return True

        return False

    def get_raw(self):
        return get_packet_raw(self)

    def complete(self):
        return False

    def get_protocol_str(self):
        assert self.root.protos, "No procols in Packet"
        return get_proto_name(self.root.protos[0])

    def summary(self):
        # We need to ask for a method here
        return "%s packet" % self.get_protocol_str()

    def get_time(self):
        # We need to ask for a method here
        return "N/A"

    def get_dest(self):
        # We need to ask for a method here
        return "N/A"

    def get_source(self):
        # We need to ask for a method here
        return "N/A"

    def get_protocols(self):
        return self.root.protos

###############################################################################
# Functions used by Contexts
###############################################################################

def _send_packet(metapacket, count, inter, callback, udata):
    try:
        sock = umpa.utils.security.super_priviliges(umpa.Socket)
        packet = metapacket.root

        while count > 0:
            sock.send(packet)
            count -= 1

            if callback(metapacket, udata) == True:
                return

            time.sleep(inter)

    except OSError, (errno, err):
        callback(Exception(err), udata)
        return

    callback(None, udata)

def send_packet(metapacket, count, inter, callback, udata=None):
    """
    Send a metapacket in thread context

    @param metapacket the packet to send
    @param count send n count metapackets
    @param inter interval between two consecutive sends
    @param callback a callback to call at each send (of type packet, udata)
           when True is returned the send thread is stopped
    @param udata the userdata to pass to the callback
    """
    send_thread = Thread(target=_send_packet, args=(metapacket, count, inter, callback, udata))
    send_thread.setDaemon(True) # avoids zombies
    send_thread.start()

    return send_thread

###############################################################################
# Functions used by dialogs but not defined
###############################################################################

def find_all_devs():
    return []

def route_resync():
    pass

def route_list():
    return []

def route_add(self, host, net, gw, dev):
    pass

def route_remove(self, host, net, gw, dev):
    pass

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
