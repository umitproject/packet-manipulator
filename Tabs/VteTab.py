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

import vte
import gtk
import gobject

from views import UmitView

class TerminalWidget(gtk.Bin):
    def __init__(self):
        super(TerminalWidget, self).__init__()

        self.term = vte.Terminal()
        self.term.fork_command()

        self.__termbox = gtk.HBox()
        self.__scroll = gtk.VScrollbar(self.term.get_adjustment())
        border = gtk.Frame()
        border.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        border.add(self.term)
        self.__termbox.pack_start(border)
        self.__termbox.pack_start(self.__scroll, False)
        self.add(self.__termbox)

    def do_size_request(self, req):
        (w,h) = self.__termbox.size_request()
        req.width = w
        req.height = h

    def do_size_allocate(self, alloc):
        self.allocation = alloc
        wid_req = self.__termbox.size_allocate(alloc)

gobject.type_register(TerminalWidget)

class VteTab(UmitView):
    icon_name = gtk.STOCK_OK
    label_text = "Terminal"

    def create_ui(self):
        self._main_widget.add(TerminalWidget())
        self._main_widget.show_all()
