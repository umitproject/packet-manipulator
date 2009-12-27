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
A perspective to show sniffed packets
"""

import copy

import gtk
import pango
import gobject

from umit.pm import backend
from umit.pm.core.i18n import _
from umit.pm.core.atoms import Node
from umit.pm.core.logger import log
from umit.pm.core.bus import ServiceBus
from umit.pm.manager.preferencemanager import Prefs

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.widgets.filterentry import FilterEntry
from umit.pm.gui.widgets.cellrenderer import GridRenderer
from umit.pm.higwidgets.higanimates import HIGAnimatedBar

from umit.pm.gui.pages.base import Perspective
from umit.pm.backend import SniffContext, MetaPacket

class SniffPage(Perspective):
    COL_NO     = 0
    COL_TIME   = 1
    COL_SRC    = 2
    COL_DST    = 3
    COL_PROTO  = 4
    COL_INFO   = 5
    COL_COLOR  = 6
    COL_OBJECT = 7

    icon = 'sniff_small'
    title = _('Sniff perspective')

    COLORS = (
              gtk.gdk.color_parse('#FFFA99'),
              gtk.gdk.color_parse('#8DFF7F'),
              gtk.gdk.color_parse('#FFE3E5'),
              gtk.gdk.color_parse('#C797FF'),
              gtk.gdk.color_parse('#A0A0A0'),
              gtk.gdk.color_parse('#D6E8FF'),
              gtk.gdk.color_parse('#C2C2FF'),
    )

    def create_ui(self):
        self.use_colors = True

        self.set_border_width(2)

        self.__create_toolbar()
        self.__create_view()

        self.statusbar = HIGAnimatedBar('', gtk.STOCK_INFO)
        self.pack_start(self.statusbar, False, False)

        self.show_all()

        Prefs()['gui.maintab.sniffview.font'].connect(self.__modify_font)
        Prefs()['gui.maintab.sniffview.usecolors'].connect(self.__modify_colors)

        self.tree.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.tree.get_selection().connect('changed',
                                          self.__on_selection_changed)

        self.filter.get_entry().connect('activate',self.__on_apply_filter)

        self.tree.connect('button-press-event', self.__on_popup)

        self.connect('realize', self.__on_realize)

        self.timeout_id = None
        self.reload()

    def __on_realize(self, window):
        self.tree.set_model(self.list_store)

    def __create_toolbar(self):
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        stocks = (
            gtk.STOCK_REFRESH,
            gtk.STOCK_MEDIA_STOP,
            gtk.STOCK_NETWORK
        )

        callbacks = (
            self.__on_restart,
            self.__on_stop,
            self.__on_reorder
        )

        tooltips = (
            _('Restart capturing'),
            _('Stop capturing'),
            _('Reorder flow')
        )

        for tooltip, stock, callback in zip(tooltips, stocks, callbacks):
            action = gtk.Action(None, None, tooltip, stock)
            action.connect('activate', callback)

            self.toolbar.insert(action.create_tool_item(), -1)

        self.filter = FilterEntry()

        item = gtk.ToolItem()
        item.add(self.filter)
        item.set_expand(True)

        self.toolbar.insert(item, -1)

        self.pack_start(self.toolbar, False, False)

    def __create_view(self):
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # We have to create two seperate objects if we want to have more
        # performance while sniffing. We'll use the tree_store only for
        # reflowing without a model filter.

        self.tree_store = gtk.TreeStore(object)
        self.list_store = gtk.ListStore(object)
        self.active_model = self.list_store

        self.tree = gtk.TreeView(self.active_model)

        self.active_filter = None
        self.model_filter = self.list_store.filter_new()
        self.model_filter.set_visible_func(self.__filter_func)

        idx = 0
        rend = GridRenderer()
        rend.set_property('ellipsize', pango.ELLIPSIZE_END)

        columns_str = Prefs()['gui.maintab.sniffview.columns'].value

        for column_str in columns_str.split(','):
            try:
                label, pixel_size, eval_str = column_str.split('|', 2)
                pixel_size = int(pixel_size)

                if eval_str[-1] != '%' or eval_str[0] != '%':
                    continue

                eval_str = eval_str[1:-1]

                col = gtk.TreeViewColumn(label, rend)
                col.set_min_width(pixel_size)
                col.set_fixed_width(pixel_size)
                col.set_resizable(True)

                if eval_str == 'number':
                    col.set_cell_data_func(rend, self.__cell_data_number)
                else:
                    func = getattr(MetaPacket, eval_str, None) or \
                           getattr(MetaPacket, 'get_' + eval_str, None)

                    if not func:
                        col.set_cell_data_func(rend, self.__cell_data_cfield,
                                               eval_str)
                    else:
                        col.set_cell_data_func(rend, self.__cell_data_func,
                                               func)

                self.tree.insert_column(col, idx)
                idx += 1
            except Exception:
                pass

        # Set the fixed height mode property to True to speeds up
        self.tree.set_fixed_height_mode(True)

        sw.add(self.tree)
        self.pack_start(sw)

    def __cell_data_number(self, col, cell, model, iter):
        packet = model.get_value(iter, 0)
        cell.set_property('text', "%s)" % ".".join(
            [str(i + 1) \
                for i in model.get_path(iter)]
        ))
        cell.set_property('cell-background-gdk', self.__get_color(packet))

    def __cell_data_cfield(self, col, cell, model, iter, cfield):
        packet = model.get_value(iter, 0)
        data = packet.cfields.get(cfield, '')

        if isinstance(data, basestring):
            cell.set_property('text', data)
        else:
            cell.set_property('text', None)

        cell.set_property('cell-background-gdk', self.__get_color(packet))

    def __cell_data_func(self, col, cell, model, iter, func):
        packet = model.get_value(iter, 0)
        data = func(packet)

        if isinstance(data, basestring):
            cell.set_property('text', data)
        else:
            cell.set_property('text', None)

        cell.set_property('cell-background-gdk', self.__get_color(packet))

    def __modify_font(self, font):
        try:
            desc = pango.FontDescription(font)

            for col in self.tree.get_columns():
                for rend in col.get_cell_renderers():
                    rend.set_property('font-desc', desc)

            self.__redraw_rows()
        except:
            # Block change

            return True

    def __modify_colors(self, value):
        self.use_colors = value
        self.tree.set_rules_hint(not self.use_colors)

        self.__redraw_rows()

    def __redraw_rows(self):
        #def emit_row_changed(model, path, iter):
        #    model.row_changed(path, iter)

        #self.active_model.foreach(emit_row_changed)

        # Queue draw should be enough here
        self.queue_draw()

    def __get_color(self, packet):
        if self.use_colors:
            proto = packet.get_protocol_str()
            return self.COLORS[hash(proto) % len(self.COLORS)]
        else:
            return None

    def __update_tree(self):
        if isinstance(self.session.context, SniffContext):
            self.session.context.check_finished()

        self.tree.freeze_child_notify()

        for packet in self.session.context.get_data():
            self.list_store.append([packet])

            #while gtk.events_pending():
            #    gtk.main_iteration_do()

        self.tree.thaw_child_notify()

        # TODO: better handle the situation.
        if getattr(self.session.context, 'auto_scroll', True) and \
           len(self.active_model) > 0:
            self.tree.scroll_to_cell(len(self.active_model) - 1)

        alive = self.session.context.is_alive()

        if not alive:
            self.statusbar.label = "<b>%s</b>" % self.session.context.summary
            self.statusbar.image = gtk.STOCK_INFO
            self.statusbar.show()

        return alive

    # Public functions

    def clear(self):
        self.tree_store.clear()
        self.list_store.clear()

        # Maybe we have to switch back to list store mode?

    def redraw(self, packet=None):
        model, lst = self.tree.get_selection().get_selected_rows()

        for idx in lst:
            iter = model.get_iter(lst[0])
            model.row_changed(idx, iter)

    def reload(self):
        for packet in self.session.context.get_data():
            self.list_store.append([packet])

            while gtk.events_pending():
                gtk.main_iteration_do()

        self.statusbar.label = "<b>%s</b>" % self.session.context.summary

        if self.timeout_id:
            gobject.source_remove(self.timeout_id)

        if isinstance(self.session.context, backend.TimedContext) and \
           self.session.context.state != self.session.context.NOT_RUNNING:
            self.timeout_id = gobject.timeout_add(300, self.__update_tree)

    # Signals callbacks

    def __on_selection_changed(self, selection):
        model, lst = selection.get_selected_rows()

        # Only if i have one row selected
        if len(lst) == 1:
            iter = model.get_iter(lst[0])
            self.session.set_active_packet(model.get_value(iter, 0))
        else:
            self.session.set_active_packet(None)

    def __on_popup(self, tree, evt):
        if evt.button != 3:
            return

        model, lst = self.tree.get_selection().get_selected_rows()

        if not lst:
            return

        menu = gtk.Menu()

        labels = (_('Create a sequence'), _('Save selected'))
        stocks = (gtk.STOCK_INDEX, gtk.STOCK_SAVE_AS)
        callbacks = (self.__on_create_seq, self.__on_save_selection)

        for lbl, stock, cb in zip(labels, stocks, callbacks):
            action =  gtk.Action(None, lbl, None, stock)
            action.connect('activate', cb)
            menu.append(action.create_menu_item())

        menu.show_all()
        menu.popup(None, None, None, evt.button, evt.time)

        return True

    def get_selected_packets(self, tree=False):
        """
        @return a list or a Tree contanining the selected packets
        """

        if tree:
            node = Node()

            def add_to_tree(model, path, iter, tree):
                obj = copy.deepcopy(model.get_value(iter, 0))
                parent = model.iter_parent(iter)

                if not parent:
                    tree.append_node(Node(obj))
                else:
                    path = tree.find(model.get_value(parent, 0))

                    if not path:
                        tree.append_node(Node(obj))
                    else:
                        node = tree.get_from_path(path)
                        node.append_node(Node(obj))

            self.tree.get_selection().selected_foreach(add_to_tree, node)

            for child in node:
                child.data = backend.SequencePacket(child.data)

            return node
        else:
            ret = []
            model, lst = self.tree.get_selection().get_selected_rows()

            for path in lst:
                ret.append(model.get_value(model.get_iter(path), 0))

            return ret

    def __on_create_seq(self, action):
        ServiceBus().call('pm.sessions', 'create_sequence_session',
                          self.get_selected_packets(True))

    def __on_save_selection(self, action):
        dialog = self.__create_save_dialog()

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            ctx = backend.StaticContext('', dialog.get_filename())
            ctx.data = self.get_selected_packets()

            if ctx.save():
                self.statusbar.image = gtk.STOCK_HARDDISK
                self.statusbar.label = \
                    _('<b>%d selected packets saved to %s</b>') % \
                     (len(ctx.data), ctx.cap_file)
            else:
                self.statusbar.image = gtk.STOCK_DIALOG_ERROR
                self.statusbar.label = "<b>%s</b>" % ctx.summary

            self.statusbar.start_animation(True)

        dialog.hide()
        dialog.destroy()

    def __on_reorder(self, action):
        if isinstance(self.session.context, backend.TimedContext):
            if self.session.context.state == self.session.context.NOT_RUNNING:
                packets = self.session.context.get_all_data()
            else:
                self.statusbar.label = \
                    _('<b>Cannot reorganize the flow while sniffing</b>')
                self.statusbar.start_animation(True)
                return

        elif isinstance(self.session.context, backend.StaticContext):
            packets = self.session.context.get_data()
        else:
            return

        tree = backend.analyze_connections(packets)

        if tree:
            self.tree_store.clear()

            for (root, lst) in tree:
                iter = self.tree_store.append(None, [root])

                for child in lst:
                    self.tree_store.append(iter, [child])

            self._switch_model(self.tree_store)

    def _switch_model(self, model):
        """
        Switch to the new model and reset the filter
        """

        if self.active_model is not model:
            self.active_model = model
            self.model_filter = model.filter_new()
            self.model_filter.set_visible_func(self.__filter_func)

        if self.active_filter:
            self.model_filter.refilter()
            self.tree.set_model(self.model_filter)
        elif self.tree.get_model() is not model:
            self.tree.set_model(model)

    def __on_apply_filter(self, entry):
        self.active_filter = self.filter.get_text() or None
        self._switch_model(self.active_model)

    def __filter_func(self, model, iter):
        if not self.active_filter:
            return True

        packet = model.get_value(iter, 0)

        if not packet:
            return False

        strs = (
            str(model.get_path(iter)[0] + 1),
            packet.get_time(),
            packet.get_source(),
            packet.get_dest(),
            packet.get_protocol_str(),
            packet.summary()
        )

        # TODO: implement a search engine like num: summary: ?

        for pattern in strs:
            if self.active_filter in pattern:
                return True

        return False

    def __on_stop(self, action):
        self.session.context.stop()
    def __on_restart(self, action):
        self.session.context.restart()
