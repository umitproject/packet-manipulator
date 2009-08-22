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
Docking windows module (it needs moo_stub module)
"""

import gtk
from umit.pm.gui.moo_stub import BigPaned, PaneLabel, PaneParams, \
                            PANE_POS_RIGHT, PANE_POS_LEFT, \
                            PANE_POS_TOP, PANE_POS_BOTTOM

POS_MAP = {
        gtk.POS_RIGHT  : PANE_POS_RIGHT,
        gtk.POS_LEFT   : PANE_POS_LEFT,
        gtk.POS_TOP    : PANE_POS_TOP,
        gtk.POS_BOTTOM : PANE_POS_BOTTOM
}

class UmitPaned(BigPaned):

    def __init__(self):
        BigPaned.__init__(self)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.set_property('enable-detaching', True)
        for pane in self.get_all_paneds():
            pane.set_pane_size(200)
            #pane.set_sticky_pane(True)
        self.show()

    def get_all_pos(self):
        return [gtk.POS_TOP, gtk.POS_BOTTOM, gtk.POS_LEFT, gtk.POS_RIGHT]

    def get_all_paneds(self):
        for pos in self.get_all_pos():
            yield self.get_paned(POS_MAP[pos])

    def add_view(self, view, removable=True):
        if view.tab_position is None:
            self.add_child(view.get_toplevel())
        else:
            POS = POS_MAP[view.tab_position]
            lab = PaneLabel(view.icon_name, None, view.label_text)
            view.get_toplevel()
            pane = self.insert_pane(view.get_toplevel(), lab, POS, POS)
            if not removable:
                pane.set_property('removable', False)
            pane.connect('remove', view.on_remove_attempt)
            self.show_all()

    def remove_view(self, view):
        self.remove_pane(view.get_toplevel())

    def detach_view(self, view, size=(400,300)):
        paned, pos = self.find_pane(view.get_toplevel())
        paned.detach_pane(pos)
        self._center_on_parent(view, size)

    def present_view(self, view):
        pane, pos = self.find_pane(view.get_toplevel())
        pane.present()

    def get_open_pane(self, name):
        POS = POS_MAP[name]
        paned = self.get_paned(POS)
        pane = paned.get_open_pane()
        return paned, pane

    def switch_next_pane(self, name):
        paned, pane = self.get_open_pane(name)
        if pane is None:
            num = -1
        else:
            num = pane.get_index()
        newnum = num + 1
        if newnum == paned.n_panes():
            newnum = 0
        newpane = paned.get_nth_pane(newnum)
        newpane.present()

    def switch_prev_pane(self, name):
        paned, pane = self.get_open_pane(name)
        if pane is None:
            num = paned.n_panes()
        else:
            num = pane.get_index()
        newnum = num - 1
        if newnum == -1:
            newnum = paned.n_panes() - 1
        newpane = paned.get_nth_pane(newnum)
        newpane.present()

    def _center_on_parent(self, view, size):
        gdkwindow = view.get_parent_window()
        px, py, pw, ph, pbd = view.svc.boss.get_window().window.get_geometry()
        w, h = size
        cx = (pw - w) / 2
        cy = (ph - h) / 2
        gdkwindow.move_resize(cx, cy, w, h)
        #gdkwindow.resize(w, h)


