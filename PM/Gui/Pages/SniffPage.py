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
A perspective to show sniffed packets
"""

import gtk
import pango
import gobject

from PM import Backend
from PM.Core.I18N import _
from PM.Manager.PreferenceManager import Prefs

from PM.Gui.Core.App import PMApp
from PM.Gui.Widgets.FilterEntry import FilterEntry
from PM.Gui.Widgets.CellRenderer import GridRenderer
from PM.higwidgets.higanimates import HIGAnimatedBar

class SniffPage(gtk.VBox):
    COL_NO     = 0
    COL_TIME   = 1
    COL_SRC    = 2
    COL_DST    = 3
    COL_PROTO  = 4
    COL_INFO   = 5
    COL_COLOR  = 6
    COL_OBJECT = 7

    def __init__(self, session):
        super(SniffPage, self).__init__(False, 4)

        self.session = session

        self.set_border_width(2)

        self.__create_toolbar()
        self.__create_view()

        self.statusbar = HIGAnimatedBar('', gtk.STOCK_INFO)
        self.pack_start(self.statusbar, False, False)

        self.show_all()

        self.use_colors = True

        # TODO: get from preference
        self.colors = (
            gtk.gdk.color_parse('#FFFA99'),
            gtk.gdk.color_parse('#8DFF7F'),
            gtk.gdk.color_parse('#FFE3E5'),
            gtk.gdk.color_parse('#C797FF'),
            gtk.gdk.color_parse('#A0A0A0'),
            gtk.gdk.color_parse('#D6E8FF'),
            gtk.gdk.color_parse('#C2C2FF'),
        )

        Prefs()['gui.maintab.sniffview.font'].connect(self.__modify_font)
        Prefs()['gui.maintab.sniffview.usecolors'].connect(self.__modify_colors)

        self.tree.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.tree.get_selection().connect('changed', self.__on_selection_changed)
        self.filter.get_entry().connect('activate', self.__on_apply_filter)

        self.tree.connect('button-press-event', self.__on_popup)

        self.timeout_id = None
        self.reload()

    def __create_toolbar(self):
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        stocks = (
            gtk.STOCK_REFRESH,
            gtk.STOCK_MEDIA_STOP,
            gtk.STOCK_SAVE,
            gtk.STOCK_SAVE_AS,
            gtk.STOCK_NETWORK
        )

        callbacks = (
            self.__on_restart,
            self.__on_stop,
            self.__on_save,
            self.__on_save_as,
            self.__on_reorder
        )

        tooltips = (
            _('Restart capturing'),
            _('Stop capturing'),
            _('Save packets'),
            _('Save packets as'),
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

        self.store = gtk.TreeStore(object)
        self.tree = gtk.TreeView(self.store)

        # Create a filter function
        self.model_filter = self.store.filter_new()
        self.model_filter.set_visible_func(self.__filter_func)

        self.tree.set_model(self.model_filter)

        idx = 0
        rend = GridRenderer()

        for txt in (_('No.'), _('Time'), _('Source'), \
                    _('Destination'), _('Protocol'), _('Info')):

            col = gtk.TreeViewColumn(txt, rend)
            col.set_cell_data_func(rend, self.__cell_data_func, idx)
            self.tree.append_column(col)

            idx += 1

        sw.add(self.tree)
        self.pack_start(sw)

    def __cell_data_func(self, col, cell, model, iter, idx):
        packet = model.get_value(iter, 0)

        if idx == self.COL_NO:
            cell.set_property('text', "%s)" % ".".join([str(i + 1) for i in model.get_path(iter)]))
        elif idx == self.COL_TIME:
            cell.set_property('text', packet.get_time())
        elif idx == self.COL_SRC:
            cell.set_property('text', packet.get_source())
        elif idx == self.COL_DST:
            cell.set_property('text', packet.get_dest())
        elif idx == self.COL_PROTO:
            cell.set_property('text', packet.get_protocol_str())
        elif idx == self.COL_INFO:
            cell.set_property('text', packet.summary())

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
        def emit_row_changed(model, path, iter):
            model.row_changed(path, iter)

        self.store.foreach(emit_row_changed)

    def __get_color(self, packet):
        if self.use_colors:
            proto = packet.get_protocol_str()
            return self.colors[hash(proto) % len(self.colors)]
        else:
            return None

    def __update_tree(self):
        for packet in self.session.context.get_data():
            self.store.append(None, [packet])

            # Scroll to end
            if getattr(self.session.context, 'auto_scroll', True):
                self.tree.scroll_to_cell(len(self.model_filter) - 1)

        alive = self.session.context.is_alive()

        if not alive:
            self.statusbar.label = "<b>%s</b>" % self.session.context.summary
            self.statusbar.image = gtk.STOCK_INFO
            self.statusbar.show()

        return alive

    # Public functions

    def populate(self, pktlist):
        for packet in pktlist:
            self.store.append(None, [packet])

    def clear(self):
        self.store.clear()

    def reload(self):
        for packet in self.session.context.get_data():
            self.store.append(None, [packet])

        self.statusbar.label = "<b>%s</b>" % self.session.context.summary

        if self.timeout_id:
            gobject.source_remove(self.timeout_id)

        if isinstance(self.session.context, Backend.TimedContext) and \
           self.session.context.state != self.session.context.NOT_RUNNING:
            self.timeout_id = gobject.timeout_add(200, self.__update_tree)

    def save(self):
        return self.__on_save(None)

    def save_as(self):
        return self.__on_save_as(None)

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
    
    def __get_packets_selected(self):
        model, lst = self.tree.get_selection().get_selected_rows()

        ret = []
        for path in lst:
            ret.append(model.get_value(model.get_iter(path), 0))

        return ret

    def __on_create_seq(self, action):
        tab = PMApp().main_window.get_tab("MainTab")
        tab.session_notebook.create_sequence_session(self.__get_packets_selected())

    def __on_save_selection(self, action):
        dialog = self.__create_save_dialog()

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            ctx = Backend.StaticContext('', dialog.get_filename())
            ctx.data = self.__get_packets_selected()

            if ctx.save():
                self.statusbar.image = gtk.STOCK_HARDDISK
                self.statusbar.label = _('<b>%d selected packets saved to %s</b>') % (len(ctx.data), ctx.cap_file)
            else:
                self.statusbar.image = gtk.STOCK_DIALOG_ERROR
                self.statusbar.label = "<b>%s</b>" % ctx.summary

            self.statusbar.start_animation(True)

        dialog.hide()
        dialog.destroy()

    def __on_reorder(self, action):
        if isinstance(self.session.context, Backend.TimedContext):
            if self.session.context.state == self.session.context.NOT_RUNNING:
                packets = self.session.context.get_all_data()
            else:
                self.statusbar.label = _('<b>Cannot reorganize the flow while sniffing</b>')
                self.statusbar.start_animation(True)
                return

        elif isinstance(self.session.context, Backend.StaticContext):
            packets = self.session.context.get_data()
        else:
            return

        tree = Backend.analyze_connections(packets)

        if tree:
            self.store.clear()

            for (root, lst) in tree:
                iter = self.store.append(None, [root])

                for child in lst:
                    self.store.append(iter, [child])

    def __on_apply_filter(self, entry):
        self.model_filter.refilter()

    def __filter_func(self, model, iter):
        txt = self.filter.get_text()

        if not txt:
            return True

        packet = model.get_value(iter, 0)

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
            if txt in pattern:
                return True

        return False

    def __on_stop(self, action):
        self.session.context.stop()
    def __on_restart(self, action):
        self.session.context.restart()

    def __on_save(self, action):
        if self.session.context.cap_file:
            return self.__save_packets(self.session.context.cap_file)
        else:
            return self.__on_save_as(None)

    def __on_save_as(self, action):
        ret = False
        dialog = self.__create_save_dialog()

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            ret = self.__save_packets(dialog.get_filename())

        dialog.hide()
        dialog.destroy()

        return ret

    def __create_save_dialog(self):
        dialog = gtk.FileChooserDialog(_('Save Pcap file to'),
                self.get_toplevel(), gtk.FILE_CHOOSER_ACTION_SAVE,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                         gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))

        for name, pattern in ((_('Pcap files'), '*.pcap'),
                              (_('Pcap gz files'), '*.pcap.gz'),
                              (_('All files'), '*')):

            filter = gtk.FileFilter()
            filter.set_name(name)
            filter.add_pattern(pattern)
            dialog.add_filter(filter)

        return dialog

    def __save_packets(self, fname):
        self.session.context.cap_file = fname
        ret = self.session.context.save()

        if ret:
            self.statusbar.image = gtk.STOCK_HARDDISK
        else:
            self.statusbar.image = gtk.STOCK_DIALOG_ERROR

        self.statusbar.label = "<b>%s</b>" % self.session.context.summary
        self.statusbar.start_animation(True)

        return ret

