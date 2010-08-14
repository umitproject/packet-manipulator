#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
#
# Author: Quek Shu Yang <quekshuy@gmail.com>
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
from umit.pm.core.logger import log
from umit.pm.manager.preferencemanager import Prefs

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.core.icons import get_pixbuf
from umit.pm.gui.widgets.plotter import Plotter
from umit.pm.gui.tabs.operationstab import SendOperation, SendReceiveOperation

from umit.pm.gui.pages.base import Perspective

from umit.pm.backend.bt_sniffer import LMP, L2CAP, LMPHeader, L2CAPHeader
from umit.pm.backend.bt_sniffer import is_lmp, is_l2cap, is_lmp_header, is_l2cap_header, get_type_name


try:
    from umit.pm.gui.widgets.pygtkhexview import HexView

    log.info('Cool we\'re using read/write hex-view.')

except ImportError:
    from umit.pm.gui.widgets.hexview import HexView

    log.warning('Erm :( We are using read only hex-view. Try to install '
                'pygtkhexview and restart PM. You could get a copy from: '
                'http://code.google.com/p/pygtkhex/')


class BtLayerHierarchy(gtk.ScrolledWindow):
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
            log.debug("BtPacketPage.reload(): self.session.packet is None")
            return

#        log.debug('Reloading BtLayerHierarchy with %s' % \
#                  self.session.packet.summary())
        
        self.add_unit(self.session.packet)

        self.tree.expand_all()
        self.tree.get_selection().select_path((0, ))

    def __create_widgets(self):
        # Icon / string (like TCP packet with some info?) / hidden
        self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, object)
        self.tree = gtk.TreeView(self.store)

        pix = gtk.CellRendererPixbuf()
        txt = gtk.CellRendererText()

        col = gtk.TreeViewColumn(_('Layers'))

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
        pass
#        self.tree.enable_model_drag_dest([('text/plain', 0, 0)],
#                                         gtk.gdk.ACTION_COPY)
#
#        self.tree.connect('drag-data-received', self.__on_drag_data)

    def add_unit(self, metapkt, parent_row_iter = None):
        """
            @param unit: Starts with a BtMetaPacket
        """
        if parent_row_iter is None:
        
            row_str = get_type_name(metapkt.sniffunit.payload)
            iter = self.store.append(None, (self.proto_icon, row_str, metapkt.sniffunit.payload))
            
            if hasattr(metapkt.sniffunit.payload, 'header'): 
                self.add_unit(metapkt.sniffunit.payload.header, iter)
            if hasattr(metapkt.sniffunit.payload, 'payload'):
                self.add_unit(metapkt.sniffunit.payload.payload, iter)
        
        elif is_lmp_header(metapkt):
            
            self.store.append(parent_row_iter, (None, 'Tid: %d' % metapkt.tid, metapkt))
            self.store.append(parent_row_iter, (None, 'Op1: %s' % hex(metapkt.op1), metapkt))
            if metapkt.op1 >= 124 and metapkt.op1 <= 127:
                self.store.append(parent_row_iter, (None, 'Op2: %s' % hex(metapkt.op2), metapkt))
            
        elif is_l2cap_header(metapkt):
            
            self.store.append(parent_row_iter, (None, 'Length: %d' % metapkt.length, metapkt))
            self.store.append(parent_row_iter, (None, 'Channel ID: %s' % hex(metapkt.chan_id), metapkt))

        else:
            
            self.store.append(parent_row_iter, (None, 'Raw: %s' % metapkt.rawdata, metapkt))
            
    def get_active_layer(self):
        """
        Return the selected layer

        @return a tuple Packet, Protocol or None, None
        """

        model, iter = self.tree.get_selection().get_selected()

        if not iter:
            return None, None

        obj = model.get_value(iter, 2)

        return self.session.packet, obj


class BtPacketPage(Perspective):
    icon = 'packet_small'
    title = _('Packet perspective')

    def create_ui(self):
        
        self.hbox = gtk.HBox(False, 2)

        # Create the toolbar for sending selected packet
#        self.toolbar = gtk.Toolbar()
#        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
#        self.toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
#
#        stocks = (
#            gtk.STOCK_EDIT,
#            gtk.STOCK_DELETE,
#            gtk.STOCK_CLEAR,
#            gtk.STOCK_SELECT_COLOR
#        )
#
#        tooltips = (
#            _('Complete layers'),
#            _('Remove selected layer'),
#            _('Reset layer to default'),
#            _('Graph packet')
#        )
#
#        callbacks = (
#            self.__on_complete,
#            self.__on_remove,
#            self.__on_reset,
#            self.__on_graph
#        )
#
#        for tooltip, stock, callback in zip(tooltips, stocks, callbacks):
#            action = gtk.Action(None, None, tooltip, stock)
#            action.connect('activate', callback)
#            self.toolbar.insert(action.create_tool_item(), -1)
#
#
#        self.proto_hierarchy = ProtocolHierarchy(self.session)
        self.layer_hchy = BtLayerHierarchy(self.session)
        self.hexview = HexView()

        try:
            # Only the read write hexview provide this
            self.hexview.set_insert_mode(True)
            self.hexview.set_read_only_mode(False)
            self.hexview.changed_callback = self.__on_hexview_changed
            self.hexview.connect('focus-out-event', self.__on_hexview_focus_out)

            self._packet_changed = False
        except:
            pass

        self.hbox.pack_start(self.layer_hchy, False, False, 0)
#        self.hbox.pack_start(self.toolbar, False, False)
        self.hbox.pack_start(self.hexview)#, False, False)

        Prefs()['gui.maintab.hexview.font'].connect(self.hexview.modify_font)
        Prefs()['gui.maintab.hexview.bpl'].connect(self.hexview.set_bpl)

        self.pack_start(self.hbox)

    def redraw_hexview(self):
        """
        Redraws the hexview
        """
        if self.session.packet:
            # Takes string while we return a list of integers
            paylst = self.session.packet.get_raw()
            self.hexview.payload = ''.join([chr(x) for x in paylst])
        else:
            self.hexview.payload = ''

    def __on_hexview_focus_out(self, widget, evt):
        if self._packet_changed and \
           self.session.packet.rebuild_from_raw_payload(self.hexview.payload):
            # Ok we've created a correct packet. Strange? Yes it is
            # At this point we have to repopulate protocol hierarchy widget at
            # first and the follow with property tab

            self.session.reload()
            #self.reload()
        else:
            self.redraw_hexview()

        self._packet_changed = False

    def __on_hexview_changed(self, hexdoc, cdata, push_undo):
        # Dummy function. Let's the focus-out-event make the rest
        self._packet_changed = True

    def reload(self):
        self.redraw_hexview()
        self.layer_hchy.reload()
        


