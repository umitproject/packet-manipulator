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
import pango

from sys import maxint

from umit.pm import backend
from umit.pm.core.i18n import _
from umit.pm.core.logger import log

from umit.pm.core.atoms import Node, defaultdict
from umit.pm.backend import SequencePacket, SequenceContext

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.core.icons import get_pixbuf
from umit.pm.gui.widgets.interfaces import InterfacesCombo
from umit.pm.gui.widgets.cellrenderer import GridRenderer
from umit.pm.higwidgets.higtooltips import HIGTooltip, HIGTooltipData

from umit.pm.gui.pages.base import Perspective

from umit.pm.manager.preferencemanager import Prefs
from umit.pm.gui.tabs.operationstab import SequenceOperation, SendOperation, \
                                      SendReceiveOperation

class FilterLayer(gtk.ComboBox):
    def __init__(self):
        self.icon = get_pixbuf('layer_small')
        self.store = gtk.ListStore(gtk.gdk.Pixbuf, str)

        super(FilterLayer, self).__init__(self.store)

        pix = gtk.CellRendererPixbuf()
        txt = gtk.CellRendererText()

        self.pack_start(pix, False)
        self.pack_start(txt, True)

        self.add_attribute(pix, 'pixbuf', 0)
        self.add_attribute(txt, 'text', 1)

    def populate(self, packets):
        self.store.clear()

        dct = defaultdict(int)

        for packet in packets:
            names = [backend.get_proto_name(proto) \
                     for proto in packet.get_protocols()]

            for name in names:
                dct[name] += 1

        sortable = [(v, k) for (k, v) in dct.items()]
        sortable.sort()
        sortable.reverse()

        self.store.append([self.icon, _('No filter')])

        for value, name in sortable:
            self.store.append([self.icon, name])

        self.set_active(0)

    def get_active_protocol(self):
        "@return the active protocol class or None"

        if self.get_active() <= 0:
            return None

        iter = self.get_active_iter()

        if iter:
            proto_str = self.store.get_value(iter, 1)

            return backend.get_proto(proto_str)

        return None


class SequencePage(Perspective):
    """
    The tree contains a list of packet for example:
     + ICMP request
       + TCP syn
       + TCP syn ack
       ..
       + TCP fin
     + ICMP reply

    So the ICMP request and reply are sent in sequence with a given
    interval, but TCP packets are sent only if we have a received packet
    for the first ICMP packet.

    TODO: add also a filter to check if the received packets meets the criteria
    """

    icon = gtk.STOCK_INDEX
    title = _('Sequence perspective')

    def create_ui(self):
        # Toolbar
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        self.intf_combo = InterfacesCombo()

        item = gtk.ToolItem()
        item.add(self.intf_combo)

        self.toolbar.insert(item, -1)

        action = gtk.Action(None, None, _('Run the sequence'),
                            gtk.STOCK_EXECUTE)
        action.connect('activate', self.__on_run)
        self.toolbar.insert(action.create_tool_item(), -1)

        self.toolbar.insert(gtk.SeparatorToolItem(), -1)

        stocks = (gtk.STOCK_GO_UP, gtk.STOCK_GO_DOWN)
        tooltips = (_('Send packet'), _('Send/receive packet'))
        callbacks = (self.__on_send, self.__on_send_receive)

        for tooltip, stock, callback in zip(tooltips, stocks, callbacks):
            action = gtk.Action(None, None, tooltip, stock)
            action.connect('activate', callback)
            self.toolbar.insert(action.create_tool_item(), -1)

        self.toolbar.insert(gtk.SeparatorToolItem(), -1)

        # Count/interval

        self.packet_count = gtk.SpinButton(gtk.Adjustment(1, 0, maxint, 1, 10))
        self.packet_interval = gtk.SpinButton(gtk.Adjustment(500, 0, maxint,
                                                             1, 10))

        for lbl, widget in zip((_('No:'), _('Interval (ms):')),
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

        tooltips = (_('Use strict checking for the replies'),
                    _('Report also received packets'),
                    _('Report also sent packets'))

        self.check_strict = gtk.CheckButton("Strict")
        self.check_received = gtk.CheckButton("Received")
        self.check_sent = gtk.CheckButton("Sent")

        self.check_strict.set_active(True)
        self.check_sent.set_active(True)

        for widget, tip in zip((self.check_strict,
                                self.check_received,
                                self.check_sent), tooltips):

            item = gtk.ToolItem()
            item.add(widget)

            widget.set_tooltip_text(tip)
            self.toolbar.insert(item, -1)

        # Combo
        space = gtk.ToolItem()
        space.set_homogeneous(False)
        space.set_expand(True)
        self.toolbar.insert(space, -1)

        action = gtk.Action(None, None, _('Merge selection'),
                            gtk.STOCK_COLOR_PICKER)
        action.connect('activate', self.__on_merge)
        self.toolbar.insert(action.create_tool_item(), -1)

        self.combo = FilterLayer()

        item = gtk.ToolItem()
        item.add(self.combo)
        item.set_homogeneous(False)
        self.toolbar.insert(item, -1)

        self.pack_start(self.toolbar, False, False)

        # Packet
        self.store = gtk.TreeStore(object)
        self.tree = gtk.TreeView(self.store)

        rend = GridRenderer()
        col = gtk.TreeViewColumn(_('Packet sequence'), rend)
        col.set_cell_data_func(rend, self.__txt_cell_data)

        self.tree.append_column(col)
        self.tree.set_rules_hint(True)

        self.use_colors = False

        # Filtering
        self.active_layer = None
        self.active_packets = []
        self.active_diff = None

        self.merging = False
        self.filter_store = gtk.ListStore(str, object)

        target_packet = ('PMPacket', gtk.TARGET_SAME_WIDGET, 0)
        target_plain = ('text/plain', 0, 0)

        self.tree.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
                                           [target_packet],
                                           gtk.gdk.ACTION_MOVE)
        self.tree.enable_model_drag_dest([target_plain, target_packet],
                                         gtk.gdk.ACTION_MOVE | \
                                         gtk.gdk.ACTION_COPY)

        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.tree)

        self.pack_start(sw)

        self.selected_packets = []
        self.context_menu = gtk.Menu()

        labels = (_('&Remove selected'),
                  _('&Copy selected'),
                  _('&Paste selected'))

        icons = (gtk.STOCK_DELETE, gtk.STOCK_COPY, gtk.STOCK_PASTE)
        callbacks = (self.__on_remove, self.__on_copy, self.__on_paste)

        for lbl, icon, cb in zip(labels, icons, callbacks):
            action = gtk.Action(None, None, lbl, icon)
            action.connect_accelerator()
            action.connect('activate', cb)
            self.context_menu.append(action.create_menu_item())

        self.context_menu.show_all()

        # Connect signals here

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

        Prefs()['gui.maintab.sequenceview.font'].connect(self.__modify_font)
        Prefs()['gui.maintab.sequenceview.usecolors'].connect(
            self.__modify_colors
        )

        self.tree.connect('button-press-event', self.__on_tree_button_pressed)
        self.tree.connect('drag-data-received', self.__on_drag_data)
        self.tree.get_selection().connect('changed',
                                          self.__on_selection_changed)

        self.combo.connect('changed', self.__on_filter)

        # Setting up the gui controls

        if isinstance(self.session.context, SequenceContext):
            self.packet_count.set_value(self.session.context.tot_loop_count)
            self.packet_interval.set_value(self.session.context.inter * 1000.0)

        self.check_received.set_active(self.session.context.report_recv)
        self.check_sent.set_active(self.session.context.report_sent)
        self.check_strict.set_active(self.session.context.strict)

        self.check_strict.connect('toggled', self.__on_strict_toggled)
        self.check_received.connect('toggled', self.__on_recv_toggled)
        self.check_sent.connect('toggled', self.__on_sent_toggled)

        self.packet_count.connect('value-changed', self.__on_pcount_changed)
        self.packet_interval.connect('value-changed', self.__on_pinter_changed)

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

    def get_current_tree(self):
        tree = Node()

        def add_to_tree(model, path, iter, tree):
            obj = SequencePacket(model.get_value(iter, 0))
            parent = model.iter_parent(iter)

            if not parent:
                tree.append_node(Node(obj))
            else:
                path = model.get_path(parent)
                parent = tree.get_from_path(path)
                parent.append_node(Node(obj))

        self.store.foreach(add_to_tree, tree)

        return tree

    def reload(self, packet=None):
        # Should be the selected

        if self.tree.get_selection().get_mode() == gtk.SELECTION_MULTIPLE:
            return

        if packet is not None:
            ret = self.tree.get_selection().get_selected()

            if ret:
                model, iter = ret
                if model.get_value(iter, 0) is packet:

                    model.row_changed(model.get_path(iter), iter)
                    self.__update_combo()

                    log.debug("row changed for current packet")

                    return
                else:
                    log.debug("Packet edited and packet selected differs")

        # If we are here the selection is not the packet so
        # rebuild entire tree.

        log.debug("Redrawing all the Sequence")

        self.store.clear()

        tree = self.session.context.get_sequence()

        if tree:
            for child in tree.get_children():
                self.__add_to_store(child, None)

            self.tree.get_selection().select_path((0, ))

        self.__update_combo()

    def __add_to_store(self, child, root):
        spak = child.get_data()
        root = self.store.append(root, [spak.packet])

        if child.is_parent():
            for node in child.get_children():
                self.__add_to_store(node, root)

        return root

    def __on_run(self, action):
        # We have to construct a sequence and run our operation :D

        tree = Node()

        def complete_sequence(model, path, iter, tree):
            path = list(path)[:-1]
            node = Node(SequencePacket(model.get_value(iter, 0)))

            if path:
                tree = tree.get_from_path(path)

            tree.append_node(node)

        self.store.foreach(complete_sequence, tree)

        count = self.packet_count.get_value_as_int()
        inter = self.packet_interval.get_value_as_int()

        operation = SequenceOperation(tree, count, inter,
                                      self.intf_combo.get_interface(),
                                      self.check_strict.get_active(),
                                      self.check_received.get_active(),
                                      self.check_sent.get_active())

        tab = PMApp().main_window.get_tab("OperationsTab")
        tab.tree.append_operation(operation)

    def __on_send(self, action):
        packet = self.session.packet

        if not packet:
            return

        # We start a background process in Operations tab

        count = self.packet_count.get_value_as_int()
        inter = self.packet_interval.get_value_as_int()

        tab = PMApp().main_window.get_tab("OperationsTab")
        tab.tree.append_operation(
            SendOperation(packet, count, inter,
                          self.intf_combo.get_interface())
        )

    def __on_send_receive(self, action):
        packet = self.session.packet

        if not packet:
            return

        # We start a background process in Operations tab

        count = self.packet_count.get_value_as_int()
        inter = self.packet_interval.get_value_as_int()

        strict = self.check_strict.get_active()
        recv = self.check_received.get_active()
        sent = self.check_sent.get_active()

        tab = PMApp().main_window.get_tab("OperationsTab")
        tab.tree.append_operation(
            SendReceiveOperation(packet, count, inter,
                                 self.intf_combo.get_interface(),
                                 strict, recv, sent)
        )

    def __on_tree_button_pressed(self, widget, evt):
        if evt.button != 3:
            return False

        self.context_menu.popup(None, None, None, evt.button, evt.time, None)

        return True

    def __txt_cell_data(self, col, rend, model, iter):
        if self.merging:
            tot = model.get_value(iter, 0)
            packet = model.get_value(iter, 1)

            rend.set_property('text', "%s) %s" % (tot, packet.summary()))
        else:
            tot = ".".join([str(i + 1) for i in model.get_path(iter)])

            packet = model.get_value(iter, 0)

            rend.set_property('text', "%s) %s" % (tot, packet.summary()))
            rend.set_property('cell-background-gdk', self.__get_color(packet))

    def refilter(self):
        self.filter_store.clear()

        def add_to_store(model, path, iter, store):
            packet = model.get_value(iter, 0)

            if packet.haslayer(self.active_layer):
                tot = ".".join([str(i + 1) for i in model.get_path(iter)])
                store.append([tot, packet])

        self.store.foreach(add_to_store, self.filter_store)

    def append_packet(self, packet, coords=None):
        """
        Append a packet to the sequence
        @param packet a MetaPacket or a str
        @param coords a tuple (x, y) or
                      True for appending after selection or None
        @return True if the packet is appended
        """

        if self.merging:
            return False

        assert isinstance(packet, (basestring, backend.MetaPacket)), \
            "A string or MetaPacket instance is required"

        if isinstance(packet, basestring):
            protoklass = backend.get_proto(packet)

            if not protoklass:
                return False

            packet = backend.MetaPacket(protoklass())

        ret = None

        if isinstance(coords, tuple) and len(coords) == 2:
            ret = self.tree.get_dest_row_at_pos(*coords)

        if ret:
            path, pos = ret
            iter = self.store.get_iter(path)

            if pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE or \
               pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
                self.store.prepend(iter, [packet])
            elif pos == gtk.TREE_VIEW_DROP_BEFORE:
                self.store.insert_before(None, iter, [packet])
            elif pos == gtk.TREE_VIEW_DROP_AFTER:
                self.store.insert_after(None, iter, [packet])
        elif not ret and coords == True:
            model, iter = self.tree.get_selection().get_selected()

            if iter:
                self.store.insert_after(None, iter, [packet])
            else:
                self.store.append(None, [packet])
        else:
            self.store.append(None, [packet])

        return True

    def __on_drag_data(self, widget, ctx, x, y, data, info, time):
        if self.merging:
            ctx.finish(False, False, time)

        ret = False

        if data:
            if data.format == 8:
                ret = self.append_packet(data.data, (x, y))
            elif str(data.target) == 'PMPacket':
                ret = self.tree.get_selection().get_selected()

                if ret:
                    packet = ret[0].get_value(ret[1], 0)
                    ret = self.append_packet(packet, (x, y))

            if ret:
                if data.format == 8:
                    ctx.finish(True, False, time)
                else:
                    ctx.finish(True, True, time)

                self.__update_combo()

                # Mark as dirty
                self.session.context.status = self.session.context.NOT_SAVED

                return True

        ctx.finish(False, False, time)

    def __on_filter(self, combo):
        self.active_layer = self.combo.get_active_protocol()

        if self.active_layer:
            self.merging = True

            self.tree.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

            self.refilter()
            self.tree.set_model(self.filter_store)
        else:
            self.merging = False
            self.tree.get_selection().set_mode(gtk.SELECTION_SINGLE)
            self.tree.set_model(self.store)

            if self.active_diff:
                tab = PMApp().main_window.get_tab('PropertyTab')
                tab.remove_notify_for(self.active_diff, self.__diff_editing)

                self.active_diff = None
                self.active_packets = []
                self.active_layer = None

                self.tree.get_selection().select_path((0, ))

    def __on_copy(self, action):
        if self.merging:
            return

        model, iter = self.tree.get_selection().get_selected()

        if iter:
            metapacket = model.get_value(iter, 0)
            self.selected_packets = [metapacket]

    def __on_paste(self, action):
        if self.merging or not self.selected_packets:
            return

        model, iter = self.tree.get_selection().get_selected()

        for packet in self.selected_packets:
            iter = self.store.insert_after(None, iter, [packet.copy()])

    def __on_remove(self, action):
        if self.merging:
            return

        model, iter = self.tree.get_selection().get_selected()

        if iter:
            model.remove(iter)
            self.session.set_active_packet(None)


    def __on_strict_toggled(self, widget):
        self.session.context.strict = widget.get_active()
        self.session.context.status = self.session.context.NOT_SAVED

    def __on_recv_toggled(self, widget):
        self.session.context.report_recv = widget.get_active()
        self.session.context.status = self.session.context.NOT_SAVED

    def __on_sent_toggled(self, widget):
        self.session.context.report_sent = widget.get_active()
        self.session.context.status = self.session.context.NOT_SAVED

    def __on_pcount_changed(self, widget):
        if isinstance(self.session.context, SequenceContext):
            self.session.context.tot_loop_count = widget.get_value_as_int()
            self.session.context.status = self.session.context.NOT_SAVED

    def __on_pinter_changed(self, widget):
        if isinstance(self.session.context, SequenceContext):
            # This part / 1000.0 should not compare here. We should instead add
            # a property to the context to manage this format conversion.
            self.session.context.inter = widget.get_value_as_int() / 1000.0
            self.session.context.status = self.session.context.NOT_SAVED


    def __on_selection_changed(self, sel):
        sel = self.tree.get_selection()

        if self.active_packets:
            self.active_packets = []

        if sel.get_mode() == gtk.SELECTION_MULTIPLE:
            model, lst = sel.get_selected_rows()

            for path in lst:
                # We are the list store
                packet = model.get_value(model.get_iter(path), 1)
                self.active_packets.append(packet)

            log.debug("Repopulating active_packets with selection %s" % \
                      self.active_packets)

            self.session.set_active_packet(None)

        elif sel.get_mode() == gtk.SELECTION_SINGLE:
            ret = sel.get_selected()

            if ret:
                model, iter = ret

                if iter:
                    self.session.set_active_packet(model.get_value(iter, 0))

    def __on_merge(self, action):
        tab = PMApp().main_window.get_tab('PropertyTab')

        if self.active_diff:
            tab.remove_notify_for(self.active_diff, self.__diff_editing)
            self.active_diff = None

        if not self.active_layer or not self.active_packets:
            return

        log.debug("Merging %d packets" % len(self.active_packets))

        self.active_diff = backend.MetaPacket(self.active_layer())
        self.session.set_active_packet(self.active_diff)

        # Now we should connect the property tree signals to our
        # but we should check if the packet edited is our or not
        # because the property manages the edit phase of multiple
        # packets in multiple changes.

        tab.register_notify_for(self.active_diff, self.__diff_editing)

    def __diff_editing(self, packet, proto, field, editing):
        if not editing:
            # We don't care about selection
            return

        log.debug("Sanity check: %s" % ((packet is self.active_diff) and ("OK")\
                                        or ("FAILED")))

        # Now we have to recursivly set the field value to all active_packets
        val = backend.get_field_value(proto, field)

        for packet in self.active_packets:
            layer = packet.getlayer(self.active_layer)
            field = backend.get_proto_field(layer, field.name)

            log.debug("Setting value to %s" % field)

            def emit_row_changed(model, path, iter):
                model.row_changed(path, iter)

            self.filter_store.foreach(emit_row_changed)

            backend.set_field_value(layer, field, val)

    def __update_combo(self):
        lst = []

        def add_to_list(model, path, iter, lst):
            lst.append(model.get_value(iter, 0))

        self.store.foreach(add_to_list, lst)
        self.combo.populate(lst)

if __name__ == "__main__":
    w = gtk.Window()
    w.add(SequencePage())
    w.show_all()
    gtk.main()
