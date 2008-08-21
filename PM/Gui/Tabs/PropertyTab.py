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

from PM import Backend
from PM.Core.I18N import _
from PM.Core.Logger import log

from PM.Gui.Core.App import PMApp
from PM.Gui.Core.Views import UmitView
from PM.Gui.Widgets.PropertyGrid import PropertyGrid
from PM.Gui.Tabs.MainTab import Session

class PropertyTab(UmitView):
    label_text = _('Properties')
    name = 'PropertyTab'
    icon_name = gtk.STOCK_INDEX
    tab_position = gtk.POS_RIGHT

    def create_ui(self):
        self.grid = PropertyGrid()
        self.grid.tree.connect('finish-edit', self.__redraw_hex_view)
        self.grid.tree.connect('field-selected', self.__on_field_selected)

        self._main_widget.add(self.grid)
        self._main_widget.show_all()

        self.prev_page = None
        self.change_id = None

        self.notify = {}

        # Start disabled
        self._main_widget.set_sensitive(False)

    def connect_tab_signals(self):
        # I need to connect the session-notebook
        # signals from main tab here so we have
        # overriden this method to avoid errors

        tab = PMApp().main_window.get_tab("MainTab")
        tab.session_notebook.connect('switch-page', self.__on_repopulate)

    def register_notify_for(self, packet, callback):
        if packet in self.notify:
            self.notify[packet].append(callback)
        else:
            self.notify[packet] = [callback]

        log.debug("%d callbacks for %s" % (len(self.notify[packet]), packet))
    
    def remove_notify_for(self, packet, callback):
        if packet in self.notify:
            self.notify[packet].remove(callback)

            log.debug("Removing callback for %s" % packet)

            if not self.notify[packet]:
                del self.notify[packet]

                log.debug("No callbacks for %s" % packet)

    def __on_repopulate(self, sess_nb, page, num):
        page = sess_nb.get_nth_page(num)

        self._main_widget.set_sensitive(False)
        self.grid.clear()

        if isinstance(page, Session):
            # We need to get the protocol instance
            # from selection or from the first iter
            # so we can repopulate the PropertyGrid
            
            packet, proto = page.packet_page.proto_hierarchy.get_active_protocol()

            if self.prev_page and self.change_id:
                sel = self.prev_page.packet_page.proto_hierarchy.tree.get_selection()
                if sel:
                    sel.disconnect(self.change_id)

            self.prev_page = page
            self.change_id = page.packet_page.proto_hierarchy.tree.get_selection().connect('changed',
                                                               self.__on_hierarchy_selection_changed)
            
            if not proto and page.packet:
                packet = page.packet
                proto = page.packet.root

            self.grid.populate(packet, proto)
            self._main_widget.set_sensitive(True)

    def __on_hierarchy_selection_changed(self, selection):
        packet, proto = self.prev_page.packet_page.proto_hierarchy.get_active_protocol()

        if not proto:
            return
        
        self.grid.clear()
        self.grid.populate(packet, proto)

        self._main_widget.set_sensitive(True)

    def __redraw_hex_view(self, tree, entry_destroyed):
        # This is called when the user end the edit action on the PropertyGrid
        # and we could redraw the entire hexview to show changes
        # The tree argument is the PropertyGridTree object

        tab = PMApp().main_window.get_tab("MainTab")
        page = tab.session_notebook.get_current_session()

        # FIXME: check if the packet page object is avaiable
        # within this session or use isisntance(SessionPage, SequencePage)
        if page:
            # No reload to avoid repopulating
            page.packet_page.redraw_hexview()

            packet, proto, field = self.grid.tree.get_selected_field()
            
            if packet in self.notify:
                for cb in self.notify[packet]:
                    cb(packet, proto, field, True)

            # Now reselect the blocks
            self.__on_field_selected(self.grid.tree, packet, proto, field)

    def __on_field_selected(self, tree, packet=None, proto=None, field=None):
        if not proto or not field:
            return

        if packet in self.notify:
            for cb in self.notify[packet]:
                cb(packet, proto, field, False)

        # We should select also the bounds in HexView
        tab = PMApp().main_window.get_tab("MainTab")
        page = tab.session_notebook.get_current_session()

        if page:
            start  = Backend.get_field_offset(packet, proto, field)
            length = Backend.get_field_size(proto, field)

            page.packet_page.hexview.select_block(start / 8, max(length / 8, 1))
