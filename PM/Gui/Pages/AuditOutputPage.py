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

from PM.Core.I18N import _
from PM.Core.Logger import log

from PM.Gui.Core.Icons import get_pixbuf
from PM.Gui.Pages.Base import Perspective
from PM.Gui.Widgets.FilterEntry import FilterEntry

ICONS = [gtk.STOCK_DIALOG_INFO,
         gtk.STOCK_DIALOG_WARNING,
         gtk.STOCK_DIALOG_ERROR]

# To convert STATUS_* to ICONS
STATUS = [2, 2, 2, 2, 1, 1, 0, 0, 0]

class AuditOutputTree(gtk.TreeView):
    def __init__(self):
        self.store = gtk.ListStore(int, str)
        gtk.TreeView.__init__(self, self.store)

        self.insert_column_with_data_func(-1, '', gtk.CellRendererPixbuf(),
                                          self.__pix_func)
        self.insert_column_with_attributes(-1, '', gtk.CellRendererText(),
                                           markup=1)

        self.get_column(0).set_expand(False)
        self.get_column(1).set_expand(True)

        self.set_rules_hint(True)
        self.set_headers_visible(False)

    def __pix_func(self, col, cell, model, iter):
        value = model.get_value(iter, 0)
        cell.set_property('stock-id', ICONS[STATUS[value]])

    def user_msg(self, msg, severity=5, facility=None):
        message = (facility and "<tt><b>" + facility + ".</b></tt>" or '') + msg
        self.store.append([severity, message])

class AuditOutput(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self, False, 2)

        self.entry = FilterEntry()
        self.tree = AuditOutputTree()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.tree)

        self.pack_start(self.entry, False, False)
        self.pack_end(sw)

class AuditOutputPage(Perspective):
    icon = gtk.STOCK_INDEX
    title = _('Audit status')

    def create_ui(self):
        self.output = AuditOutput()

        self.pack_start(self.output)
        self.show_all()

    def user_msg(self, msg, severity=5, facility=None):
        "wrapper to simplify the code"
        self.output.tree.user_msg(msg, severity, facility)
