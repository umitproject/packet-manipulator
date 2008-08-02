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

class Page(gtk.Table):
    widgets = [

    ]
    def __init__(self):
        super(Page, self).__init__(max(len(self.widgets), 1), 2)

        self.set_border_width(4)
        self.create_ui()
        self.show_all()

    def create_ui(self):
        idx = 0

        for (lbl, widget) in self.widgets:

            if lbl:
                label = gtk.Label(lbl)
                label.set_use_markup(True)
                label.set_alignment(0, 0.5)

                self.attach(label, 0, 1, idx, idx + 1, yoptions=gtk.SHRINK)
                self.attach(widget, 1, 2, idx, idx + 1, yoptions=gtk.SHRINK)
            else:
                self.attach(widget, 0, 2, idx, idx + 1, yoptions=gtk.SHRINK)

            idx += 1

class GUIPage(Page):
    widgets = [
        (None, gtk.CheckButton('Use docking windows')),
        ('HexView Font:', gtk.FontButton()),
        ('Bytes per line:', gtk.SpinButton(gtk.Adjustment(8, 1, 16, 1, 1)))
    ]

class PreferenceDialog(gtk.Dialog):
    def __init__(self, parent):
        super(PreferenceDialog, self).__init__(
            "Preferences - PacketManipulator", parent,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_REJECT,
             gtk.STOCK_APPLY, gtk.RESPONSE_ACCEPT)
        )

        self.store = gtk.ListStore(str, str)
        self.tree = gtk.TreeView(self.store)

        self.tree.append_column(
            gtk.TreeViewColumn('', gtk.CellRendererPixbuf(), stock_id=0))

        self.tree.append_column(
            gtk.TreeViewColumn('', gtk.CellRendererText(), text=1))

        self.tree.set_headers_visible(False)
        self.tree.set_rules_hint(True)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.tree)

        hbox = gtk.HBox()
        hbox.pack_start(sw, False, False)

        self.notebook = gtk.Notebook()
        self.notebook.set_show_border(False)
        self.notebook.set_show_tabs(False)
        hbox.pack_end(self.notebook)

        self.__populate()

        hbox.show_all()
        self.vbox.pack_start(hbox)
        self.vbox.set_border_width(4)
        self.vbox.set_spacing(4)

    def __populate(self):
        self.store.append([gtk.STOCK_PREFERENCES, "GUI Preferences"])
        self.notebook.append_page(GUIPage())

if __name__ == "__main__":
    d = PreferenceDialog(None)
    d.show()
    gtk.main()
