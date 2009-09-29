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
Simple widgets that emulate the behaviour of a paned with multiple childs
"""

import gtk

from umit.pm.core.logger import log
from umit.pm.gui.widgets.expander import AnimatedExpander

class MultiPaned(object):
    def __init__(self):
        self.current = None
        self.paneds = []
        self.active_widget = None

    def add_child(self, widget, resize=False):
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

    def _get_paned_for(self, widget):
        for paned in self.paneds:
            if paned.get_child1() is widget:
                return paned

    def __on_expanded(self, widget):
        if not widget.get_expanded():
            self._minimize_widget(widget)
        else:
            self._set_active(widget)

    def _save_state(self, paned, w):
        cur_values = paned.child_get_property(w, 'resize')
        w.set_data('pm::old_resize', cur_values)

    def _set_state(self, paned, w, resize=None):
        if resize:
            paned.set_property('position', paned.get_property('max-position'))
        else:
            paned.set_property('position', 0)

        if resize != None:
            paned.child_set_property(w, 'resize', resize)
        else:
            cur_values = w.get_data('pm::old_resize')

            if isinstance(cur_values, bool):
                paned.child_set_property(w, 'resize', cur_values)

    def _restore_widget(self, w):
        paned = self._get_paned_for(w)

        if paned:
            self._set_state(paned, w)

    def _set_active(self, w):
        if self.active_widget:
            self._restore_widget(self.active_widget)

        paned = self._get_paned_for(w)

        if paned:
            self._save_state(paned, w)
            self._set_state(paned, w, True)

        self.active_widget = w

    def _minimize_widget(self, w):
        paned = self._get_paned_for(w)

        if paned:
            self._save_state(paned, w)
            self._set_state(paned, w, False)

        if self.active_widget is w:
            self.active_widget = None

class VMultiPaned(gtk.VPaned, MultiPaned):
    def __init__(self):
        MultiPaned.__init__(self)
        gtk.VPaned.__init__(self)

        self.current = self
        self.paneds = [self.current]

    def add_child(self, widget, resize=False):
        new_paned = gtk.VPaned()
        new_paned.show()

        self.current.pack1(widget, resize, False)
        self.current.pack2(new_paned, False, False)
        self.current.show()

        self.current = new_paned
        self.paneds.append(new_paned)

        MultiPaned.add_child(self, widget, resize)

class HMultiPaned(gtk.HPaned, MultiPaned):
    def __init__(self):
        MultiPaned.__init__(self)
        gtk.HPaned.__init__(self)

        self.current = self
        self.paneds = [self.current]

    def add_child(self, widget, resize=False):
        new_paned = gtk.HPaned()

        self.current.pack1(widget, resize, False)
        self.current.pack2(new_paned, False, False)
        self.current.show()

        self.current = new_paned
        self.paneds.append(new_paned)

        MultiPaned.add_child(self, widget, resize)

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
