#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Adriano Monteiro Marques
#
# Author: Francesco Piccinno <stack.box@gmail.com>
# Author: Guilherme Rezende <guilhermebr@gmail.com>
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
SIP Portscan (Active audit)
"""


import gtk
import gobject
import random


from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.atoms import generate_traceback
from umit.pm.core.auditutils import is_ip, random_ip, AuditOperation
from umit.pm.core.const import STATUS_ERR, STATUS_WARNING, STATUS_INFO

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.plugins.core import Core
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *

from umit.pm.backend import MetaPacket


AUDIT_NAME = 'sip-portscan'

class SipPack(object):

    def __init__(self, destip, srcip, srcport, remote_port, type_of_msg, useragent, extension='101', caller='101', tag=None, cseq=1):

        self.header = dict()

        if type_of_msg == 'REGISTER':
            uri = '<sip:%s>' % destip
            fromaddr = '<sip:%s@%s>' % (caller, destip)

        elif type_of_msg == 'INVITE':
            uri = '<sip:%s@%s>' % (extension, destip)
            fromaddr = '"%s" <sip:%s@%s>' % (caller, caller, destip)

        if tag is not None:
            fromaddr += ';tag=%s' % tag

        branch = '%s' % random.getrandbits(32)

        self.head = '%s %s SIP/2.0' % (type_of_msg, uri)
        self.header['Contact'] = 'sip:%s@%s:%s' % (caller,srcip,srcport)
        self.header['To'] = '<sip:%s@%s:%s>' % (extension, destip, remote_port)
        self.header['Via'] = 'SIP/2,0/UDP %s:%s;rport;branch=%s' % (srcip, remote_port, branch)
        self.header['From'] = fromaddr
        self.header['Call-ID'] = '%s' % random.getrandbits(80)
        self.header['CSeq'] = '%s %s' % (cseq, type_of_msg)
        self.header['Max-Forwards'] = 60
        self.header['Content-Length'] = 0
        self.header['User-Agent'] = useragent


    def prepare(self):
        sip = '%s\r\n' % self.head
        for h in self.header.iteritems():
            sip += '%s: %s\r\n' % h
        sip += '\r\n'
        return(sip)

class SipPortscanOperation(AuditOperation):
    def __init__(self, session,  target_ip, remote_port, type_of_msg, user_agent, source):
        AuditOperation.__init__(self)

        self.session = session
        self.target_ip = target_ip
        self.remote_port = remote_port
        self.type_of_msg = type_of_msg
        self.user_agent = user_agent
        self.srcip = source
        self.srcport = 5060

    def start(self):
        if self.state == self.RUNNING:
            return False

        self.state = self.RUNNING

        if self.target_ip.find(','):
            for dstip in self.target_ip.split(','):
                if self.remote_port.find(','):
                    for dstport in self.remote_port.split(','):
                        sipmsg = SipPack(dstip, self.srcip, self.srcport, dstport, self.type_of_msg, self.user_agent)
                        self.sip_send(self.srcip, dstip, self.srcport, int(dstport), sipmsg.prepare())

                else:
                    sipmsg = SipPack(dstip, self.srcip, self.srcport, self.remote_port, self.type_of_msg, self.user_agent)
                    self.sip_send(self.srcip, dstip, self.srcport, int(self.remote_port), sipmsg.prepare())


        elif self.remote_port.find(','):
            for dstport in self.remote_port.split(','):
                sipmsg = SipPack(self.target_ip, self.srcip, self.srcport, dstport, self.type_of_msg, self.user_agent)
                self.sip_send(self.srcip, self.target_ip, self.srcport, int(dstport), sipmsg.prepare())


        else:
            sipmsg = SipPack(self.target_ip, self.srcip, self.srcport, self.remote_port, self.type_of_msg, self.user_agent)
            self.sip_send(self.srcip, self.target_ip, self.srcport, int(self.remote_port), sipmsg.prepare())


        self.percentage = 100.0
        self.state = self.NOT_RUNNING


    def stop(self):
        self.state = self.NOT_RUNNING

    def sip_send(self, srcip, dstip, srcport, dstport, data):
        pkt = MetaPacket.new('ip') / MetaPacket.new('udp')
        pkt.set_fields('ip', {
            'dst' : dstip,
            'src' : srcip})

        pkt.set_fields('udp', {
            'sport' : srcport,
            'dport' : dstport,
            'payload' : data})

        self.sender = self.session.context.sr_l3(
            pkt, timeout=4,
      #      onerror=self.on_error,
            onreply=self.on_resolved,
            onsend=self.on_send)


    def on_send(self, send, mpkt, udata):
        self.session.output_page.user_msg(
            _('SIP Request FROM %s to %s ') % (send.mpkts[0].get_field('ip.src'), send.mpkts[0].get_field('ip.dst')),
            STATUS_INFO, AUDIT_NAME)

    def on_resolved(self, send, mpkt, reply, udata):

        payload = reply.data
        print payload
        self.session.output_page.user_msg(
            _('SIP Reply FROM %s TO %s') % \
            (reply.get_field('ip.src'),
             reply.get_field('ip.dst'),
             ), STATUS_INFO, AUDIT_NAME
        )


class SipPortscan(Plugin, ActiveAudit):
    __inputs__ = (
        ('target ip', ('0.0.0.0', _('A ip or CIDR/wildcard expression to perform a multihost scan'))),
        ('remote port', ('5060', _('A port list to scan'))),
        ('type of message', (['REGISTER','OPTIONS', 'INVITE', 'PHRACK', 'INFO'], _('Which headers that the message will include'))),
        ('user agent', (['Cisco', 'Linksys', 'Grandstream', 'Yate', 'Xlite', 'Asterisk'], _('A list of user-agents to scan spoofed'))),
    )

    def start(self, reader):
        a, self.item = self.add_menu_entry('SIPPortscan',
                                           _('Sip Portscan'),
                                           _('SIP Portscan test'),
                                           gtk.STOCK_EXECUTE)


    def stop(self):
        self.remove_menu_entry(self.item)

    def execute_audit(self, sess, inp_dict):
        target_ip = inp_dict['target ip']
        remote_port = inp_dict['remote port']
        type_of_msg = inp_dict['type of message']
        user_agent = inp_dict['user agent']

        source = sess.context.get_ip1()


        return SipPortscanOperation(
            sess, target_ip, remote_port, type_of_msg, user_agent, source
        )

__plugins__ = [SipPortscan]
__plugins_deps__ = [('SIPPortscan', ['IPDecoder'], ['=SIPPortscan-1.0'], [])]

__audit_type__ = 1
__protocols__ = (('udp', 5060), ('udp', 5061), ('sip', None))
__vulnerabilities__ = (('SIP Portscan', {
    'description' : 'SIP Portscan plugin'
    'The Session Initiation Protocol (SIP) is an IETF-defined signaling protocol,'
    'widely used for controlling multimedia communication sessions'
    'such as voice and video calls over'
    'Internet Protocol (IP). The protocol can be used for creating,'
    'modifying and terminating two-party (unicast) or multiparty (multicast)'
    'sessions consisting of one or several media streams.'
    'The modification can involve changing addresses or ports, inviting more'
    'participants, and adding or deleting media streams. Other feasible'
    'application examples include video conferencing, streaming multimedia distribution,'
    'instant messaging, presence information, file transfer and online games.'
    'SIP was originally designed by Henning Schulzrinne and Mark Handley starting in 1996.'
    'The latest version of the specification is RFC 3261 from the IETF Network Working'
    'Group. In November 2000, SIP was accepted as a 3GPP signaling protocol and permanent'
    'element of the IP Multimedia Subsystem (IMS) architecture for IP-based streaming'
    'multimedia services in cellular systems.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                     'Session_Initiation_Protocol'), )
    }),
)