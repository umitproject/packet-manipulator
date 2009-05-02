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

import os
import os.path

from PM.Backend.Scapy.packet import MetaPacket
from PM.Backend.Scapy.wrapper import RawPcapReader, PcapReader, wrpcap, PacketList

from PM.Core.I18N import _

def register_static_context(BaseStaticContext):

    class StaticContext(BaseStaticContext):
        def load(self, operation=None):
            if not self.cap_file:
                return False

            self.data = []

            try:
                pktcount = 0
                reader = PcapReader(self.cap_file)
                size = os.stat(self.cap_file).st_size

                if size >= 1024 ** 3:
                    fsize = "%.1f GB" % (size / (1024.0 ** 3))
                elif size >= 1024 ** 2:
                    fsize = "%.1f MB" % (size / (1024.0 ** 2))
                else:
                    fsize = "%.1f KB" % (size / 1024.0)

                data = []

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

                        data.append(p)

                for p in PacketList(data, name = os.path.basename(self.cap_file)):
                    self.data.append(MetaPacket(p))

                del data

                if operation:
                    operation.summary = _('Loaded %s - %d packets (%s)') % \
                                         (self.cap_file, pktcount, fsize)
                    operation.percentage = 100.0

            except IOError, (errno, err):
                self.summary = str(err)
                return False

            self.status = self.SAVED
            self.title = self.cap_file
            self.summary = _('%d packets loaded.') % len(self.data)
            return True

        def save(self):
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
                wrpcap(self.cap_file, data, gz=('gz' in self.cap_file) and (1) or (0))
            except IOError, (errno, err):
                self.summary = str(err)
                return False

            self.status = self.SAVED
            self.title = self.cap_file
            self.summary = _('%d packets written.') % len(data)
            return True

    return StaticContext
