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

from base64 import b64decode, b64encode

from xml.sax import handler, make_parser
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl

from umit.pm.core.atoms import Node, generate_traceback
from umit.pm.core.logger import log

from umit.pm.backend.scapy import *
from umit.pm.backend import SequencePacket

class SequenceLoader(handler.ContentHandler):
    def __init__(self, fname):
        self.fname = fname

        self.in_node = False
        self.in_packet = False

        # Various attributes
        self.packet_interval = None
        self.packet_filter = None

        self.attr_strict = None
        self.attr_sent = None
        self.attr_recv = None
        self.attr_loopcnt = None
        self.attr_inter = None

        # Variables used to track document
        self.in_proto = False
        self.protocol = None
        self.current_protocol = None
        self.in_field = False
        self.field_id = False
        self.field_value = None

        self.tree = Node()
        self.current_node = self.tree
        self.tree_len = 0

        handler.ContentHandler.__init__(self)

    def parse(self):
        parser = make_parser()
        parser.setContentHandler(self)
        parser.parse(self.fname)
        parser.close()
        parser.reset()

        return self.tree

    def parse_async(self):
        """
        @attention Use try/except for this function
        the functions will be iterable and at every iteration will return a
        tuple of the type (tree, pktidx, percentage of loading, fsize)
        """
        parser = make_parser()
        parser.setContentHandler(self)

        position = 0
        fd = open(self.fname, 'r')
        fd.seek(0, 2)
        size = float(fd.tell())
        fd.seek(0)

        for data in fd:
            parser.feed(data)
            position += len(data)

            yield self.tree, self.tree_len, (position / size) * 100.0, size

        parser.close()
        parser.reset()

    def add_pending(self):
        if self.current_protocol:

            if self.protocol:
                self.protocol = self.protocol / self.current_protocol
            else:
                self.protocol = self.current_protocol

            self.protocol.time = self.current_protocol.time

            self.current_node.data.packet = MetaPacket(self.protocol)
            self.protocol = self.current_protocol = None

    def startElement(self, name, attrs):
        if name == 'PMScapySequence':
            self.in_sequence = True

            try:
                self.attr_loopcnt = int(attrs['loopcnt'])
                self.attr_inter = float(attrs['inter'])

                self.attr_recv = int(attrs['report_recv']) != 0
                self.attr_sent = int(attrs['report_sent']) != 0
                self.attr_strict = int(attrs['strict']) != 0
            except Exception:
                if not isinstance(self.attr_loopcnt, int):
                    self.attr_loopcnt = 1
                if not isinstance(self.attr_inter, (float, int)):
                    self.attr_inter = 500
                if not isinstance(self.attr_recv, bool):
                    self.attr_recv = False
                if not isinstance(self.attr_sent, bool):
                    self.attr_sent = True
                if not isinstance(self.attr_strict, bool):
                    self.attr_strict = True

        elif self.in_sequence and name == 'SequencePacket':

            self.add_pending()

            try:
                self.packet_interval = eval(attrs['interval']) or 0
                self.packet_filter = attrs['filter']

                node = Node(SequencePacket(None,
                                           self.packet_interval,
                                           self.packet_filter))

                self.current_node.append_node(node)
                self.current_node = node

                self.tree_len += 1

            except Exception, err:
                log.debug(generate_traceback())
            else:
                self.in_packet = True

        elif self.in_packet and name == 'proto':
            try:
                proto_id = attrs['id']
                proto_time = eval(attrs['time'])

                protocol = get_proto(proto_id)()
                protocol.time = proto_time

                if self.current_protocol is not None:

                    if self.protocol is not None:
                        self.protocol = self.protocol / self.current_protocol
                    else:
                        self.protocol = self.current_protocol

                self.current_protocol = protocol
            except Exception, err:
                log.debug(generate_traceback())
            else:
                self.in_proto = True
        elif self.in_proto and name == 'field':
            try:
                self.field_id = attrs['id']
            except Exception, err:
                log.error('Field seems to not have id attribute')
            else:
                self.in_field = True

    def endElement(self, name):
        if name == 'PMScapySequence':
            self.in_sequence = self.in_packet = \
                self.in_proto = self.in_field = False

            self.packet_interval = self.packet_filter = self.protocol = \
                self.field_id = self.field_value = None

        elif name == 'SequencePacket':
            self.add_pending()

            self.current_node = self.current_node.get_parent() or self.tree

            self.in_packet = self.in_proto = self.in_field = False
            self.packet_interval = self.packet_filter = self.protocol = \
                self.current_protocol = self.field_id = self.field_value = None

        elif name == 'proto':
            self.in_proto = self.in_field = False
            self.field_id = self.field_value = None
        elif name == 'field':
            self.in_field = False
            self.field_id = self.field_value = None

    def characters(self, content):
        if self.in_field and self.field_id and self.current_protocol:
            self.field_value = content
            value = b64decode(self.field_value)

            try:
                # TODO: Not so secure. Here we could have some kind of backdoor
                value = eval(value)
            except:
                pass

            field = get_proto_field(self.current_protocol, self.field_id)

            if field:
                set_field_value(self.current_protocol, field, value)
            else:
                log.warning("Field %s is not present in %s protocol. Probably "
                            "you are loading a sequence created with a newer "
                            "scapy version" % (self.field_id,
                                               type(self.current_protocol)))

class SequenceWriter(object):
    def __init__(self, fname, sequence, strict, report_recv, report_sent, \
                 loopcnt, inter):

        self.fname = fname
        self.seq = sequence

        self.attr_loopcnt = loopcnt
        self.attr_inter = inter

        self.attr_strict = strict
        self.attr_recv = report_recv
        self.attr_sent = report_sent

    def save(self):
        for i in self.save_async():
            pass

    def save_async(self):
        output = open(self.fname, 'w')

        self.depth_idx = 0
        self.writer = XMLGenerator(output, 'utf-8')

        self.writer.startDocument()

        attr_vals = {'report_recv' : (self.attr_recv) and '1' or '0',
                     'report_sent' : (self.attr_sent) and '1' or '0',
                     'strict' : (self.attr_strict) and '1' or '0'}

        if isinstance(self.attr_loopcnt, int):
            attr_vals['loopcnt'] = str(self.attr_loopcnt)
        if isinstance(self.attr_inter, (float, int)):
            attr_vals['inter'] = str(self.attr_inter)

        attrs = AttributesImpl(attr_vals)

        self.startElement('PMScapySequence', attrs)

        self.current_node = None

        idx = 0
        slen = float(len(self.seq))

        for node in self.seq.get_children():
            self.current_node = node
            self.write_node(node)

            idx += 1
            yield idx, (idx / slen) * 100.0, output.tell()

        self.current_node = None

        self.endElement('PMScapySequence')

        self.writer.endDocument()
        output.close()

    def writeSpaces(self, prepend='', append=''):
        idx = max(self.depth_idx - 1, 0)
        txt = '%s%s%s' % (prepend, '  ' * idx, append)

        if txt:
            self.writer.characters(txt)

    def startElement(self, name, attrs, indent=True):
        if indent:
            self.writer.characters('\n')

        self.depth_idx += 1

        self.writeSpaces()
        self.writer.startElement(name, attrs)

    def endElement(self, name, indent=True):
        if indent:
            self.writeSpaces('\n')

        self.writer.endElement(name)

        self.depth_idx -= 1

    def write_node(self, node):
        self.start_xml_node(node.get_data())

        for child_node in node.get_children():
            self.current_node = child_node
            self.write_node(child_node)

        self.end_xml_node()

    def start_xml_node(self, seq_packet):
        inter = seq_packet.inter
        filter = seq_packet.filter

        attr_vals = {'interval' : str(inter),
                     'filter' : filter or ''}

        attrs = AttributesImpl(attr_vals)
        self.startElement('SequencePacket', attrs)

        self.start_xml_packet(seq_packet.packet)

    def end_xml_node(self):
        self.endElement('SequencePacket')

    def start_xml_packet(self, metapacket):
        protocols = metapacket.get_protocols()

        for proto in protocols:
            attr_vals = {'id' : get_proto_name(proto),
                         'time' : "%.6f" % proto.time}

            attrs = AttributesImpl(attr_vals)
            self.startElement('proto', attrs)


            for field in get_proto_fields(proto):
                if is_default_field(proto, field):
                    continue

                name = get_field_name(field)
                value = get_field_value(proto, field)

                attr_vals = {'id' : name}

                self.writer.characters('\n')

                attrs = AttributesImpl(attr_vals)
                self.startElement('field', attrs, False)
                self.writer.characters(b64encode(str(value)))
                self.endElement('field', False)

        for idx in xrange(len(protocols)):
            self.endElement('proto')

def save_sequence(fname, sequence, strict=True, report_recv=False, \
                  report_sent=True, tot_loop_count=None, inter=None):
    assert isinstance(sequence, Node)

    try:
        return SequenceWriter(fname, sequence, strict, report_recv, \
                              report_sent, tot_loop_count, inter).save_async()
    except Exception, err:
        log.error("Cannot while saving sequence to %s" % fname)
        log.error(generate_traceback())
        raise err

def load_sequence(fname):
    try:
        return SequenceLoader(fname)
    except Exception, err:
        log.error("Error while loading sequence from %s" % fname)
        log.error(generate_traceback())

        raise err

if __name__ == "__main__":
    tree = Node()
    first = Node(SequencePacket(MetaPacket(Ether() / IP() /  TCP())))
    first.append_node(Node(SequencePacket(MetaPacket(IP()))))

    tree.append_node(first)
    SequenceWriter("test.xml", tree)

    for child in tree:
        print child.get_data().packet.get_time()

    import time
    time.sleep(2)

    new_tree = SequenceLoader("test.xml").parse()

    print "Checking validity %s" % ((new_tree == tree) and ("ok") or ("wrong"))

    for child in new_tree:
        print child
        print child.get_data().packet.get_time()

