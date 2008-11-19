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

from PM import Backend
from PM.Core.I18N import _
from collections import defaultdict

from PM.Gui.Core.Views import UmitView
from PM.Gui.Core.Icons import get_pixbuf
   
class ProtocolTree(gtk.VBox):
    COL_PIX = 0
    COL_STR = 1
    COL_OBJ = 2

    def __init__(self):
        super(ProtocolTree, self).__init__(False, 2)
        
        toolbar = gtk.Toolbar()
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        
        stocks = (gtk.STOCK_SORT_ASCENDING,
                  gtk.STOCK_SORT_DESCENDING,
                  gtk.STOCK_CONVERT)
        
        callbacks = (self.__on_sort_ascending,
                     self.__on_sort_descending,
                     self.__on_sort_layer)

        tooltips = (_('Sort ascending'),
                    _('Sort descending'),
                    _('Sort by layer'))
        
        for tooltip, stock, cb in zip(tooltips, stocks, callbacks):
            action = gtk.Action(None, None, tooltip, stock)
            item = action.create_tool_item()
            item.connect('clicked', cb)
            
            toolbar.insert(item, -1)
        
        self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, object)
        self.tree = gtk.TreeView()
        self.tree.set_headers_visible(False)
        
        txt = gtk.CellRendererText()
        pix = gtk.CellRendererPixbuf()

        col = gtk.TreeViewColumn(_('Protocols'))
        col.pack_start(pix, False)
        col.pack_start(txt)

        col.set_attributes(pix, pixbuf=ProtocolTree.COL_PIX)
        col.set_attributes(txt, text=ProtocolTree.COL_STR)

        col.set_cell_data_func(pix, self.__pix_cell_data_func)
        col.set_cell_data_func(txt, self.__txt_cell_data_func)
        
        txt.set_property('xpad', 6)
        pix.set_property('xpad', 0)
        
        self.tree.append_column(col)
        self.tree.set_enable_tree_lines(True)
        self.tree.set_rules_hint(True)
        
        self.tree.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_COPY
        )
        
        self.tree.connect_after('drag-begin', self.__on_drag_begin)
        self.tree.connect('drag-data-get', self.__on_drag_data_get)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        
        sw.add(self.tree)
        
        self.pack_start(toolbar, False, False)
        self.pack_start(sw)

        self.proto_icon = get_pixbuf('protocol_small')
        self.layer_icon = get_pixbuf('layer_small')
        
        self.__on_sort_ascending(None)
    
    def populate(self, fill=True):
        self.store.clear()
        
        if fill:
            for i in Backend.get_protocols():
                self.store.append(None,
                    [self.proto_icon, Backend.get_proto_class_name(i), i])
        else:
            return Backend.get_protocols()
        
    def __on_sort_descending(self, item):
        self.populate()
        model = gtk.TreeModelSort(self.store)
        model.set_sort_column_id(ProtocolTree.COL_STR, gtk.SORT_DESCENDING)
        self.tree.set_model(model)
    
    def __on_sort_ascending(self, item):
        self.populate()
        model = gtk.TreeModelSort(self.store)
        model.set_sort_column_id(ProtocolTree.COL_STR, gtk.SORT_ASCENDING)
        self.tree.set_model(model)
    
    def __on_sort_layer(self, item):
        lst = self.populate(False)
        
        dct = defaultdict(list)
        
        for proto in lst:
            dct[Backend.get_proto_layer(proto)].append(proto)
        
        for i in xrange(1, 8, 1):
            if not i in dct:
                continue

            it = self.store.append(None, [self.layer_icon, _('Layer %d') % i, None])
            
            for proto in dct[i]:
                self.store.append(it, [self.proto_icon, Backend.get_proto_class_name(proto), proto])

        if None in dct:
            it = self.store.append(None, [self.layer_icon, _('Unknown layer'), None])

            for proto in dct[None]:
                self.store.append(it, [self.proto_icon, Backend.get_proto_class_name(proto), proto])

        
        self.tree.set_model(self.store)
    
    def __pix_cell_data_func(self, column, cell, model, iter):
        val = model.get_value(iter, ProtocolTree.COL_STR)
        obj = model.get_value(iter, ProtocolTree.COL_OBJ)
        
        if not obj:
            cell.set_property('cell-background-gdk',
                              self.style.base[gtk.STATE_INSENSITIVE])
        else:
            cell.set_property('cell-background-gdk', None)

    def __txt_cell_data_func(self, column, cell, model, iter):
        val = model.get_value(iter, ProtocolTree.COL_STR)
        obj = model.get_value(iter, ProtocolTree.COL_OBJ)
        
        if not obj:
            # This is a layer text so markup and color
            cell.set_property('markup', '<b>%s</b>' % val)
            cell.set_property('cell-background-gdk',
                              self.style.base[gtk.STATE_INSENSITIVE])
        else:
            cell.set_property('cell-background-gdk', None)
    
    def __on_drag_begin(self, widget, ctx):
        ctx.set_icon_default()

        # We could use that stuff in moo implementation
        widget = self.tree
        cmap = widget.get_colormap()
        width, height = widget.window.get_size()

        pix = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, width, height)
        pix = pix.get_from_drawable(widget.window, cmap, 0, 0, 0, 0,
                                    width, height)
        pix = pix.scale_simple(width * 4 / 5, height / 2, gtk.gdk.INTERP_HYPER)
        ctx.set_icon_pixbuf(pix, 0, 0)

        return False

    def __on_drag_data_get(self, btn, ctx, sel, info, time):
        model, iter = self.tree.get_selection().get_selected()
        sel.set_text(model.get_value(iter, ProtocolTree.COL_STR))

        return True

class ProtocolSelectorTab(UmitView):
    "The protocol selector tab"

    icon_name = gtk.STOCK_CONNECT
    label_text = _('Protocols')
    name = 'ProtocolTab'
    tab_position = gtk.POS_RIGHT

    def create_ui(self):
        self.tree = ProtocolTree()
        self._main_widget.add(self.tree)
        self._main_widget.show_all()
