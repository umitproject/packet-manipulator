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
SIP UserEnumeration (Active audit)
"""
import gtk
import gobject
import random

from time import sleep
from threading import Thread

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

AUDIT_NAME = 'sip-userenum'
AUDIT_MSG = '<tt><b>' + AUDIT_NAME + ':</b> %s</tt>'

class SipPack(object):
    def __init__(self, target_addr, srcip, srcport, type_of_msg, user_agent, extension=None):
        self.target_addr = target_addr
        self.srcip = srcip
        self.srcport = srcport
        self.type_of_msg = type_of_msg
        self.user_agent = user_agent
        self.counter_pack = 0
        self.t_packs = 0
        self.extension = extension


    def create(self, destip, srcip, srcport, remote_port, type_of_msg, useragent, extension, caller='101', tag=None, cseq=1, percent=0):

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
        header['Via'] = 'SIP/2.0/UDP %s:%s;rport;branch=%s' % (srcip, remote_port, branch)
        header['From'] = fromaddr
        header['Call-ID'] = '%s' % random.getrandbits(80)
        header['CSeq'] = '%s %s' % (cseq, type_of_msg)
        header['Max-Forwards'] = 60
        header['Content-Length'] = 0
        header['User-Agent'] = useragent


        sip = '%s\r\n' % head
        for h in header.iteritems():
            sip += '%s: %s\r\n' % h
        sip += '\r\n'

        pkt = MetaPacket.new('ip') / MetaPacket.new('udp')
        pkt.set_fields('ip', {
            'dst' : destip,
            'src' : srcip})

        pkt.set_fields('udp', {
            'sport' : srcport,
            'dport' : int(remote_port),
            'payload' : sip})

        percent = (self.counter_pack/self.t_packs) * 100.0
        status = 'Sending message %d of %d...' % (self.counter_pack, self.t_packs)

        return pkt, percent, status


    def __iter__(self):
        return self.messages()

    def messages(self):
        if self.extension is not None:
            #extension = self.extension.split(',')
            self.t_packs = len(self.target_addr) * len(self.extension)
        else:
            self.extension = '101'
            self.t_packs = len(self.target_addr)


        for dstaddr in self.target_addr:
            dstaddr = dstaddr.split(':')
            destip = dstaddr[0]
            remote_port = dstaddr[1]

            for extension in self.extension:
                self.counter_pack += 1
                yield self.create(destip, self.srcip, self.srcport, remote_port, self.type_of_msg, self.user_agent, extension, caller=extension)

class SipExtra:

    def __init__(self):
        self.utils = Core().get_need(None, 'SipGuiUtils')

    def on_response(self, sippack_dict):
        self.sip_dict = sippack_dict

    def create_sip_btn(self):
        inputs = ('type of message', 'user agent')
        btn = gtk.Button("Create")
        btn.connect('clicked', self.utils.create_sip_window, inputs, self.on_response)
        return btn

    def create_file_btn(self):
        filechooserbutton = gtk.FileChooserButton("Select A File", None)
        return filechooserbutton

    def create_profiler_btn(self):
        btn = gtk.Button("Select")
        btn.connect('clicked', self.utils.create_profiler_window, self.on_response_profiler)
        return btn

    def on_response_profiler(self, profile_select):
        self.profiles = profile_select

    def get_dict(self):
        return self.sip_dict

    def get_profiles(self):
        return self.profiles

sipextra = SipExtra()

class SipEnumOperation(AuditOperation):
    def __init__(self, session, target_ip, source_port, type_of_msg, user_agent, delay, source_ip, user_list):
        AuditOperation.__init__(self)

        #self.utils = Core().get_need(None, 'SipPack')

        self.session = session
        self.target_ip = target_ip
        self.type_of_msg = type_of_msg
        self.user_agent = user_agent
        self.srcip = source_ip
        self.srcport = source_port
        self.delay = delay and delay / 1000.0 or 0
        self.user_list = user_list

        self.percentage = 0
        self.summary = AUDIT_MSG % _('idle')

    def start(self):
        if self.state == self.RUNNING:
            return False

        self.state = self.RUNNING

        thread = Thread(target=self.__thread_main, name='SIPENUMERATION')
        thread.setDaemon(True)
        thread.start()

        return True

    def stop(self):
        self.state = self.NOT_RUNNING
        self.summary = AUDIT_MSG % _('Stopped')


    def __thread_main(self):
        try:
            log.debug('Entered in __thread_main')

            sippack = SipPack(self.target_ip, self.srcip, self.srcport, self.type_of_msg, self.user_agent, extension=self.user_list)


            for sipmsg, percent, status in sippack.messages():
                self.sip_send(sipmsg)
                self.summary = AUDIT_MSG % _('%s' % status)
                self.percentage = percent
                sleep(self.delay)


            self.state = self.NOT_RUNNING
            self.summary = AUDIT_MSG % _('Finished')
            self.percentage = 100.0


        except Exception, err:
            log.error(generate_traceback())

    def sip_send(self, pkt):
        self.sender = self.session.context.sr_l3(pkt, timeout=4, onreply=self.on_resolved)
        self.session.output_page.user_msg(
            _('SIP Request FROM %s:%s to %s:%s ') % (pkt.get_field('ip.src'), pkt.get_field('udp.sport'), pkt.get_field('ip.dst'), pkt.get_field('udp.dport')),
            STATUS_INFO, AUDIT_NAME)

    def on_resolved(self, send, mpkt, reply, udata):
        #print '%s' % reply.get_field('udp.payload')
        if mpkt is not None:
            self.session.output_page.user_msg(
                _('SIP Reply FROM %s:%s TO %s:%s') % \
                (reply.get_field('ip.src'), reply.get_field('udp.sport'),
                 reply.get_field('ip.dst'), reply.get_field('udp.dport')
                 ), STATUS_INFO, AUDIT_NAME)



class SipEnumeration(Plugin, ActiveAudit):
    __inputs__ = (('User List', (sipextra.create_file_btn, _("Enumeration List"))),
                  ('source port', (5060, _('A port to send sip packet'))),
                  ('delay', (300, _('Time delay betwen send packets'))),
                  ('Sip Pack', (sipextra.create_sip_btn, _("SIP packet"))),
                  ('IP List', (sipextra.create_profiler_btn, _("SIP hostlist select window"))),
                  )

    def start(self, reader):
        a, self.item = self.add_menu_entry('SipEnumeration', 'Sip Enumeration...',
                                           _('A SIP Enumeration'),
                                           gtk.STOCK_EXECUTE)

    def stop(self):
        self.remove_menu_entry(self.item)


    def execute_audit(self, sess, inp_dict):
        sip_dict = sipextra.get_dict()
        user_list = []

        user_agent = sip_dict['user agent']
        type_of_msg = sip_dict['type of message']
        delay = inp_dict['delay']
        lines = open(inp_dict['User List'],'r').readlines()
        for line in lines:
            col = line.find('\n')
            if col != -1:
                user_list.append(line[:col])
            else:
                user_list.append(line)

        target_ip = sipextra.get_profiles()
        print target_ip
        source_port = inp_dict['source port']
        source_ip = sess.context.get_ip1()


        return SipEnumOperation(
            sess, target_ip, source_port, type_of_msg, user_agent, delay, source_ip, user_list
        )

__plugins__ = [SipEnumeration]
__plugins_deps__ = [('SipEnumeration', ['SipGuiUtils'], ['SipEnumeration-0.1'], [])]

__audit_type__ = 1
__protocols__ = (('udp', 5060), ('udp', 5061), ('sip', None))
__vulnerabilities__ = (('SIP Enumeration', {
    'description' : 'SIP Enumeration plugin'
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