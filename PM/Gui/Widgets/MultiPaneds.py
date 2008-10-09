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

"""
Simple widgets that emulate the behaviour of a paned with multiple childs
"""

import gtk

# TODO: use metaclasses to zip the code!

class VMultiPaned(gtk.VPaned):
    def __init__(self):
        gtk.VPaned.__init__(self)

        self.current = self
        self.paneds = [self.current]

    def add_child(self, widget, resize=False, shrink=True):
        new_paned = gtk.VPaned()
        self.current.pack1(widget, resize, shrink)
        self.current.pack2(new_paned, False, False)

        self.current = new_paned

class HMultiPaned(gtk.HPaned):
    def __init__(self):
        gtk.HPaned.__init__(self)

        self.current = self
        self.paneds = [self.current]

    def add_child(self, widget, resize=False, shrink=True):
        new_paned = gtk.HPaned()
        self.current.pack1(widget, resize, shrink)
        self.current.pack2(new_paned, False, False)

        self.current = new_paned

if __name__ == "__main__":
    pan = MultiPaned()
    w = gtk.Window()
    w.add(pan)

    pan.add_child(gtk.Label("first"))
    pan.add_child(gtk.Label("second"))

    w.show_all()
    gtk.main()
