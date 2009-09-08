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

# Use this to generate a field list
# for i in [i.name for i in backend.get_proto_fields(backend.IP())]: print "<attr id=\"%s\">\n</attr>" % i

"""
<scapydoc>
<proto id="IP" layer="3">
    <attr id="version">
        The Version field indicates the format of the internet header.
    </attr>
    <attr id="ihl">
        Internet Header Length is the length of the internet header in 32 bit
        words, and thus points to the beginning of the data.
    </attr>
    <attr id="tos">
        The Type of Service provides an indication of the abstract parameters
        of the quality of service desired.
    </attr>
    <attr id="len">
        Internet Header Length is the length of the internet header in 32 bit
        words, and thus points to the beginning of the data.
    </attr>
    <attr id="id">
    </attr>
    <attr id="flags">
        Various Control Flags.
    </attr>
    <attr id="frag">
        This field indicates where in the datagram this fragment belongs.
    </attr>
    <attr id="ttl">
        This field indicates the maximum time the datagram is allowed to
        remain in the internet system.
    </attr>
    <attr id="proto">
        This field indicates the next level protocol used in the data portion
        of the internet datagram.
    </attr>
    <attr id="chksum">
        A checksum on the header only.
    </attr>
    <attr id="src">
        The source address.
    </attr>
    <attr id="dst">
        The destination address.
    </attr>
    <attr id="options">
        The options may appear or not in datagrams.
    </attr>
</proto>
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
<proto id="UDP" layer="4">
    User Datagram Protocol implementation.
    
    This protocol provides a procedure for application programs to send 
    messages to other programs with a minimum of protocol mechanism. The 
    protocol is transaction oriented, and delivery and duplicate protection 
    are not guaranteed.
    <attr id="sport">
        The source port number. See RFC 768 for more.
    </attr>
    <attr id="dport">
        The destination port number. See RFC 768 for more.
    </attr>
    <attr id="len">
        Length is the length in octets of this user datagram including this 
        header and the data. See RFC 768 for more.
    </attr>
    <attr id="chksum">
        Checksum of Pseudo Header, UDP header and data. See RFC 768 for more.
    </attr>
</proto>
<proto id="ICMP" layer="4">
    Internet Control Message Protocol implementation.

    It the most common protocol in the Internet on fourth layer 
    of the OSI model.
    <attr id="type">
        Specifies the format of the ICMP message.
    </attr>
    <attr id="code">
        Further qualifies the ICMP message.
    </attr>
    <attr id="chksum">
        Checksum that covers the ICMP message. This is the 16-bit one's 
        complement of the one's complement sum of the ICMP message starting 
        with the Type field.
    </attr>
    <attr id="id">
        This field contains an ID value, should be returned in case of ECHO REPLY
    </attr>
    <attr id="seq">
        This field contains a sequence value, should be returned 
        in case of ECHO REPLY.
    </attr>
</proto>
<proto id="ARP" layer="2">
    In computer networking, the Address Resolution Protocol (ARP) is the method for finding a host's hardware address when only its Network Layer address is known. ARP is defined in RFC 826.[1] It is a current Internet Standard (STD 37).
    <attr id="hwtype">
        Each data link layer protocol is assigned a number used in this field. For example, Ethernet is 1.
    </attr>
    <attr id="ptype">
        Each protocol is assigned a number used in this field. For example, IP is 0x0800.
    </attr>
    <attr id="hwlen">
        Length in bytes of a hardware address. Ethernet addresses are 6 bytes long.
    </attr>
    <attr id="plen">
        Length in bytes of a logical address. IPv4 address are 4 bytes long.
    </attr>
    <attr id="op">
        Specifies the operation the sender is performing: 1 for request, and 2 for reply.
    </attr>
    <attr id="hwsrc">
        Hardware address of the sender.
    </attr>
    <attr id="psrc">
        Protocol address of the sender.
    </attr>
    <attr id="hwdst">
        Hardware address of the intended receiver. This field is ignored in requests.
    </attr>
    <attr id="pdst">
        Protocol address of the intended receiver.
    </attr>
</proto>
<proto id="Ether" layer="1">
    Ethernet v2 framing, also known as DIX Ethernet (named after the major participants in the framing of the protocol: Digital Equipment Corporation, Intel, Xerox) defines the 2-octet field following the destination and source addresses as an EtherType that identifies an upper layer protocol.
    <attr id="dst">
        Destination MAC address
    </attr>
    <attr id="src">
        Source MAC address
    </attr>
    <attr id="type">
        For example, an EtherType value of 0x0800 signals that the packet contains an IPv4 datagram. Likewise, an EtherType of 0x0806 indicates an ARP frame, and 0x8100 indicates IEEE 802.1Q frame.
    </attr>
</proto>
</scapydoc>
"""

import sys
from xml.sax import handler, make_parser, parseString

from umit.pm.backend.scapy import wrapper
from umit.pm.core.logger import log

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

                    log.debug("Applying documentation to %s" % proto)

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
            pass

    def escape(self, txt):
        txt = txt.replace("\r", "\n").replace("\t", " ")
        data = [part.lstrip(" ") for part in txt.split("\n")]
        return "\n".join(filter(None, data))

def apply_doc():
    handler = DocLoader(sys.stdout)
    parseString(__doc__, handler)
