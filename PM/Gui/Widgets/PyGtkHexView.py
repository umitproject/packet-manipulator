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

import gtk
import gtkhex
import gobject

from PM.Core.Logger import log

class HexView(gtkhex.Hex):
    __gtype_name__ = "PyGtkHexView"

    def __init__(self):
        self._document = gtkhex.Document()

        super(HexView, self).__init__(self._document)

        self.show_offsets(True)
        self.set_geometry(8, 5)
        self.set_read_only_mode(True)

    def select_block(self, offset, len, ascii=True):
        """
        Select a block of data in the HexView

        @param offset the offset byte
        @param len the lenght of selection
        @param ascii True to set primary selection on ASCII otherwise on HEX
        """

        log.debug('Selecting blocks starting from %d to %d (%s)' % \
                  (offset, offset + len, self.payload.__len__()))

        self.set_selection(offset, offset + len)

    def get_payload(self):
        return self._document.get_data(0, self._document.file_size)
    def set_payload(self, val):
        self._document.set_data(0, len(val), self._document.file_size,
                                val, False)

    def get_font(self):
        return self._font
    def modify_font(self, val):
        self.set_font(val)

    def get_bpl(self): return self._bpl
    def set_bpl(self, val):
        # This is hardcoded in the sense that gtkhex doens't offer this but
        # grouping. So we use that to encode grouping information.

        # GROUP_LONG has 4 bytes, GROUP_WORD has 2 bytes, GROUP_BYTE only 1

        if val == 1:
            self.set_group_type(gtkhex.GROUP_BYTE)
        elif val == 2:
            self.set_group_type(gtkhex.GROUP_WORD)
        elif val == 3:
            self.set_group_type(gtkhex.GROUP_LONG)

    payload = property(get_payload, set_payload)
    font = property(get_font, modify_font)
    bpl = property(get_bpl, set_bpl)

gobject.type_register(HexView)

if __name__ == "__main__":
    v = HexView()
    v.payload = "Crashhhaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!"
    v.font = "Courier New 10"
    w = gtk.Window()
    w.add(v)
    w.show_all()
    gtk.main()
