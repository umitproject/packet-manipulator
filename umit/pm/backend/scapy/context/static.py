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

import os
import os.path

from umit.pm.backend.scapy.packet import MetaPacket
from umit.pm.backend.scapy.wrapper import PcapWriter, PcapReader, wrpcap, PacketList
from umit.pm.manager.auditmanager import AuditDispatcher, IL_TYPE_ETH

from umit.pm.core.i18n import _

class CustomPcapWriter(PcapWriter):
    def __init__(self, operation, plen, filename, *args, **kargs):
        self.operation = operation

        self.packet_len = plen
        self.packet_idx = 0

        PcapWriter.__init__(self, filename, *args, **kargs)

    def _write_packet(self, packet):
        PcapWriter._write_packet(self, packet)

        self.packet_idx += 1

        if self.packet_idx % 10 == 0:
            self.update_operation()

    def update_operation(self):
        size = os.stat(self.filename).st_size

        if size >= 1024 ** 3:
            fsize = "%.1f GB" % (size / (1024.0 ** 3))
        elif size >= 1024 ** 2:
            fsize = "%.1f MB" % (size / (1024.0 ** 2))
        else:
            fsize = "%.1f KB" % (size / 1024.0)

        if self.operation:
            self.operation.summary = _('Writing %s - %d packets (%s)') % \
                                      (self.filename, self.packet_idx, fsize)

            self.operation.percentage = (float(self.packet_idx) /
                                         float(self.packet_len)) * 100.0

def register_static_context(BaseStaticContext):

    class StaticContext(BaseStaticContext):
        def __init__(self, title, fname=None, audits=False):
            BaseStaticContext.__init__(self, title, fname, audits)

            self.audit_dispatcher = None

        def load(self, operation=None):
            if not self.cap_file:
                return False

            self.data = []

            try:
                pktcount = 0
                reader = PcapReader(self.cap_file)
                size = os.stat(self.cap_file).st_size

                if self.audits:
                    self.audit_dispatcher = AuditDispatcher(reader.linktype)

                if size >= 1024 ** 3:
                    fsize = "%.1f GB" % (size / (1024.0 ** 3))
                elif size >= 1024 ** 2:
                    fsize = "%.1f MB" % (size / (1024.0 ** 2))
                else:
                    fsize = "%.1f KB" % (size / 1024.0)

                while True:
                    p = reader.read_packet()

                    if p is None:
                        break
                    else:
                        pktcount += 1

                        if pktcount % 10 == 0 and operation:
                            operation.summary = \
                                _('Loading %s - %d packets (%s)') % \
                                 (self.cap_file, pktcount, fsize)

                            # FIXME: we are accessing to a private field (f)

                            if getattr(reader.f, 'fileobj', None):
                                # If fileobj is present we are gzip file and we
                                # need to get the absolute position not the
                                # relative to the gzip file.
                                pos = reader.f.fileobj.tell()
                            else:
                                pos = reader.f.tell()

                            operation.percentage = \
                                (pos / float(size)) * 100.0

                        lst = PacketList([p], os.path.basename(self.cap_file))
                        mpkt = MetaPacket(lst[0])
                        self.data.append(mpkt)

                        # TODO: overhead
                        if self.audit_dispatcher:
                            self.audit_dispatcher.feed(mpkt)

                if operation:
                    operation.summary = _('Loaded %s - %d packets (%s)') % \
                                         (self.cap_file, pktcount, fsize)
                    operation.percentage = 100.0

            except IOError, (errno, err):
                self.summary = str(err)

                if operation:
                    operation.summary = str(err)
                    operation.percentage = 100.0

                return False

            self.status = self.SAVED
            self.title = self.cap_file
            self.summary = _('%d packets loaded.') % len(self.data)
            return True

        def save(self, operation=None):
            if getattr(self, 'get_all_data', False):
                data = self.get_all_data()
            else:
                data = self.get_data()

            if not self.cap_file:
                return False

            data = [packet.root for packet in data]

            if not data:
                self.summary = _('No packets to save')
                return False

            try:
                writer = CustomPcapWriter(operation, len(data), self.cap_file, \
                                          gz=('gz' in self.cap_file) and 1 or 0)
                writer.write(data)
                writer.close()

                writer.update_operation()

            except IOError, (errno, err):
                self.summary = str(err)

                if operation:
                    operation.summary = str(err)

                return False

            self.status = self.SAVED
            self.title = self.cap_file
            self.summary = _('%d packets written.') % len(data)
            return True

    return StaticContext
