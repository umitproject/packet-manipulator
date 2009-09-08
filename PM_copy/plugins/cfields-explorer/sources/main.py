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
import pango

from umit.pm.core.logger import log

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.plugins.engine import Plugin

from umit.pm.gui.sessions import SessionType
from umit.pm.gui.pages.base import Perspective

from umit.pm.core.errors import PMErrorException

class Explorer(Perspective):
    icon = gtk.STOCK_INFO
    title = 'CFields explorer'

    def create_ui(self):
        self.store = gtk.ListStore(str, str)
        self.tree = gtk.TreeView(self.store)

        rend = gtk.CellRendererText()
        self.tree.append_column(gtk.TreeViewColumn('Key', rend, text=0))
        self.tree.append_column(gtk.TreeViewColumn('Value', rend, text=1))
        self.tree.set_rules_hint(True)
        self.tree.modify_font(pango.FontDescription('Monospace 9'))

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.tree)

        self.pack_start(sw)
        self.show_all()

        self.session.editor_cbs.append(self.repopulate)

    def repopulate(self):
        if not self.session.packet:
            return

        self.store.clear()

        for k, v in self.session.packet.cfields.items():
            self.store.append([k, repr(v)])

class CFieldsExplorer(Plugin):
    def start(self, reader):
        PMApp().main_window.bind_session(SessionType.SNIFF_SESSION, Explorer)

    def stop(self):
        PMApp().main_window.unbind_session(SessionType.SNIFF_SESSION, Explorer)

__plugins__ = [CFieldsExplorer]
