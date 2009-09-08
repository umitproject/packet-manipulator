#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
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

from umit.pm.core.i18n import _
from umit.pm.core.logger import log

class HexDocument(gtkhex.Document):
    __gtype_name__ = "PyGtkHexDocument"
    __gsignals__ = {
        'changed' : (gobject.SIGNAL_RUN_LAST,
                     gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,
                                         gobject.TYPE_BOOLEAN)),
    }

    def __init__(self):
        super(HexDocument, self).__init__()

    def do_document_changed(self, cdata, push_undo):
        self.emit('changed', cdata, push_undo)

class HexView(gtkhex.Hex):
    __gtype_name__ = "PyGtkHexView"

    def __init__(self):
        self._document = HexDocument()

        super(HexView, self).__init__(self._document)

        self.show_offsets(True)
        self.set_geometry(8, 5)
        self.set_read_only_mode(True)
        self._trapped = True

        self.changed_callback = None
        self._document.connect('changed', self.__wrap_on_changed)

        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)

        self.hdisp, self.adisp = self.get_children()[0:2]

        #self.hdisp.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        #self.adisp.add_events(gtk.gdk.BUTTON_PRESS_MASK)

        # Hex / Ascii
        self.hdisp.connect('button-press-event', self.__on_button_press, 0)
        self.adisp.connect('button-press-event', self.__on_button_press, 1)

    def __on_cut(self, action, typo):
        self.cut_to_clipboard()

    def __on_copy(self, action, typo):
        bounds = self.get_selection()

        if not bounds:
            return

        data = self._document.get_data(bounds[0], bounds[1])

        def hexdump():
            idx = 0
            out = ''

            for x in data:
                i = hex(ord(x))[2:].upper()

                if len(i) == 1:
                    out += "0"

                out += "%s" % i
                idx += 1

                if idx % 8 == 0:
                    out += '\n'
                    idx = 0
                else:
                    out += ' '
            return out

        def asciidump():
            idx = 0
            out = ''

            for x in data:
                i = x.isalpha() and x or '.'

                out += "%s" % i
                idx += 1

                if idx % 8 == 0:
                    out += '\n'
                    idx = 0
            return out

        if typo == 0:
            gtk.clipboard_get().set_text(hexdump())

        elif typo == 1:
            self.copy_to_clipboard()
        else:
            out = ''

            for h, a in zip(hexdump().splitlines(), asciidump().splitlines()):
                padding = 8 - len(a)
                out += h + (" " * ((padding * 3) - 1)) + "\t" + a + "\n"

            gtk.clipboard_get().set_text(out)

    def __on_bcopy(self, action, typo):
        self.__on_copy(action, 3)

    def __on_paste(self, action, typo):
        self.paste_from_clipboard()

    def __on_button_press(self, widget, evt, typo):
        if evt.button != 3:
            return

        menu = gtk.Menu()

        # OK show a popup to copy and paste
        # cut/copy/paste/delete

        txts = (_('Cu_t'), _('_Copy'), _('_Paste'), _('Copy from _both'))
        icons = (gtk.STOCK_CUT, gtk.STOCK_COPY, gtk.STOCK_PASTE, gtk.STOCK_COPY)
        cbcs = (self.__on_cut, self.__on_copy, self.__on_paste, self.__on_bcopy)

        clipboard_sel = gtk.clipboard_get().wait_for_text() and True or False

        idx = 0

        for txt, icon, cbc in zip(txts, icons, cbcs):
            action = gtk.Action(None, txt, None, icon)
            action.connect('activate', cbc, typo)

            item = action.create_menu_item()

            if not clipboard_sel and idx == 2:
                item.set_sensitive(False)

            menu.append(item)

            idx += 1

        menu.popup(None, None, None, evt.button, evt.time, None)
        menu.show_all()

    def __wrap_on_changed(self, document, cdata, push_undo):
        if callable(self.changed_callback) and self._trapped:
           self.changed_callback(document, cdata, push_undo)

        self._trapped = True

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
        self._trapped = False
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
