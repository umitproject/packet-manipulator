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

from xml.sax import handler, make_parser
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl

from PM.Core.Atoms import Node
from PM.Core.Logger import log

from PM.Backend.Scapy import *
from PM.Backend import SequencePacket

class SequenceLoader(handler.ContentHandler):
    def __init__(self, fname):
        self.fname = fname

        self.in_node = False
        self.in_packet = False
        self.packet_interval = None
        self.packet_filter = None
        self.in_proto = False
        self.protocol = None
        self.current_protocol = None
        self.in_field = False
        self.field_id = False
        self.field_value = None

        self.tree = Node()
        self.current_node = self.tree

        handler.ContentHandler.__init__(self)

        parser = make_parser()
        parser.setContentHandler(self)
        parser.parse(self.fname)

    def add_pending(self):
        if self.current_protocol:

            if self.protocol:
                self.protocol = self.current_protocol / self.protocol
            else:
                self.protocol = self.current_protocol

            self.protocol.time = self.current_protocol.time

            self.current_node.data.packet = MetaPacket(self.protocol)
            self.protocol = self.current_protocol = None

    def startElement(self, name, attrs):
        if name == 'PMScapySequence':
            self.in_sequence = True
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
            except Exception, err:
                print err
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
                        self.protocol = self.current_protocol / self.protocol
                    else:
                        self.protocol = self.current_protocol

                self.current_protocol = protocol

            except Exception, err:
                print err
            else:
                self.in_proto = True
        elif self.in_proto and name == 'field':
            try:
                self.field_id = attrs['id']
            except Exception, err:
                print err
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
        if self.in_field:
            self.field_value = content

            try:
                value = eval(self.field_value)
            except:
                value = self.field_value

            field = get_proto_field(self.current_protocol,
                                            self.field_id)

            set_field_value(self.current_protocol, field, value)

class SequenceWriter(object):
    def __init__(self, fname, sequence):
        output = open(fname, 'w')

        self.depth_idx = 0
        self.writer = XMLGenerator(output, 'utf-8')

        self.writer.startDocument()
        self.startElement('PMScapySequence', {})

        self.current_node = None

        for node in sequence.get_children():
            self.current_node = node
            self.write_node(node)

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
        protocols.reverse()

        for proto in protocols:
            attr_vals = {'id' : get_proto_name(proto),
                         'time' : "%.6f" % proto.time}

            attrs = AttributesImpl(attr_vals)
            self.startElement('proto', attrs)


            for field in get_proto_fields(proto):
                name = get_field_name(field)
                value = get_field_value(proto, field)

                attr_vals = {'id' : name}

                self.writer.characters('\n')

                attrs = AttributesImpl(attr_vals)
                self.startElement('field', attrs, False)
                self.writer.characters(str(value))
                self.endElement('field', False)

        for idx in xrange(len(protocols)):
            self.endElement('proto')

def save_sequence(fname, sequence):
    assert isinstance(sequence, Node)

    try:
        SequenceWriter(fname, sequence)
    except Exception, err:
        log.debug("Cannot save sequence to file %s (%s)" % (fname, str(err)))
        return False
    else:
        return True

def load_sequence(fname):
    try:
        tree = SequenceLoader(fname).tree
        return tree
    except Exception, err:
        log.debug("Cannot load sequence from file %s (%s)" % (fname, str(err)))
        return None

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

    new_tree = SequenceLoader("test.xml").tree

    print "Checking validity %s" % ((new_tree == tree) and ("ok") or ("wrong"))

    for child in new_tree:
        print child
        print child.get_data().packet.get_time()

