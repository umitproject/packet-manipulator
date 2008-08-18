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

"""
<proto id="TCP" layer="4">
    This is Transmission Control Protocol.<br/>
    It the most common protocol in the Internet on fourth layer of the OSI model.
    <attr id="sport">
        The source port number (0-65535)
    </attr>
    <attr id="dport">
        The destination port number (0-65535)
    </attr>
    <attr id="seq">
        The sequence number of the first data octet in this segment (except when SYN is present).
    </attr>
    <attr id="ack">
        If the ACK control bit is set this field contains the value of the
        next sequence number the sender of the segment is expecting to receive.
    </attr>
    <attr id="dataofs">
        The number of 32 bit words in the TCP Header. This indicates where
        the data begins.
    </attr>
    <attr id="reserved">
        Reserved for future use.
    </attr>
    <attr id="flags">
        URG, ACK, PSH, RST, SYN, FIN flags.
    </attr>
    <attr id="window">
        The number of data octets beginning with the one indicated in the
        acknowledgment field which the sender of this segment is willing to accept.
    </attr>
    <attr id="chksum">
        Checksum of Pseudo Header, TCP header and data.
    </attr>
    <attr id="urgptr">
        This field communicates the current value of the urgent pointer as a
        positive offset from the sequence number in this segment.
    </attr>
    <attr id="options">
        Options may occupy space at the end of the TCP header and are a multiple of 8 bits in length.
    </attr>
</proto>
"""

import sys
from xml.sax import handler, make_parser, parseString

import wrapper

class DocLoader(handler.ContentHandler):
    def __init__(self, outfile):
        self.outfile = outfile
        self.layer = None
        self.protocol = None
        self.protocol_doc = ''

        self.attributes = {}
        self.attribute = None
        self.attribute_doc = ''

        self.in_proto = False
        self.in_attr = False

    def startElement(self, name, attrs):
        try:
            if name == 'proto':
                self.layer = int(attrs['layer'])
                self.protocol = attrs['id']
                self.in_proto = True
                self.in_attr = False

            if name == 'attr' and self.in_proto:
                self.attribute = attrs['id']
                self.in_attr = True

        except Exception:
            pass
    
    def characters(self, chars):
        if self.in_proto and self.in_attr:
            self.attribute_doc += chars
        elif self.in_proto:
            self.protocol_doc += chars

    def endElement(self, name):
        try:
            if name == 'proto' and self.in_proto:
                all = wrapper.__dict__

                if self.protocol in all:
                    proto = all[self.protocol]

                    setattr(proto, '__doc__', self.escape(self.protocol_doc))
                    setattr(proto, '_pm_layer', self.layer)

                    for attr in self.attributes:
                        field = getattr(proto, attr, None)

                        if field:
                            setattr(field, '__doc__', self.escape(self.attributes[attr]))

                self.in_proto = False
                self.in_attr = False
                self.protocol_doc = ''
                self.attributes.clear()
                self.attribute = None
                self.attribute_doc = ''
                self.in_attr = False
                self.layer = None

            if name == 'attr' and self.in_proto and self.in_attr:
                self.attributes[self.attribute] = self.escape(self.attribute_doc)

                self.attribute = None
                self.attribute_doc = ''
                self.in_attr = False
        except Exception, err:
            print err

    def escape(self, txt):
        txt = txt.replace("\r", "\n").replace("\t", " ")
        data = [part.lstrip(" ") for part in txt.split("\n")]
        return "\n".join(filter(None, data))

def apply_doc():
    handler = DocLoader(sys.stdout)
    parseString(__doc__, handler)
