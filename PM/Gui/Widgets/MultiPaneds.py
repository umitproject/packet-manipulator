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

from PM.Core.Logger import log
from PM.Gui.Widgets.Expander import AnimatedExpander

class MultiPaned(object):
    def __init__(self):
        self.current = None
        self.paneds = []

    def add_child(self, widget, resize=False, shrink=True):
        if isinstance(widget, (gtk.Expander, AnimatedExpander)):
            widget.connect('activate', self.__on_expanded)
        else:
            log.debug('This is not a gtk.Expander neither AnimatedExpander')

    def remove_child(self, widget):
        i = len(self.paneds) - 1

        while i >= 0:
            curr = self.paneds[i]

            if curr.get_child1() is widget:
                last = curr.get_child2()
                curr.remove(last)

                root = curr.get_parent()
                root.remove(curr)
                root.add(last)

                del self.paneds[i]

                break

            i -= 1

    def __on_expanded(self, widget):
        for paned in self.paneds:
            w = paned.get_child1()

            if w is not widget:
                w = paned.get_child2()

                if w is not widget:
                    continue

            if not widget.get_expanded():
                cur_values = paned.child_get_property(w, 'resize'), \
                           paned.child_get_property(w, 'shrink')

                w.set_data('pm::old_state', cur_values)

                paned.child_set_property(w, 'resize', False)
                paned.child_set_property(w, 'shrink', False)

            else:
                old_values = w.get_data('pm::old_state')

                if not isinstance(old_values, tuple):
                    return

                paned.child_set_property(w, 'resize', old_values[0])
                paned.child_set_property(w, 'shrink', old_values[1])

            return

class VMultiPaned(gtk.VPaned, MultiPaned):
    def __init__(self):
        MultiPaned.__init__(self)
        gtk.VPaned.__init__(self)

        self.current = self
        self.paneds = [self.current]

    def add_child(self, widget, resize=False, shrink=True):
        new_paned = gtk.VPaned()

        self.current.pack1(widget, resize, shrink)
        self.current.pack2(new_paned, False, False)

        self.current = new_paned
        self.paneds.append(new_paned)

        MultiPaned.add_child(self, widget, resize, shrink)

class HMultiPaned(gtk.HPaned, MultiPaned):
    def __init__(self):
        MultiPaned.__init__(self)
        gtk.HPaned.__init__(self)

        self.current = self
        self.paneds = [self.current]

    def add_child(self, widget, resize=False, shrink=True):
        new_paned = gtk.HPaned()
        self.current.pack1(widget, resize, shrink)
        self.current.pack2(new_paned, False, False)

        self.current = new_paned

        MultiPaned.add_child(self, widget, resize, shrink)

if __name__ == "__main__":
    pan = VMultiPaned()
    w = gtk.Window()
    w.add(pan)

    def makebtn(pan):
        def rem(btn, pan):
            pan.remove_child(btn)

        btn = gtk.Button("Remove")
        btn.connect('clicked', rem, pan)

        pan.add_child(btn)


    makebtn(pan)
    makebtn(pan)
    makebtn(pan)
    makebtn(pan)

    pan.add_child(gtk.Label("first"))
    pan.add_child(gtk.Label("second"))

    w.show_all()
    gtk.main()
