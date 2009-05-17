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
from PM.Core.Logger import log
from PM.Manager.PreferenceManager import Prefs

from PM.Gui.Core.App import PMApp
from PM.Gui.Core.Icons import get_pixbuf
from PM.Gui.Widgets.Plotter import Plotter
from PM.Gui.Tabs.OperationsTab import SendOperation, SendReceiveOperation

from PM.Gui.Pages.Base import Perspective

try:
    from PM.Gui.Widgets.PyGtkHexView import HexView

    log.info('Cool we\'re using read/write hex-view.')

except ImportError:
    from PM.Gui.Widgets.HexView import HexView

    log.warning('Erm :( We are using read only hex-view. Try to install '
                'pygtkhexview and restart PM. You could get a copy from: '
                'http://code.google.com/p/pygtkhex/')

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
            root = self.store.append(root, [self.proto_icon,
                                            Backend.get_proto_name(proto),
                                            proto])

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
        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.add(self.tree)

    def __connect_signals(self):
        self.tree.enable_model_drag_dest([('text/plain', 0, 0)],
                                         gtk.gdk.ACTION_COPY)

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
                return

            # We append as default
            where = -1

            if ret:
                path, pos = ret

                # because it's a treeview with only one child for row
                where = len(path)

                if pos == gtk.TREE_VIEW_DROP_BEFORE or \
                   pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
                    where -= 1

            # Now try to insert this stuff into the packet

            if self.session.packet.insert(packet, where):
                ctx.finish(True, False, time)

                self.session.reload_container(self.session.packet)
                self.session.reload_editor()

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

        assert Backend.is_proto(obj), "Should be a Protocol instance."

        return self.session.packet, obj


class PacketPage(Perspective):
    icon = 'packet_small'
    title = _('Packet perspective')

    def create_ui(self):
        self.hbox = gtk.HBox(False, 2)

        # Create the toolbar for sending selected packet
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        self.toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)

        stocks = (
            gtk.STOCK_EDIT,
            gtk.STOCK_DELETE,
            gtk.STOCK_CLEAR,
            gtk.STOCK_SELECT_COLOR
        )

        tooltips = (
            _('Complete layers'),
            _('Remove selected layer'),
            _('Reset layer to default'),
            _('Graph packet')
        )

        callbacks = (
            self.__on_complete,
            self.__on_remove,
            self.__on_reset,
            self.__on_graph
        )

        for tooltip, stock, callback in zip(tooltips, stocks, callbacks):
            action = gtk.Action(None, None, tooltip, stock)
            action.connect('activate', callback)
            self.toolbar.insert(action.create_tool_item(), -1)


        self.proto_hierarchy = ProtocolHierarchy(self.session)
        self.hexview = HexView()

        self.hbox.pack_start(self.proto_hierarchy, False, False, 0)
        self.hbox.pack_start(self.toolbar, False, False)
        self.hbox.pack_start(self.hexview)#, False, False)

        Prefs()['gui.maintab.hexview.font'].connect(self.hexview.modify_font)
        Prefs()['gui.maintab.hexview.bpl'].connect(self.hexview.set_bpl)

        self.pack_start(self.hbox)

    def redraw_hexview(self):
        """
        Redraws the hexview
        """
        if self.session.packet:
            self.hexview.payload = Backend.get_packet_raw(self.session.packet)
        else:
            self.hexview.payload = ''

    def reload(self):
        # Hide the toolbar while merging fields

        # FIXME: cyclic
        #if isinstance(self.session, SequenceSession) and \
        if getattr(self.session, 'sequence_page', None) and \
           self.session.sequence_page.merging:
            self.toolbar.hide()
            self.proto_hierarchy.hide()
        else:
            self.toolbar.show()
            self.proto_hierarchy.show()

        self.redraw_hexview()
        self.proto_hierarchy.reload()

    def __on_remove(self, action):
        packet, protocol = self.proto_hierarchy.get_active_protocol()

        if not packet:
            return

        if packet.remove(protocol):
            self.session.reload_container(packet)
            self.reload()

    def __on_reset(self, action):
        packet, protocol = self.proto_hierarchy.get_active_protocol()

        if not packet:
            return

        if packet.reset(protocol):
            self.session.reload_container(packet)
            self.reload()

    def __on_complete(self, action):
        packet, protocol = self.proto_hierarchy.get_active_protocol()

        if not packet:
            return

        if packet.complete():
            self.session.reload_container(packet)
            self.reload()

    def __on_graph(self, action):
        if not self.session.packet:
            return

        dialog = gtk.Dialog(
                _('Graph for %s') % self.session.packet.get_protocol_str(),
                self.get_toplevel(), 0, (gtk.STOCK_CLOSE, gtk.RESPONSE_REJECT,
                                         gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))

        dialog.plotter = Plotter(self.session.packet)
        dialog.vbox.pack_start(dialog.plotter)
        dialog.show_all()

        dialog.connect('response', self.__on_graph_response)

    def __on_graph_response(self, dialog, id):
        if id == gtk.RESPONSE_REJECT:
            dialog.hide()
            dialog.destroy()
        elif id == gtk.RESPONSE_ACCEPT:
            chooser = gtk.FileChooserDialog(_('Save graph to'), dialog,
                         gtk.FILE_CHOOSER_ACTION_SAVE,
                         (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                          gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))

            if chooser.run() == gtk.RESPONSE_ACCEPT:
                fname = chooser.get_filename()
                dialog.plotter.export_to(fname)

            chooser.hide()
            chooser.destroy()
