#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
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
GDL (Gnome Docking Library) paned implementation
"""

# TODO: implement layout saving/loading

import gtk
import gdl

from umit.pm.core.logger import log
from umit.pm.gui.core.app import PMApp

class UmitPaned(gtk.HBox):
    """Fallback UmitPaned based on gtk.Paned
    """

    def __init__(self):
        super(UmitPaned, self).__init__(False, 2)

        self.dock = gdl.Dock()
        self.docklayout = gdl.DockLayout(self.dock)
        self.dockbar = gdl.DockBar(self.dock)

        self.dockbar.show_all()

        self.ph_r = gdl.DockPlaceholder('r', self.dock, gdl.DOCK_RIGHT, False)
        self.ph_l = gdl.DockPlaceholder('r', self.dock, gdl.DOCK_LEFT, False)
        self.ph_t = gdl.DockPlaceholder('t', self.dock, gdl.DOCK_TOP, False)
        self.ph_b = gdl.DockPlaceholder('b', self.dock, gdl.DOCK_BOTTOM, False)

        self.ph_r.props.width = 150
        self.ph_l.props.width = 150
        self.ph_t.props.height = 300
        self.ph_b.props.height = 300

        self.central = None
        self.tab_map = {}

        self.pack_start(self.dockbar, False, False, 0)
        self.pack_end(self.dock)

        self.show_all()

    def add_view(self, tab, unused=False):
        widget = tab.get_toplevel()

        if not tab.tab_position:
            # Ok this is the central widget
            item = gdl.DockItem('MainTab', 'MainTab', tab.icon_name,
                                gdl.DOCK_ITEM_BEH_LOCKED | \
                                #gdl.DOCK_ITEM_BEH_NO_GRIP | \
                                gdl.DOCK_ITEM_BEH_CANT_CLOSE | \
                                gdl.DOCK_ITEM_BEH_CANT_ICONIFY)
            item.add(widget)
            item.show()

            self.central = item
            self.dock.add_item(item, gdl.DOCK_CENTER)

            log.debug('Setting central widget to %s' % self.central)

            return

        if not self.central:
            log.error('Central widget has not be set yet.')
            raise Exception('Central widget has not be set yet')

        item = gdl.DockItem(tab.label_text, tab.label_text, tab.icon_name,
                            gdl.DOCK_ITEM_BEH_NORMAL |
                            gdl.DOCK_ITEM_BEH_CANT_CLOSE)
        item.add(widget)
        item.show()

        ph = None
        pos = tab.tab_position

        log.debug("Item %s created. Docking to %s" % (item, pos))

        if pos is gtk.POS_LEFT:
            ph = self.ph_l
            pos = gdl.DOCK_LEFT
        elif pos is gtk.POS_RIGHT:
            ph = self.ph_r
            pos = gdl.DOCK_RIGHT
        elif pos is gtk.POS_TOP:
            ph = self.ph_t
            pos = gdl.DOCK_TOP
        elif pos is gtk.POS_BOTTOM:
            ph = self.ph_b
            pos = gdl.DOCK_BOTTOM

        ph.add(item)
        self.tab_map[tab] = item

    def remove_view(self, tab):
        try:
            item = self.tab_map[tab]

            item.hide_item()
            item.remove(tab.get_toplevel())
            item.unbind()

            del self.tab_map[tab]

            log.debug('Tab %s with item %s removed' %  (tab, item))
        except ValueError:
            log.debug('Tab %s not found' % tab)