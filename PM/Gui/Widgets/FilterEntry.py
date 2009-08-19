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

import gtk
import gobject

class FilterEntry(gtk.HBox):
    __gtype_name__ = "FilterEntry"

    def __init__(self):
        super(FilterEntry, self).__init__(False, 2)

        self.set_border_width(4)

        self._entry = gtk.Entry()
        self._box = gtk.EventBox()
        self._box.add(gtk.image_new_from_stock(gtk.STOCK_CLEAR,
                                               gtk.ICON_SIZE_MENU))

        self._entry.set_has_frame(False)

        self.pack_start(self._entry)
        self.pack_end(self._box, False, False)

        self._box.connect('button-release-event', self.__on_button_release)
        self._entry.connect('changed', self.__on_update)

        self._colors = None

    def do_realize(self):
        gtk.HBox.do_realize(self)

        self._colors = (
            self.style.white,
            gtk.gdk.color_parse("#FEFEDC")
        )

        self.__on_update(self._entry)

    def do_expose_event(self, evt):
        alloc = self.allocation
        rect = gtk.gdk.Rectangle(alloc.x, alloc.y, alloc.width, alloc.height)

        self.style.paint_flat_box(
            self.window,
            self._entry.state,
            self._entry.get_property('shadow_type'),
            alloc,
            self._entry,
            'entry_bg',
            rect.x, rect.y, rect.width, rect.height
        )

        self.style.paint_shadow(
            self.window,
            self._entry.state,
            self._entry.get_property('shadow_type'),
            alloc,
            self._entry,
            'entry',
            rect.x, rect.y, rect.width, rect.height
        )

        return gtk.HBox.do_expose_event(self, evt)

    def __on_button_release(self, image, evt):
        if evt.button == 1:
            self._entry.set_text('')

    def __on_update(self, entry):
        if self._entry.get_text():
            color = self._colors[1]
        else:
            color = self._colors[0]

        self._entry.modify_base(gtk.STATE_NORMAL, color)
        self._box.modify_bg(gtk.STATE_NORMAL, color)
        self.modify_base(gtk.STATE_NORMAL, color)

    def get_text(self):
        return self._entry.get_text()

    def set_text(self, txt):
        self._entry.set_text(txt)

    def get_entry(self):
        return self._entry

gobject.type_register(FilterEntry)
