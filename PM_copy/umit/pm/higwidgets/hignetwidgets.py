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

"""
This module includes:
- HIGIpEntry a simple IP widget
"""

import re
import gtk
import gobject

class HIGGenericEntry(gtk.HBox):
    __gtype_name__ = "HIGIpEntry"
    __gsignals__ = {
        'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
    }
    regex = re.compile("\\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b")
    groups = 4
    maxlength = 3
    separator = '.'

    def __init__(self):
        gtk.HBox.__init__(self, False, 2)

        self._current = None
        self._entries = [gtk.Entry(self.maxlength) for i in xrange(self.groups)]
        self._img_error = gtk.image_new_from_stock(
                gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_MENU
        )
        self._img_ok = gtk.image_new_from_stock(
                gtk.STOCK_APPLY, gtk.ICON_SIZE_MENU
        )

        self.has_frame = True

        redraw = lambda x, y, root: root.queue_draw()

        for entry in self._entries:
            entry.connect('focus-in-event', redraw, self)
            entry.connect('focus-out-event', redraw, self)
            entry.connect('key-press-event', self.__on_key_press)
            entry.connect('key-release-event', self.__on_key_release)
            entry.set_width_chars(self.maxlength)

        self.__pack_widgets()

    def modify_font(self, font_desc):
        for entry in self._entries:
            entry.modify_font(font_desc)

    def __pack_widgets(self):
        self.set_border_width(4)

        for e in self._entries:
            e.set_alignment(0.5)
            e.set_has_frame(False)
            e.set_width_chars(self.maxlength)

        idx = 0
        for i in xrange(self.groups):
            self.pack_start(self._entries[idx], False, False, 0)

            if idx != self.groups - 1:
                self.pack_start(gtk.Label(self.separator), False, False, 0)

            idx += 1

        self.pack_start(self._img_error, False, False, 0)
        self.pack_start(self._img_ok, False, False, 0)
        self.show_all()

    def do_realize(self):
        gtk.HBox.do_realize(self)
        self._img_ok.hide()

    def __on_key_press(self, widget, evt):
        if evt.keyval == gtk.keysyms.BackSpace or \
           evt.keyval == gtk.keysyms.Left:
            self.__move_next(False)
            return True

        elif evt.keyval == gtk.keysyms.Tab or \
           evt.keyval == gtk.keysyms.Right:
            self.__move_next()
            return True

        elif evt.keyval <= 256 and chr(evt.keyval) == self.separator:
            self.__move_next()
            return True

        return False

    def __on_key_release(self, widget, evt):
        if evt.keyval <= 256 and chr(evt.keyval).isdigit() and \
             widget.get_property('cursor_position') == (self.groups - 1):
            self.__move_next()

        self.__validate()
        return False

    def __move_next(self, up=True):
        if not self._current:
            if up:
                i = -1
            else:
                i = len(self._entries)
        else:
            i = self._entries.index(self._current)

        if up:
            i += 1
        else:
            i -= 1

        if i < 0 or i >= self.groups:
            i = 0

        self._entries[i].grab_focus()
        self._current = self._entries[i]

    def __validate(self):
        if self.regex.match(self.text):
            self._img_error.hide()
            self._img_ok.show()
            self.emit('changed')
        else:
            self._img_error.show()
            self._img_ok.hide()

    def do_expose_event(self, evt):
        alloc = self.allocation
        rect = gtk.gdk.Rectangle(alloc.x, alloc.y, alloc.width, alloc.height)

        if not self._current:
            self._current = self._entries[0]

        if self.has_frame:
            self.style.paint_flat_box(
                self.window,
                self._current.state,
                self._current.get_property('shadow_type'),
                alloc,
                self._current,
                'entry_bg',
                rect.x, rect.y, rect.width, rect.height
            )

            self.style.paint_shadow(
                self.window,
                self._current.state,
                self._current.get_property('shadow_type'),
                alloc,
                self._current,
                'entry',
                rect.x, rect.y, rect.width, rect.height
            )

        return gtk.Bin.do_expose_event(self, evt)

    def get_text(self):
        return self.separator.join(map(lambda e: e.get_text(), self._entries))

    def set_text(self, txt):
        t = txt.split(self.separator)

        if len(t) == self.groups:
            [e.set_text(v) for e, v in zip(self._entries, t)]

    def set_has_frame(self, val):
        self.has_frame = val

    def get_has_frame(self):
        return self.has_frame

    text = property(get_text, set_text)

gobject.type_register(HIGGenericEntry)

HIGIpEntry = HIGGenericEntry

class HIGIpv6Entry(HIGGenericEntry):
    regex = re.compile('^[A-f0-9]{1,4}([:]{1,2}[A-f0-9]{1,4})+$')
    groups = 8
    maxlength = 4
    separator = ':'

class HIGMacEntry(HIGGenericEntry):
    regex = re.compile('([0-9a-fA-F]{2}([:-]|$)){6}')
    groups = 6
    maxlength = 2
    separator = ':'

if __name__ == "__main__":
    w = gtk.Window()

    bb = gtk.VBox()
    bb.pack_start(gtk.Label("This is a dummy ip widget:"), False, False)
    bb.pack_start(HIGIpEntry())

    w.add(bb)
    w.show_all()

    w.connect('delete-event', lambda *w: gtk.main_quit())
    gtk.main()
