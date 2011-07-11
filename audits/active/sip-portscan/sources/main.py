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
from time import sleep

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
AUDIT_MSG = '<tt><b>' + AUDIT_NAME + ':</b> %s</tt>'


class SipPack(object):
    class Packet(object):
	def __init__(self, dstip, dstport, srcip, srcport, head, header):
	    self.dstip = dstip
	    self.dstport = dstport
	    self.srcip = srcip
	    self.srcport = srcport
	    self.head = head
	    self.header = header

	def prepare(self):
	    sip = '%s\r\n' % self.head
	    for h in self.header.iteritems():
		sip += '%s: %s\r\n' % h
	    sip += '\r\n'
	    return sip

    def __init__(self):
	self.packets =  []
	self.current_item = 0


    def create(self, destip, srcip, srcport, remote_port, type_of_msg, useragent, extension='101', caller='101', tag=None, cseq=1):

        header = dict()

        if type_of_msg == 'REGISTER':
            uri = '<sip:%s>' % destip
            fromaddr = '<sip:%s@%s>' % (caller, destip)

        elif type_of_msg == 'INVITE':
            uri = '<sip:%s@%s>' % (extension, destip)
            fromaddr = '"%s" <sip:%s@%s>' % (caller, caller, destip)

        if tag is not None:
            fromaddr += ';tag=%s' % tag

        branch = '%s' % random.getrandbits(32)

        head = '%s %s SIP/2.0' % (type_of_msg, uri)
        header['Contact'] = 'sip:%s@%s:%s' % (caller,srcip,srcport)
        header['To'] = '<sip:%s@%s:%s>' % (extension, destip, remote_port)
        header['Via'] = 'SIP/2,0/UDP %s:%s;rport;branch=%s' % (srcip, remote_port, branch)
        header['From'] = fromaddr
        header['Call-ID'] = '%s' % random.getrandbits(80)
	header['CSeq'] = '%s %s' % (cseq, type_of_msg)
        header['Max-Forwards'] = 60
        header['Content-Length'] = 0
        header['User-Agent'] = useragent

	self.packets.append(self.Packet(destip, remote_port, srcip, srcport, head, header))

    def __iter__(self):
	return self

    def next(self):
	if (self.current_item == len(self.packets)):
	    raise StopIteration
	else:
	    pack = self.packets[self.current_item]
	    self.current_item += 1
	    return pack

	return self.data



class SipPortscanOperation(AuditOperation):
    def __init__(self, session, target_ip, remote_port, source_port, type_of_msg, user_agent, delay, source_ip):
        AuditOperation.__init__(self)

        self.session = session
        self.target_ip = target_ip
        self.remote_port = remote_port
        self.type_of_msg = type_of_msg
        self.user_agent = user_agent
        self.srcip = source_ip
        self.srcport = source_port
        self.delay = delay and delay / 1000.0 or 0

        self.percentage = 0
        self.summary = AUDIT_MSG % _('idle')

    def start(self):
        if self.state == self.RUNNING:
            return False

        self.state = self.RUNNING

	sipmsg = SipPack()

        if self.target_ip.find(','):
            for dstip in self.target_ip.split(','):
                if self.remote_port.find(','):
                    for dstport in self.remote_port.split(','):
                        sipmsg.create(dstip, self.srcip, self.srcport, dstport, self.type_of_msg, self.user_agent)

                else:
                    sipmsg.create(dstip, self.srcip, self.srcport, self.remote_port, self.type_of_msg, self.user_agent)


        elif self.remote_port.find(','):
            for dstport in self.remote_port.split(','):
                sipmsg.create(self.target_ip, self.srcip, self.srcport, dstport, self.type_of_msg, self.user_agent)


        else:
            sipmsg.create(self.target_ip, self.srcip, self.srcport, self.remote_port, self.type_of_msg, self.user_agent)


	self.sip_send(sipmsg)

        self.percentage = 100.0
        self.state = self.NOT_RUNNING
        self.summary = AUDIT_MSG % _('Finished')



    def stop(self):
        self.state = self.NOT_RUNNING
        self.summary = AUDIT_MSG % _('Stopped')


    def sip_send(self, packets):

	self.summary = AUDIT_MSG % _('Sending...')
	n_pack = 0
	t_pack = len(packets.packets)

	for sipmsg in packets:
	    pkt = MetaPacket.new('ip') / MetaPacket.new('udp')
	    pkt.set_fields('ip', {
	        'dst' : sipmsg.dstip,
	        'src' : sipmsg.srcip})

	    pkt.set_fields('udp', {
	        'sport' : sipmsg.srcport,
	        'dport' : int(sipmsg.dstport),
	        'payload' : sipmsg.prepare()})

	    self.sender = self.session.context.sr_l3(pkt, onreply=self.on_resolved)
	    self.session.output_page.user_msg(
	        _('SIP Request FROM %s to %s ') % (pkt.get_field('ip.src'), pkt.get_field('ip.dst')),
	        STATUS_INFO, AUDIT_NAME)

	    n_pack += 1
	    self.percentage = (n_pack / t_pack) * 100.0


	    sleep(self.delay)


    def on_resolved(self, send, mpkt, reply, udata):
        self.session.output_page.user_msg(
            _('SIP Reply FROM %s TO %s') % \
            (reply.get_field('ip.src'),
             reply.get_field('ip.dst'),
             ), STATUS_INFO, AUDIT_NAME)


class SipPortscan(Plugin, ActiveAudit):
    __inputs__ = (
        ('target ip', ('0.0.0.0', _('A ip or CIDR/wildcard expression to perform a multihost scan'))),
        ('remote port', ('5060', _('A port list to scan'))),
        ('source port', (5060, _('A port to send sip packet'))),
        ('delay', (300, _('Time delay betwen send packets'))),
        ('type of message', (['REGISTER','OPTIONS', 'INVITE', 'PHRACK', 'INFO'], _('Which headers that the message will include'))),
        ('user agent', (['Cisco', 'Linksys', 'Grandstream', 'Yate', 'Xlite', 'Asterisk'], _('A list of user-agents to scan spoofed'))),
    )

    def start(self, reader):
        a, self.item = self.add_menu_entry('SIPPortscan', 'Sip Portscan...',
                                           _('A SIP Portscan'),
                                           gtk.STOCK_EXECUTE)


    def stop(self):
        self.remove_menu_entry(self.item)

    def execute_audit(self, sess, inp_dict):
        target_ip = inp_dict['target ip']
        remote_port = inp_dict['remote port']
        source_port = inp_dict['source port']
        type_of_msg = inp_dict['type of message']
        user_agent = inp_dict['user agent']
        delay = inp_dict['delay']
        source_ip = sess.context.get_ip1()


        return SipPortscanOperation(
            sess, target_ip, remote_port, source_port, type_of_msg, user_agent, delay, source_ip
        )

__plugins__ = [SipPortscan]
__plugins_deps__ = [('SIPPortscan', ['SIPMonitor'], ['SIPPortscan-0.1'], [])]

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