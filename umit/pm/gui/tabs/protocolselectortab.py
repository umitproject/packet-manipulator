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

import gtk

from umit.pm import backend
from umit.pm.core.i18n import _
from umit.pm.core.atoms import defaultdict
from umit.pm.core.bus import ServiceBus

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.core.views import UmitView
from umit.pm.gui.core.icons import get_pixbuf

from umit.pm.gui.sessions.sequencesession import SequenceSession

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

        self.tree.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_COPY
        )

        self.tree.connect_after('drag-begin', self.__on_drag_begin)
        self.tree.connect('drag-data-get', self.__on_drag_data_get)
        self.tree.connect('button-press-event', self.__on_button_press)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        sw.add(self.tree)

        self.pack_start(toolbar, False, False)
        self.pack_start(sw)

        self.proto_icon = get_pixbuf('protocol_small')
        self.layer_icon = get_pixbuf('layer_small')

        # Now create the context menu
        self.context_menu = gtk.Menu()

        self.accel_group = gtk.AccelGroup()
        self.action_group = gtk.ActionGroup('ProtocolSelectorAction')

        labels = (_('Add to a new sequence'), None,
                  _('Append to the sequence'),
                  _('Append to the sequence selection'), None,
                  _('Append to the hierarchy'),
                  _('Append to the hierarchy selection'))

        accels = ('<Shift>N', None,
                  '<Shift>S',
                  '<Shift><Alt>S', None,
                  '<Ctrl>H',
                  '<Ctrl><Alt>H')

        stocks = (gtk.STOCK_NEW, None,
                  gtk.STOCK_GOTO_BOTTOM,
                  gtk.STOCK_GO_DOWN, None,
                  gtk.STOCK_GOTO_BOTTOM,
                  gtk.STOCK_GO_DOWN)

        cbs = (self.__add_to_new_sequence, None,
               self.__append_cur_sequence,
               self.__append_cur_sequence_sel, None,
               self.__append_cur_hier,
               self.__append_cur_hier_sel)

        for lbl, stock, accel, cb in zip(labels, stocks, accels, cbs):
            if not lbl:
                self.context_menu.append(gtk.SeparatorMenuItem())
                continue

            action = gtk.Action(lbl, lbl, None, stock)
            action.connect('activate', cb)
            self.action_group.add_action_with_accel(action, accel)
            action.set_accel_group(self.accel_group)
            self.context_menu.append(action.create_menu_item())

        self.context_menu.show_all()
        self.__on_sort_ascending(None)

    def populate(self, fill=True):
        self.store.clear()

        if fill:
            for i in backend.get_protocols():
                self.store.append(None,
                    [self.proto_icon, backend.get_proto_class_name(i), i])
        else:
            return backend.get_protocols()

    def __on_button_press(self, widget, evt):
        if evt.button != 3:
            return False

        self.context_menu.popup(None, None, None, evt.button, evt.time)
        return True

    def __on_sort_descending(self, item):
        self.populate()
        model = gtk.TreeModelSort(self.store)
        model.set_sort_column_id(ProtocolTree.COL_STR, gtk.SORT_DESCENDING)
        self.tree.set_rules_hint(True)
        self.tree.set_model(model)

    def __on_sort_ascending(self, item):
        self.populate()
        model = gtk.TreeModelSort(self.store)
        model.set_sort_column_id(ProtocolTree.COL_STR, gtk.SORT_ASCENDING)
        self.tree.set_rules_hint(True)
        self.tree.set_model(model)

    def __on_sort_layer(self, item):
        lst = self.populate(False)

        dct = defaultdict(list)

        for proto in lst:
            dct[backend.get_proto_layer(proto)].append(proto)

        for i in xrange(1, 8, 1):
            if not i in dct:
                continue

            it = self.store.append(None, [self.layer_icon, _('Layer %d') % i,
                                          None])

            for proto in dct[i]:
                self.store.append(it, [self.proto_icon,
                                       backend.get_proto_class_name(proto),
                                       proto])

        if None in dct:
            it = self.store.append(None, [self.layer_icon, _('Unknown layer'),
                                          None])

            for proto in dct[None]:
                self.store.append(it, [self.proto_icon,
                                       backend.get_proto_class_name(proto),
                                       proto])

        self.tree.set_rules_hint(False)
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
        #ctx.set_icon_default()

        # We could use that stuff in moo implementation
        #widget = self.tree
        #cmap = widget.get_colormap()
        #width, height = widget.window.get_size()

        #pix = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, width, height)
        #pix = pix.get_from_drawable(widget.window, cmap, 0, 0, 0, 0,
        #                            width, height)
        #pix = pix.scale_simple(width * 4 / 5, height / 2, gtk.gdk.INTERP_HYPER)
        #ctx.set_icon_pixbuf(pix, 0, 0)

        return False

    def __on_drag_data_get(self, btn, ctx, sel, info, time):
        sel.set_text(self.__get_selected())
        return True

    def __get_selected(self):
        model, iter = self.tree.get_selection().get_selected()
        if iter:
            return model.get_value(iter, ProtocolTree.COL_STR)
        return None

    # Callbacks for context menu
    def __add_to_new_sequence(self, action):
        sel = self.__get_selected()

        if sel:
            ServiceBus().call('pm.sessions', 'create_edit_session', sel)
            return True

    def __do_append_cur_sequence(self, selection=None, hier=False):
        sel = self.__get_selected()

        if sel:
            sess = ServiceBus().call('pm.sessions', 'get_current_session')

            if not isinstance(sess, SequenceSession):
                return False

            if not hier:
                sess.sequence_page.append_packet(sel, selection)
            else:
                sess.packet_page.proto_hierarchy.append_packet(sel, selection)

            return True

        return False

    def __append_cur_sequence(self, action):
        return self.__do_append_cur_sequence()
    def __append_cur_sequence_sel(self, action):
        return self.__do_append_cur_sequence(True)

    def __append_cur_hier(self, action):
        return self.__do_append_cur_sequence(hier=True)
    def __append_cur_hier_sel(self, action):
        return self.__do_append_cur_sequence(True, True)

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

    def connect_tab_signals(self):
        PMApp().main_window.add_accel_group(self.tree.accel_group)
