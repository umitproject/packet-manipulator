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

import pango
import gtk
import os

from umit.pm.core.i18n import _
from umit.pm.core.const import PM_VERSION
from umit.pm.manager.preferencemanager import Prefs

from umit.pm.gui.core.views import UmitView
from umit.pm.gui.core.icons import get_pixbuf

class StatusView(gtk.ScrolledWindow):
    def __init__(self):
        super(StatusView, self).__init__()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.tag_table = gtk.TextTagTable()
        self.buffer = gtk.TextBuffer(self.tag_table)
        self.view = gtk.TextView(self.buffer)
        self.view.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.view.set_indent(4)

        Prefs()['gui.statustab.font'].connect(self.__modify_font)

        self.view.set_border_window_size(gtk.TEXT_WINDOW_LEFT, 16)
        self.view.set_editable(False)

        # Create various tags

        self.view.connect('expose-event', self.__redraw_left_window)
        self.view.connect('style-set', self.__on_style)
        self.view.connect('realize', self.__on_realize)
        self.add(self.view)

        self.icons = (
            get_pixbuf('info_small'),
            get_pixbuf('warning_small'),
            get_pixbuf('error_small')
        )

        self.lines = []

    def __modify_font(self, val):
        try:
            desc = pango.FontDescription(val)

            self.view.modify_font(desc)
            self.view.get_window(gtk.TEXT_WINDOW_LEFT).set_background(
                self.style.base[gtk.STATE_NORMAL]
            )
        except:
            return True

    def append(self, txt, type=0):
        if type < 0 or type > 2:
            type = 0

        self.lines.append(type)
        self.buffer.insert(self.buffer.get_end_iter(), txt + "\n")

    def info(self, txt):
        self.append(txt, 0)
    def warning(self, txt):
        self.append(txt, 1)
    def error(self, txt):
        self.append(txt, 2)

    def __on_style(self, widget, old):
        window = self.view.get_window(gtk.TEXT_WINDOW_LEFT)

        if window:
            window.set_background(self.style.base[gtk.STATE_NORMAL])

    def __on_realize(self, widget):
        self.__on_style(widget, None)

    def __redraw_left_window(self, widget, event):
        window = self.view.get_window(gtk.TEXT_WINDOW_LEFT)

        if event.window != window:
            return False

        cr = window.cairo_create()
        cr.save()

        area = event.area

        # Now get the first/last iters
        _, start_y = self.view.window_to_buffer_coords(gtk.TEXT_WINDOW_LEFT,
                                                         0, area.y)
        start_it, _ = self.view.get_line_at_y(start_y)

        _, end_y = self.view.window_to_buffer_coords(gtk.TEXT_WINDOW_LEFT, 0,
                                                       area.y + area.height - 1)
        end_it, _ = self.view.get_line_at_y(end_y)

        # Draw stuff
        for line in xrange(start_it.get_line(), end_it.get_line() + 1, 1):
            if line >= len(self.lines):
                continue

            pix = self.icons[self.lines[line]]
            y, _ = self.view.get_line_yrange(self.buffer.get_iter_at_line(line))
            _, y = self.view.buffer_to_window_coords(gtk.TEXT_WINDOW_LEFT, 0, y)

            cr.set_source_pixbuf(pix, 0, y)
            cr.paint()

        cr.restore()

        return False

class StatusTab(UmitView):
    icon_name = gtk.STOCK_INFO
    tab_position = gtk.POS_BOTTOM
    label_text = _('Status')
    name = 'StatusTab'

    def create_ui(self):
        self.status = StatusView()

        self.status.info(_("PacketManipulator %s started on %s") % (PM_VERSION,
                                                                    os.name))
        self.status.info(_("Using %s as backend") % \
                         Prefs()['backend.system'].value)

        self.status.info(_("What do you wanna pwn today?"))

        self._main_widget.add(self.status)
        self._main_widget.show_all()
