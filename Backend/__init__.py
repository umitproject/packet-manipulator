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
from umpa.protocols._ import Protocol

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

def get_proto_name(proto_inst):
    return proto_inst.__class__.__name__

def get_field_name(field):
    return field.name

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

class VirtualIFace:
    def __init__(self, name, desc, ip):
        self.name = name
        self.description = desc
        self.ip = ip

def find_all_devs():
    "@return a list of avaiable devices to sniff from (use generators)"
    
    # TODO: implement real code
    
    for i in (VirtualIFace("eth0", "Ethernet", "192.168.1.0"),
               VirtualIFace("wlan0", "Wireless", "172.16.0.1")):
        yield i

gprotos = load_gprotocols()
