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
A perspective to show and edit packets
"""

import gtk

from PM import Backend
from PM.Core.I18N import _
from PM.Manager.PreferenceManager import Prefs

from PM.Gui.Core.App import PMApp
from PM.Gui.Core.Icons import get_pixbuf
from PM.Gui.Widgets.HexView import HexView
from PM.Gui.Tabs.OperationsTab import SendOperation, SendReceiveOperation

class ProtocolHierarchy(gtk.ScrolledWindow):
    def __init__(self, parent):
        gtk.ScrolledWindow.__init__(self)

        self.__create_widgets()
        self.__pack_widgets()
        self.__connect_signals()

        self.session = parent
        self.proto_icon = get_pixbuf('protocol_small')

        self.reload()

    def reload(self):
        self.store.clear()

        if not self.session.packet:
            return

        root = None

        # We pray to be ordered :(
        for proto in Backend.get_packet_protos(self.session.packet):
            root = self.store.append(root, [self.proto_icon, Backend.get_proto_name(proto), proto])

        self.tree.expand_all()
        self.tree.get_selection().select_path((0, ))

    def __create_widgets(self):
        # Icon / string (like TCP packet with some info?) / hidden
        self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, object)
        self.tree = gtk.TreeView(self.store)

        pix = gtk.CellRendererPixbuf()
        txt = gtk.CellRendererText()

        col = gtk.TreeViewColumn(_('Protocol'))

        col.pack_start(pix, False)
        col.pack_start(txt, True)

        col.set_attributes(pix, pixbuf=0)
        col.set_attributes(txt, text=1)

        self.tree.append_column(col)

        self.tree.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        self.tree.set_rules_hint(True)

    def __pack_widgets(self):
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.add(self.tree)

    def __connect_signals(self):
        self.tree.enable_model_drag_dest([('text/plain', 0, 0)], gtk.gdk.ACTION_COPY)
        self.tree.connect('drag-data-received', self.__on_drag_data)

    def __on_drag_data(self, widget, ctx, x, y, data, info, time):
        if not self.session.packet:
            ctx.finish(False, False, time)

        if data and data.format == 8:
            ret = self.tree.get_dest_row_at_pos(x, y)

            try:
                # Try to construct an empty packet
                packet = Backend.get_proto(data.data)()
                packet = Backend.MetaPacket(packet)
            except Exception:
                ctx.finish(False, False, time)

            # We append as default
            where = -1

            if ret:
                path, pos = ret
                where = len(path) # because it's a treeview with only one child for row

                if pos == gtk.TREE_VIEW_DROP_BEFORE or \
                   pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
                    where -= 1
            
            # Now try to insert this stuff into the packet

            if self.session.packet.insert(packet, where):
                ctx.finish(True, False, time)
                self.session.reload()
            else:
                ctx.finish(False, False, time)

        else:
            ctx.finish(False, False, time)

    def get_active_protocol(self):
        """
        Return the selected protocol or the most
        important protocol if no selection.

        @return a tuple Packet, Protocol or None, None
        """

        model, iter = self.tree.get_selection().get_selected()

        if not iter:
            return None, None

        obj = model.get_value(iter, 2)
        
        assert (Backend.is_proto(obj), "Should be a Protocol instance.")

        return self.session.packet, obj


class PacketPage(gtk.VBox):
    def __init__(self, parent):
        super(PacketPage, self).__init__(False, 4)

        self.session = parent

        # Create the toolbar for sending selected packet
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        stocks = (
            gtk.STOCK_EDIT,
            gtk.STOCK_DELETE,
            gtk.STOCK_GO_UP,
            gtk.STOCK_GO_DOWN
        )

        tooltips = (
            _('Complete layers'),
            _('Remove selected layer'),
            _('Send packet'),
            _('Send/receive packet')
        )

        callbacks = (
            self.__on_complete,
            self.__on_remove,
            self.__on_send,
            self.__on_send_receive
        )

        for tooltip, stock, callback in zip(tooltips, stocks, callbacks):
            action = gtk.Action(None, None, tooltip, stock)
            action.connect('activate', callback)
            self.toolbar.insert(action.create_tool_item(), -1)

        self.toolbar.insert(gtk.SeparatorToolItem(), -1)

        from sys import maxint

        self.packet_count = gtk.SpinButton(gtk.Adjustment(1, 0, maxint, 1, 10))
        self.packet_interval = gtk.SpinButton(gtk.Adjustment(0, 0, maxint, 1, 10))

        for lbl, widget in zip((_('No:'), _('Interval:')),
                               (self.packet_count, self.packet_interval)):

            hbox = gtk.HBox(False, 4)
            hbox.set_border_width(2)

            label = gtk.Label(lbl)
            label.set_use_markup(True)
            label.set_alignment(0, 0.5)

            hbox.pack_start(label)
            hbox.pack_start(widget)

            item = gtk.ToolItem()
            item.add(hbox)

            self.toolbar.insert(item, -1)

        self.pack_start(self.toolbar, False, False)

        self.proto_hierarchy = ProtocolHierarchy(self.session)
        self.hexview = HexView()

        vpaned = gtk.VPaned()
        vpaned.pack1(self.proto_hierarchy, True, False)
        vpaned.pack2(self.hexview, True, False)
        
        self.pack_start(vpaned)

        Prefs()['gui.maintab.hexview.font'].connect(self.hexview.modify_font)
        Prefs()['gui.maintab.hexview.bpl'].connect(self.hexview.set_bpl)

    def redraw_hexview(self):
        """
        Redraws the hexview
        """
        if self.session.packet:
            self.hexview.payload = Backend.get_packet_raw(self.session.packet)
        else:
            self.hexview.payload = ""

    def reload(self):
        self.redraw_hexview()
        self.proto_hierarchy.reload()

    def __on_remove(self, action):
        packet, protocol = self.proto_hierarchy.get_active_protocol()

        if not packet:
            return

        packet.remove(protocol)
        self.reload()

    def __on_complete(self, action):
        packet, protocol = self.proto_hierarchy.get_active_protocol()

        if not packet:
            return

        packet.complete()
        self.reload()

    def __on_send(self, action):
        packet, protocol = self.proto_hierarchy.get_active_protocol()

        if not packet:
            return

        # We start a background process in Operations tab

        count = self.packet_count.get_value_as_int()
        inter = self.packet_interval.get_value_as_int()

        tab = PMApp().main_window.get_tab("OperationsTab")
        tab.tree.append_operation(SendOperation(packet, count, inter))

    def __on_send_receive(self, action):
        packet, protocol = self.proto_hierarchy.get_active_protocol()

        if not packet:
            return

        # We start a background process in Operations tab

        count = self.packet_count.get_value_as_int()
        inter = self.packet_interval.get_value_as_int()

        tab = PMApp().main_window.get_tab("OperationsTab")
        tab.tree.append_operation(SendReceiveOperation(packet, count, inter))
