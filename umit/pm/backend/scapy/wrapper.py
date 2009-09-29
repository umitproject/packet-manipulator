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

import os
import sys
import select as selectmod

__original_write = os.write

def __new_write(fd, txt):
    if fd == 1:
        sys.stdout.write(txt)
    else:
        __original_write(fd, txt)

os.write = __new_write

__original_select = selectmod.select

if os.name != 'nt' and not os.getenv('PM_NOSCAPYWORKAROUND', ''):

    def __intr_select(_in, _out, _err, timeout=2):
        while True:
            try:
                return __original_select(_in, _out, _err, timeout)
            except selectmod.error, (ec, es):
                if ec == 4: # EINTR
                    continue
                else:
                    raise

    selectmod.select = __intr_select

PM_USE_NEW_SCAPY = False
DARWIN, NETBSD, OPENBSD, FREEBSD = False, False, False, False

try:
    from scapy import *

    if 'conf' not in globals():
        from scapy.all import *
        PM_USE_NEW_SCAPY = True

except ImportError:
    from umit.pm.core.errors import PMErrorException
    raise PMErrorException(
        "Cannot use this backend without scapy installed.\n\n"
        "Get a copy from http://www.secdev.org/projects/scapy/"
    )

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.manager.preferencemanager import Prefs

if not 'WINDOWS' in globals():
    WINDOWS = False

def change_interface(iface):
    if iface:
        conf.iface = iface

conf.color_theme = NoTheme()
Prefs()['backend.scapy.interface'].connect(change_interface)

###############################################################################
# Protocols loading
###############################################################################

def load_scapy_protocols():
    import __builtin__
    all = __builtin__.__dict__.copy()
    all.update(globals())
    objlst = filter(lambda (n,o): isinstance(o,type) and issubclass(o,Packet), \
                    all.items())
    objlst.sort(lambda x,y:cmp(x[0],y[0]))

    ret = []

    for n,o in objlst:
        ret.append(o)

    return ret

# We use this global variable to track protocols
gprotos = load_scapy_protocols()

log.debug("%d protocols registered." % len(gprotos))

###############################################################################
# Protocols functions
###############################################################################

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
    return getattr(proto, '_pm_layer', None)

def get_proto_fields(proto_inst):
    if isinstance(proto_inst, type) and isinstance(proto_inst, Packet):
        for f in proto_inst.fields_desc:
            yield f

    elif isinstance(proto_inst, Packet):
        for f in proto_inst.fields_desc:
            yield f

        if not isinstance(proto_inst.payload, NoPayload):
            get_proto_fields(proto_inst.payload)

def get_proto_size(proto_inst):
    """@return the size of the entire protocol in bits"""
    size = 0

    for field in get_proto_fields(proto_inst):
        size += get_field_size(proto_inst, field)

    return size

def get_proto_field(proto_inst, name):
    for f in get_proto_fields(proto_inst):
        if f.name == name:
            return f

###############################################################################
# Packet functions
###############################################################################

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

def get_packet_raw(metapack):
    if metapack.root:
        return str(metapack.root)
    else:
        return ""

###############################################################################
# Fields functions
###############################################################################

def get_field_desc(field):
    if not field:
        return _('No description')

    if field.__doc__:
        return field.__doc__
    else:
        return field.__class__.__name__

def get_field_name(field):
    return field.name

def get_field_value(proto, field):
    return getattr(proto, field.name)

def set_field_value(proto, field, value):
    return setattr(proto, field.name, value)

def get_field_value_repr(proto, field):
    return field.i2repr(proto, getattr(proto, field.name))

def get_field_size(proto, field):
    if isinstance(field, StrField):
        try:
            # We have to manage in a different way the StrField
            return field.i2len(proto, getattr(proto, field.name)) * 8
        except TypeError:
            return len(field.i2m(proto, getattr(proto, field.name)))
        #return len(field.i2m(proto, getattr(proto, field.name))) * 8

    if hasattr(field, 'size'):
        return field.size
    else:
        return field.sz * 8

def get_field_offset(packet, proto, field):
    bits = 0

    child = packet.root

    while not isinstance(child, NoPayload) and proto != child:
        for f in child.fields_desc:
            bits += get_field_size(child, f)

        child = child.payload

    for f in child.fields_desc:
        if field == f:
            return bits

        bits += get_field_size(child, f)

    raise Exception('Field or protocol is not present in the packet')

def get_field_enumeration_s2i(field):
    return field.s2i.items()

def get_field_enumeration_i2s(field):
    try:
        return field.i2s.items()
    except AttributeError:
        # Triggered on fields like ICMP.code
        return map(lambda x: (x[1], x[0]), field.s2i_all.items())

def is_field_autofilled(field):
    # If the field is setted to None it's calculated
    # automatically
    return field.default == None

def is_default_field(proto_inst, field):
    return get_field_value(proto_inst, field) == field.default

###############################################################################
# Flag fields functions
###############################################################################

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

def get_flag_keys(field):
    assert isinstance(field, FlagsField)

    if field.multi:
        return map(lambda x: x[0], field.names)
    else:
        return list(field.names)

###############################################################################
# Checking functions
###############################################################################

def is_field(field):
    if isinstance(field, Emph):
        return True

    return isinstance(field, (Field, ConditionalField))

def is_flags(field):
    return isinstance(field, FlagsField)

def is_proto(proto):
    return isinstance(proto, Packet)

def implements(obj, klass):
    if isinstance(obj, (Emph, ConditionalField)):
        return isinstance(obj.fld, klass)

    return isinstance(obj, klass)

def is_showable_field(field, metapkt):
    if not isinstance(field, ConditionalField):
        return True

    return field._evalcond(metapkt.root)
