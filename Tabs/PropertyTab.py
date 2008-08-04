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
import Backend

from views import UmitView
from widgets.PropertyGrid import PropertyGrid
from Tabs.MainTab import SessionPage

class PropertyTab(UmitView):
    label_text = "Properties"
    icon_name = gtk.STOCK_INDEX
    tab_position = gtk.POS_RIGHT

    def create_ui(self):
        self.grid = PropertyGrid()
        self.grid.tree.connect('finish-edit', self.__redraw_hex_view)
        self.grid.tree.connect('field-selected', self.__on_field_selected)

        self._main_widget.add(self.grid)
        self._main_widget.show_all()

        # Start disabled
        self._main_widget.set_sensitive(False)

    def connect_tab_signals(self):
        # I need to connect the session-notebook
        # signals from main tab here so we have
        # overriden this method to avoid errors

        from App import PMApp
        tab = PMApp().main_window.get_tab("MainTab")
        tab.session_notebook.connect('switch-page', self.__on_repopulate)

    def __on_repopulate(self, sess_nb, page, num):
        page = sess_nb.get_nth_page(num)

        self._main_widget.set_sensitive(False)
        self.grid.clear()

        if isinstance(page, SessionPage):
            # We need to get the protocol instance
            # from selection or from the first iter
            # so we can repopulate the PropertyGrid
            
            proto = page.proto_hierarchy.get_active_protocol()
            
            self.grid.populate(proto)
            self._main_widget.set_sensitive(True)

    def __redraw_hex_view(self, tree, entry_destroyed):
        # This is called when the user end the edit action on the PropertyGrid
        # and we could redraw the entire hexview to show changes
        # The tree argument is the PropertyGridTree object

        from App import PMApp
        tab = PMApp().main_window.get_tab("MainTab")
        page = tab.session_notebook.get_current_session()

        if page:
            page.redraw_hexview()

            # Now reselect the blocks
            self.__on_field_selected(self.grid.tree, *self.grid.tree.get_selected_field())

    def __on_field_selected(self, tree, proto=None, field=None):
        if not proto or not field:
            return

        # We should select also the bounds in HexView
        from App import PMApp
        tab = PMApp().main_window.get_tab("MainTab")
        page = tab.session_notebook.get_current_session()

        if page:
            start  = Backend.get_field_offset(proto, field)
            length = Backend.get_field_size(proto, field)

            page.hexview.select_block(start / 8, max(length / 8, 1))
