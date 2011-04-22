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

from datetime import datetime

from umit.pm.core.logger import log
from umit.pm.core.atoms import generate_traceback
from umit.pm.core.netconst import IL_TYPE_ETH, IL_TYPE_TR, IL_TYPE_FDDI, \
                             IL_TYPE_RAWIP, IL_TYPE_WIFI, IL_TYPE_COOK, \
                             IL_TYPE_PRISM, LL_TYPE_ARP, \
                             NL_TYPE_TCP, NL_TYPE_UDP

from umit.pm.backend.scapy.translator import global_trans
from umit.pm.backend.scapy.wrapper import *


class MetaPacket(object):
    def __init__(self, proto=None, cfields=None, flags=0):
        self.root = proto
        self.cfields = cfields or {}
        self.flags = flags

        self.l2_proto = None
        self.l2_src = None
        self.l2_dst = None
        self.l2_len = 0

        self.l3_src = None
        self.l3_dst = None
        self.l3_proto = None
        self.l3_len = 0

        self.l4_src = None
        self.l4_dst = None
        self.l4_ack = 0
        self.l4_seq = 0
        self.l4_flags = 0
        self.l4_proto = 0
        self.l4_len = 0

        self.payload_len = 0

        self.inject = ''
        self.inject_len = 0
        self.inj_delta = 0

        self.data = ''
        self.data_len = 0

        self.session = None
        self.context = None

    def set_data_len(self, length):
        """
        This is used from the injection engine to set the correct payload
        string to transport protocols like TCP or UDP
        """
        value = self.data[:length]

        if self.l4_proto == NL_TYPE_TCP:
            self.root[TCP].payload = Raw(value)
            self.root[TCP].chksum = None
        elif self.l4_proto == NL_TYPE_UDP:
            self.root[UDP].payload = Raw(value)
            self.root[UDP].chksum = None

    def __div__(self, other):
        cfields = self.cfields.copy()
        cfields.update(other.cfields)

        return MetaPacket(self.root / other.root, cfields)

    def hashret(self):
        return self.root.hashret()

    def answers(self, other):
        return self.root.answers(other.root)

    @classmethod
    def new(cls, proto_name):
        try:
            klass = global_trans[proto_name][0]
            return MetaPacket(klass())
        except ValueError:
            log.error('Protocol %s not registered. Add it to global_trans')
            return None

    @classmethod
    def new_from_str(cls, proto_name, raw):
        try:
            klass = global_trans[proto_name][0]
            return MetaPacket(klass(raw))
        except:
            log.error('Could not create %s MetaPacket from %s' % \
                      (proto_name, repr(raw)))
            return None

    @classmethod
    def new_from_layer(cls, mpkt, proto_name):
        try:
            klass = global_trans[proto_name][0]
            return MetaPacket(mpkt.getlayer(klass))
        except ValueError:
            log.error('Protocol %s not registered. Add it to global_trans')
            return None

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

    def get_datetime(self):
        return datetime.fromtimestamp(self.root.time)

    def get_rawtime(self):
        return self.root.time

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

    def get_protocol_bounds(self, proto_inst):
        "@return a tuple (start, len)"

        start = 0
        proto = self.root

        while isinstance(proto, Packet):
            if isinstance(proto, NoPayload):
                return None
            elif proto_inst is proto:
                return start, start + get_proto_size(proto_inst) / 8

            start += get_proto_size(proto) / 8
            proto = proto.payload

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

                current = current.payload
                continue

            if field is not None:
                # We should look for field in the current protocol

                if field in current.fields_desc:
                    delattr(current, field.name)

                    # Ok. Let's return because we have reached our
                    # field!

                    return True
            else:
                # If we are here we should reset all the fields!
                # kill them all man!

                for k in current.fields.keys():
                    delattr(current, k)

            # If we have reached our proto we are sure that
            # we have resetted the selected fields correctly
            # at this point so it's safe to return

            if protocol_found:
                return True

            current = current.payload

        return False

    def haslayer(self, layer):
        return bool(self.root.haslayer(layer))

    def getlayer(self, layer):
        return self.root.getlayer(layer)

    def get_raw(self):
        return str(self.root)

    def get_raw_layer(self, layer):
        return str(self.getlayer(layer))

    def rebuild_from_raw_payload(self, newpayload):
        log.debug('Rebuilding packet starting from %s' % \
                  str(self.root.__class__))

        try:
            new_proto = self.root.__class__(newpayload)
            self.root = new_proto
            return True
        except Exception, err:
            log.debug('Rebuild from raw failed (%s)' % str(err))
            return False

    # standard functions
    def get_datalink(self):
        if isinstance(self.root, Ether):
            return IL_TYPE_ETH
        if isinstance(self.root, RadioTap):
            return IL_TYPE_WIFI
        return None

    def reset_field(self, fieldname):
        try:
            ret = fieldname.split('.')
            layer = self.root.getlayer(global_trans[ret[0]][0])

            if not layer:
                return None

            if len(ret) > 1:
                delattr(layer, ret[1])
            else:
                log.error('Cannot reset an entire protocol')

        except Exception, err:
            log.error('Error while resetting %s field. Traceback:' % \
                      fieldname)
            log.error(generate_traceback())

    def set_fields(self, proto, dict):
        try:
            layer = self.root.getlayer(global_trans[proto][0])

            if not layer:
                return None

            for key, value in dict.items():
                if isinstance(value, MetaPacket):
                    setattr(layer, key, value.root)
                else:
                    setattr(layer, key, value)

        except Exception, err:
            log.error('Error while setting %s fields to %s. Traceback:' % \
                      (dict, proto))
            log.error(generate_traceback())

    def set_field(self, fieldname, value):
        if isinstance(value, MetaPacket):
            value = value.root

        try:
            ret = fieldname.split('.')
            layer = self.root.getlayer(global_trans[ret[0]][0])

            if not layer:
                return None

            if len(ret) == 2:
                setattr(layer, ret[1], value)
            elif len(ret) == 3:
                val = getattr(layer, ret[1])

                if val is not None:
                    setattr(val, ret[2], value)
                else:
                    raise Exception('Middle value is None')
            else:
                log.error('Cannot set an entire protocol')

        except Exception, err:
            log.error('Error while setting %s field to %s. Traceback:' % \
                      (fieldname, repr(value)))
            log.error(generate_traceback())

    def get_fields(self, proto, tup):
        try:
            layer = self.root.getlayer(global_trans[proto][0])

            if not layer:
                return (None, ) * len(tup)

            out = []

            for key in tup:
                value = getattr(layer, key)

                if isinstance(value, Packet):
                    value = MetaPacket(value)

                out.append(value)

            return out
        except Exception, err:
            log.error('Error while getting %s fields from %s. Traceback:' % \
                      (tup, proto))
            log.error(generate_traceback())
            return (None, ) * len(tup)

    def get_field(self, fieldname, default=None):
        try:
            ret = fieldname.split('.')
            layer = self.root.getlayer(global_trans[ret[0]][0])

            if not layer:
                return default

            if len(ret) > 1:
                val = getattr(layer, ret[1])

                if len(ret) == 3 and val:
                    val = getattr(val, ret[2])

                if isinstance(val, Packet):
                    return MetaPacket(val)

                return val != None and val or default
            else:
                return str(layer)
        except Exception, err:
            log.error('Error while getting %s field. Traceback:' % fieldname)
            log.error(generate_traceback())
            return default

    def copy(self, full=False):
        if self.root:
            cpy = MetaPacket(self.root.copy(),
                             self.cfields.copy())
        if full:
            cpy.l2_proto = self.l2_proto
            cpy.l2_src = self.l2_src
            cpy.l2_dst = self.l2_dst
            cpy.l2_len = self.l2_len

            cpy.l3_src = self.l3_src
            cpy.l3_dst = self.l3_dst
            cpy.l3_proto = self.l3_proto
            cpy.l3_len = self.l3_len

            cpy.l4_src = self.l4_src
            cpy.l4_dst = self.l4_dst
            cpy.l4_ack = self.l4_ack
            cpy.l4_seq = self.l4_seq
            cpy.l4_flags = self.l4_flags
            cpy.l4_proto = self.l4_proto
            cpy.l4_len = self.l4_len

            cpy.payload_len = self.payload_len

            cpy.inject = self.inject
            cpy.inject_len = self.inject_len
            cpy.inj_delta = self.inj_delta

            cpy.data = self.data
            cpy.data_len = self.data_len

        return cpy

    def add_to(self, aft_proto, mpkt):
        self.root[global_trans[aft_proto][0]].payload = mpkt.root

    # Custom fields

    def get_cfield(self, name):
        return self.cfields[name]

    def set_cfield(self, name, val):
        self.cfields[name] = val

    def unset_cfield(self, name):
        del self.cfields[name]
