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
import sys

from collections import defaultdict

from PM.Core.Logger import log

from PM.Gui.Core.App import PMApp
from PM.Gui.Core.Views import UmitView
from PM.Gui.Plugins.Engine import Plugin
from PM.Gui.Sessions.SniffSession import SniffSession

_ = str

try:
    import GeoIP
except ImportError:
    raise Exception("Cannot load GeoIP.\n"
                    "You should install python-geoip to use this plugin")

class GeoTab(UmitView):
    icon_name = gtk.STOCK_INFO
    tab_position = gtk.POS_LEFT
    label_text = _('Geo stats')
    name = 'GeoTab'

    def create_ui(self):
        self.locator = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # Country / IP
        self.store = gtk.ListStore(str, str)
        self.tree = gtk.TreeView(self.store)

        self.tree.append_column(gtk.TreeViewColumn('Country', gtk.CellRendererText(), text=0))
        self.tree.append_column(gtk.TreeViewColumn('IP', gtk.CellRendererText(), text=1))

        sw.add(self.tree)

        self._main_widget.add(sw)
        self._main_widget.show_all()

        tab = PMApp().main_window.get_tab("MainTab")
        tab.session_notebook.connect('switch-page', self.__on_switch_page)

    def __on_switch_page(self, sess_nb, page, num):
        self.store.clear()
        page = sess_nb.get_nth_page(num)

        if isinstance(page, SniffSession):
            self.__repopulate(page.context.data)

    def __repopulate(self, packets):
        countries = defaultdict(int)

        for metapacket in packets:
            is_ip = False
            query = metapacket.get_source()

            if query.count('.') == 4:
                is_ip = True

            # Check others functions
            countries[self.locator.country_code_by_addr(query)] += 1

        items = [(v, k) for k, v in countries.items() if k]
        items.sort()

        for hits, name in items:
            self.store.append([name, str(hits)])

class GeoStats(Plugin):
    def start(self, reader):
        catalog = reader.bind_translation("geostats")

        if catalog:
            global _
            _ = catalog.gettext

        self.geo_tab = GeoTab()
        PMApp().main_window.register_tab(self.geo_tab, True)

    def stop(self):
        PMApp().main_window.deregister_tab(self.geo_tab)

__plugins__ = [GeoStats]
