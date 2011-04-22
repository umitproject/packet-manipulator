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
import gobject

from umit.pm.core.i18n import _
from umit.pm.gui.core.views import UmitView

class TerminalWidget(gtk.Bin):
    __gtype_name__ = "TerminalWidget"

    def __init__(self):
        super(TerminalWidget, self).__init__()
        self.__termbox = gtk.HBox()
        self.add(self.__termbox)

        try:
            import vte

            self.term = vte.Terminal()
            self.term.fork_command()
            self.term.connect('child-exited',
                              lambda *w: self.term.fork_command())

            self.__scroll = gtk.VScrollbar(self.term.get_adjustment())
            border = gtk.Frame()
            border.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            border.add(self.term)

            self.__termbox.pack_start(border)
            self.__termbox.pack_start(self.__scroll, False)

            self.term.set_size_request(0, 0)
        except ImportError:
            label = gtk.Label(
                _("<b>Loser!</b> You don't have vte python bindings installed.\n" \
                "Download it from <tt>http://ftp.acc.umu.se/pub/GNOME/sources/vte/</tt>")
            )

            label.set_use_markup(True)
            label.set_selectable(True)

            self.__termbox.pack_start(label)

        self.show_all()

    def do_size_request(self, req):
        w, h = self.__termbox.size_request()
        req.width = w
        req.height = h

    def do_size_allocate(self, alloc):
        return self.__termbox.size_allocate(alloc)

gobject.type_register(TerminalWidget)

class VteTab(UmitView):
    icon_name = 'terminal_small'
    label_text = _('Terminal')
    name = 'TerminalTab'
    tab_position = gtk.POS_BOTTOM

    def create_ui(self):
        self._main_widget.add(TerminalWidget())
        self._main_widget.show_all()
