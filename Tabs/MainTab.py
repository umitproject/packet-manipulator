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
import Backend

from widgets.HexView import HexView
from widgets.Expander import AnimatedExpander
from widgets.Sniff import SniffPage

from views import UmitView
from Icons import get_pixbuf

from umitCore.I18N import _
from Manager.PreferenceManager import Prefs

from Tabs.OperationsTab import SendOperation, SendReceiveOperation

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

        col = gtk.TreeViewColumn('Name')

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
        if data and data.format == 8:
            ret = self.view.get_dest_row_at_pos(x, y)

            if not ret:
                self.store.append(None, [None, data.data, data.data, None])
            else:
                path, pos = ret
                print path, pos

            ctx.finish(True, False, time)
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
            gtk.STOCK_GO_UP,
            gtk.STOCK_GO_DOWN
        )

        tooltips = (
            'Send packet',
            'Send/receive packet'
        )

        callbacks = (
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

    def __on_send(self, action):
        packet, protocol = self.proto_hierarchy.get_active_protocol()

        if not packet:
            return

        # We start a background process in Operations tab

        count = self.packet_count.get_value_as_int()
        inter = self.packet_interval.get_value_as_int()

        from App import PMApp
        tab = PMApp().main_window.get_tab("Operations")
        tab.tree.append_operation(SendOperation(packet, count, inter))

    def __on_send_receive(self, action):
        packet, protocol = self.proto_hierarchy.get_active_protocol()

        if not packet:
            return

        # We start a background process in Operations tab

        count = self.packet_count.get_value_as_int()
        inter = self.packet_interval.get_value_as_int()

        from App import PMApp
        tab = PMApp().main_window.get_tab("Operations")
        tab.tree.append_operation(SendReceiveOperation(packet, count, inter))

class SessionPage(gtk.VBox):
    def __init__(self, ctx=None, show_sniff=True, show_packet=True):
        gtk.VBox.__init__(self)

        self.packet = None
        self.context = ctx

        self.sniff_page = SniffPage(self)
        self._label = gtk.Label(ctx.summary)

        self.set_border_width(4)

        self.vpaned = gtk.VPaned()
        self.sniff_expander = AnimatedExpander(_("Sniff perspective"), 'sniff_small')
        self.packet_expander = AnimatedExpander(_("Packet perspective"), 'packet_small')

        self.packet_page = PacketPage(self)

        self.vpaned.pack1(self.sniff_expander, True, False)
        self.vpaned.pack2(self.packet_expander, True, False)

        self.sniff_expander.add_widget(self.sniff_page, show_sniff)
        self.packet_expander.add_widget(self.packet_page, show_packet)

        self.packet_page.reload()

        self.pack_start(self.vpaned)
        self.show_all()

    def set_active_packet(self, packet):
        self.packet = packet
        self.packet_page.reload()

    def get_label(self):
        return self._label

    label = property(get_label)

class SessionNotebook(gtk.Notebook):
    def __init__(self):
        gtk.Notebook.__init__(self)

        self.set_show_border(False)
        self.set_scrollable(True)

        # We have a static page to manage the packets
        # selected from sniff perspective
        self.view_page = None

    def create_edit_session(self, packet):
        ctx = Backend.StaticContext()

        if isinstance(packet, basestring):
            packet = Backend.get_proto(packet)()
            packet = Backend.MetaPacket(packet)

        ctx.data.append(packet)
        ctx.summary = _('Editing %s') % packet.get_protocol_str()

        session = SessionPage(ctx)#, show_sniff=False)
        return self.__append_session(session)

    def create_sniff_session(self, ctx):
        session = SessionPage(ctx, show_packet=False)
        return self.__append_session(session)

    def create_context_session(self, ctx, sniff=True, packet=True):
        session = SessionPage(ctx, show_sniff=sniff, show_packet=packet)
        return self.__append_session(session)

    def create_offline_session(self, fname):
        ctx = Backend.StaticContext(fname)
        ctx.load()

        session = SessionPage(ctx, show_packet=False)
        return self.__append_session(session)

    def create_empty_session(self, title):
        session = SessionPage(title=title)
        return self.__append_session(session)

    def __append_session(self, session):
        self.append_page(session, session.label)
        self.set_tab_reorderable(session, True)
        return session

    def get_current_session(self):
        """
        Get the current SessionPage

        @return a SessionPage instance or None
        """

        idx = self.get_current_page()
        obj = self.get_nth_page(idx)

        if obj and isinstance(obj, SessionPage):
            return obj

        return None

class MainTab(UmitView):
    tab_position = None
    label_text = "MainTab"

    def __create_widgets(self):
        "Create the widgets"
        self.vbox = gtk.VBox(False, 2)
        self.session_notebook = SessionNotebook()

    def __pack_widgets(self):
        "Pack the widgets"

        self.vbox.pack_start(self.session_notebook)

        self.session_notebook.drag_dest_set(
            gtk.DEST_DEFAULT_ALL,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_COPY
        )

        self._main_widget.add(self.vbox)
        self._main_widget.show_all()

    def __connect_signals(self):
        self.session_notebook.connect('drag-data-received', self.__on_drag_data)

    def create_ui(self):
        "Create the ui"
        self.__create_widgets()
        self.__pack_widgets()
        self.__connect_signals()

    def get_current_session(self):
        "@returns the current SessionPage or None"
        page = self.get_current_page()

        if page and isinstance(page, SessionPage):
            return page
        return None

    def get_current_page(self):
        "@return the current page in notebook or None"

        idx = self.session_notebook.get_current_page()
        return self.session_notebook.get_nth_page(idx)

    #===========================================================================

    def __on_drag_data(self, widget, ctx, x, y, data, info, time):
        "drag-data-received callback"

        if data and data.format == 8:
            proto = data.data

            if Backend.get_proto(proto):
                self.session_notebook.create_edit_session(data.data)
                ctx.finish(True, False, time)
                return True

        ctx.finish(False, False, time)
