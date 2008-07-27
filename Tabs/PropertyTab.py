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
from views import UmitView
from widgets.PropertyGrid import PropertyGrid
from Tabs.MainTab import SessionPage

class PropertyTab(UmitView):
    label_text = "Properties"
    icon_name = gtk.STOCK_INDEX

    def create_ui(self):
        self.grid = PropertyGrid()
        self._main_widget.add(self.grid)
        self._main_widget.show_all()

        # Start disabled
        self._main_widget.set_sensitive(False)

    def connect_tab_signals(self):
        # I need to connect the session-notebook
        # signals from main tab here so we have
        # overriden this method to avoid errors

        from App import PMApp
        tab = PMApp().main_window.main_tab
        tab.session_notebook.connect('switch-page', self.__on_repopulate)

    def __on_repopulate(self, sess_nb, page, num):
        page = sess_nb.get_nth_page(num)

        self._main_widget.set_sensitive(False)
        self.grid.clear()

        if isinstance(page, SessionPage):
            # We need to get the protocol instance
            # so we can repopulate the PropertyGrid

            self.grid.populate(page.protocol)
            self._main_widget.set_sensitive(True)
