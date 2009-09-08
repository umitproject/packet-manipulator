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

"""
A simple docking windows fallback replacement based on gtk.Notebook
"""

import gtk

class UmitPaned(gtk.VBox):
    """Fallback UmitPaned based on gtk.Paned
    """

    def __init__(self):
        super(UmitPaned, self).__init__(2, False)

        self.hpaned = gtk.HPaned()
        self.vpaned = gtk.VPaned()

        self.hnotebook = gtk.Notebook()
        self.vnotebook = gtk.Notebook()

        self.vnotebook.set_tab_pos(gtk.POS_BOTTOM)

        self.pack_start(self.vpaned)
        self.vpaned.pack2(self.vnotebook, False, True) # bottom

        self.vpaned.add1(self.hpaned)
        self.hpaned.pack1(self.hnotebook, False, True) # left

        self.show_all()

    def add_view(self, tab, unused=False):
        widget = tab.get_toplevel()

        if not tab.tab_position:
            if not self.hpaned.get_child2():
                self.hpaned.pack2(widget, True, False)
                return

        label = gtk.HBox()

        image = gtk.image_new_from_stock(tab.icon_name, gtk.ICON_SIZE_MENU)

        pos = tab.tab_position

        label.pack_start(image, False, False)
        label.pack_start(gtk.Label(tab.label_text))
        label.show_all()

        #print "Adding widget", widget, "to", pos

        if pos == gtk.POS_RIGHT or pos == gtk.POS_LEFT:
            self.hnotebook.append_page(widget, label)
            self.hnotebook.set_tab_reorderable(widget, True)
        elif pos == gtk.POS_TOP or pos == gtk.POS_BOTTOM:
            self.vnotebook.append_page(widget, label)
            self.vnotebook.set_tab_reorderable(widget, True)

    def remove_view(self, tab):
        pos = tab.tab_position

        if pos == gtk.POS_RIGHT or pos == gtk.POS_LEFT:
            nb = self.hnotebook
        elif pos == gtk.POS_TOP or pos == gtk.POS_BOTTOM:
            nb = self.vnotebook

        num = nb.page_num(tab.get_toplevel())
        if num > -1:
            nb.remove_page(num)
        else:
            raise Exception("Cannot found the widget")

if __name__ == "__main__":
    w = gtk.Window()
    p = UmitPaned()
    p.add_view("Top", gtk.Label("miao"))
    p.add_view("Center", gtk.Label("Center"))
    p.add_view("Right", gtk.Label("miao"))
    w.add(p)
    w.show_all()
    gtk.main()
