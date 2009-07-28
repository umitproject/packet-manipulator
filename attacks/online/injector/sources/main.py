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
import gobject

import threading

from PM.Core.I18N import _
from PM.Core.NetConst import *
from PM.Core.Atoms import defaultdict

from PM.Gui.Core.App import PMApp

from PM.Gui.Plugins.Core import Core
from PM.Gui.Plugins.Engine import Plugin

from PM.Manager.AttackManager import *

from PM.Backend import MetaPacket

COLUMN_SRC,    \
COLUMN_PSRC,   \
COLUMN_DST,    \
COLUMN_PDST,   \
COLUMN_PROTO,  \
COLUMN_STATUS, \
COLUMN_BYTES,  \
COLUMN_OBJECT = range(8)

# Special constant to track idle connections
CONN_IDLE = CONN_TIMED_OUT + 1


def _kill_stream_seq(ctx, stream, seqoff):
    pkt = MetaPacket.new('ip') / MetaPacket.new('tcp')
    pkt.set_field('ip.src', stream.get_source())
    pkt.set_field('ip.dst', stream.get_dest())
    pkt.set_field('tcp.sport', stream.sport)
    pkt.set_field('tcp.dport', stream.dport)
    pkt.set_field('tcp.seq', stream.client.first_data_seq + \
                  stream.server.count + stream.server.urg_count + \
                  (seqoff and stream.server.window / 2 or 0))
    pkt.set_field('tcp.flags', TH_RST)

    ctx.si_l3(pkt)

    pkt = MetaPacket.new('ip') / MetaPacket.new('tcp')
    pkt.set_field('ip.src', stream.get_dest())
    pkt.set_field('ip.dst', stream.get_source())
    pkt.set_field('tcp.sport', stream.dport)
    pkt.set_field('tcp.dport', stream.sport)
    pkt.set_field('tcp.seq', stream.server.first_data_seq + \
                  stream.client.count + stream.client.urg_count + \
                  (seqoff and stream.client.window / 2 or 0))
    pkt.set_field('tcp.flags', TH_RST)

    ctx.si_l3(pkt)

def kill_stream(ctx, stream):
    _kill_stream_seq(ctx, stream, False)
    _kill_stream_seq(ctx, stream, True)

class ConnectionsList(gtk.GenericTreeModel):
    __gtype_name__ = 'ConnectionsList'

    columns = (
        gobject.TYPE_STRING, gobject.TYPE_INT,
        gobject.TYPE_STRING, gobject.TYPE_INT,
        gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_INT
    )

    def __init__(self):
        gtk.GenericTreeModel.__init__(self)

        # This contains pointer to streams or tuple of values for orphans
        self.stream_list = []

        # This is to speedup the search phase
        self.stream_dict = {}

    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY|gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_n_columns(self):
        return len(self.columns)

    def on_get_column_type(self, index):
        return self.columns[index]

    def on_get_iter(self, path):
        try:
            if self.stream_list[path[0]]:
                return path[0]
        except IndexError:
            return None

    def on_get_path(self, rowref):
        return tuple(rowref)

    def on_get_value(self, rowref, column):
        try:
            return self.stream_list[rowref][column]
        except IndexError:
            return None

    def on_iter_next(self, rowref):
        try:
            self.stream_list[rowref+1]
        except IndexError:
            return None
        else:
            return rowref+1

    def on_iter_children(self, parent):
        return None

    def on_iter_has_child(self, rowref):
        return False

    def on_iter_n_children(self, rowref):
        if rowref:
            return 0
        return len(self.stream_list)

    def on_iter_nth_child(self, parent, n):
        if parent:
            return None
        try:
            self.stream_list[n]
        except IndexError:
            return None
        else:
            return n

    def on_iter_parent(self, child):
        return None


gobject.type_register(ConnectionsList)

class ConnectionsWindow(gtk.Dialog):
    def __init__(self, reassembler):
        self.session = None
        self.reassembler = reassembler

        self.status_string = (_('established'), _('active'), _('reset'),
                              _('closed'), _('timed out'), _('idle'))

        gtk.Dialog.__init__(self, _('Active connections'), PMApp().main_window,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        self.vbox.set_border_width(4)

        self.stream_dict = {}

        self.store = gtk.ListStore(str, int, str, int, str, int, int, object)
        self.tree = gtk.TreeView(self.store)

        idx = 0
        rend = gtk.CellRendererText()

        for lbl in (_('Host'), _('Port'), _('Host'), _('Port'), \
                    _('Protocol'), _('Status'), _('Bytes')):

            col = gtk.TreeViewColumn(lbl, rend, text=idx)

            if idx == COLUMN_STATUS:
                col.set_cell_data_func(rend, self.__status_data_func)

            self.tree.append_column(col)
            idx += 1

        self.tree.set_rules_hint(True)
        self.tree.set_search_column(0)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        sw.add(self.tree)
        sw.show_all()

        self.vbox.pack_start(sw)

        self.menu = gtk.Menu()

        lbls = (('details', _('Details'), gtk.STOCK_INFO, self.__on_details),
                ('kill', _('Kill connection'), gtk.STOCK_CLEAR, self.__on_kill))

        for name, lbl, stock, callback in lbls:
            act = gtk.Action(name, lbl, None, stock)
            act.connect('activate', callback)

            item = act.create_menu_item()
            item.show()

            self.menu.append(item)

        self.connect('response', self.__on_response)
        self.tree.connect('button-press-event', self.__on_button_pressed)

        gobject.timeout_add(1000, self.__on_update_tree)

    def add_connection(self, stream):
        if stream in self.stream_dict and self.stream_dict[stream][0] is stream:
            self.remove_connection(stream)

        self.store.append(
            [stream.get_source(), stream.sport, stream.get_dest(), stream.dport,
             'TCP', stream.state, stream.get_bytes(), stream]
        )

        path = self.store.iter_n_children(None) - 1
        self.stream_dict[stream] = (stream, path)

        log.debug('Connection added')

    def remove_connection(self, stream):
        idx = self.stream_dict[stream][1]

        del self.stream_dict[stream]

        self.store[idx][COLUMN_OBJECT] = (stream.get_bytes(), stream.state)

        log.debug('Reference removed')

    def get_extern_iter(self, top=True):
        rect = self.tree.get_visible_rect()
        x, y = self.tree.widget_to_tree_coords(rect.x,
                                               (top and rect.y or rect.height))

        x += 2
        y += (top and 2 or -2)

        path = self.tree.get_path_at_pos(x, y)

        try:
            if path:
                return self.store.get_iter(path[0])

            if top:
                return self.store.get_iter_first()
        except:
            pass

    def __on_details(self, action):
        pass

    def __on_kill(self, action):
        sel = self.tree.get_selection()
        model, iter = sel.get_selected()

        if iter:
            stream = self.store.get_value(iter, COLUMN_OBJECT)

            if stream and not isinstance(stream, (tuple, int)):
                kill_stream(self.session.context, stream)

    def __on_button_pressed(self, widget, evt):
        sel = self.tree.get_selection()
        model, iter = sel.get_selected()

        if evt.button != 3:
            return

        if iter:
            stream = self.store.get_value(iter, COLUMN_OBJECT)

            if stream and not isinstance(stream, (tuple, int)):
                self.menu.show()
                self.menu.popup(None, None, None, evt.button, evt.time, None)

    def __on_update_tree(self):
        log.debug('Updating tree view (%d connections)' % \
                  self.store.iter_n_children(None))

        start, end = self.get_extern_iter(), self.get_extern_iter(False)

        if not start:
            return True

        while start != end:
            try:
                stream = self.store.get_value(start, COLUMN_OBJECT)
            except Exception, err:
                return True

            if isinstance(stream, tuple):
                self.store.set_value(start, COLUMN_BYTES, stream[0])
                self.store.set_value(start, COLUMN_STATUS, stream[1])
                self.store.set_value(start, COLUMN_OBJECT, None)
            elif stream is not None:
                old_bytes = self.store.get_value(start, COLUMN_BYTES)
                new_bytes = stream.get_bytes()

                if old_bytes == new_bytes:
                    self.store.set_value(start, COLUMN_STATUS, CONN_IDLE)
                else:
                    self.store.set_value(start, COLUMN_STATUS, stream.state)
                    self.store.set_value(start, COLUMN_BYTES, new_bytes)

            start = self.store.iter_next(start)

        return True

    def __status_data_func(self, col, cell, model, iter):
        idx = model.get_value(iter, COLUMN_STATUS)

        assert idx >= 0 and idx <= 5, 'Status id cannot be %d' % idx

        cell.set_property('text', self.status_string[idx])

    def __on_response(self, dialog, rid):
        if rid == gtk.RESPONSE_CLOSE:
            self.hide()

class Injector(Plugin, OnlineAttack):
    def start(self, reader):
        tcpdecoder = Core().get_need(reader, 'TCPDecoder')

        if not tcpdecoder:
            raise PMErrorException('TCPDecoder plugin not loaded.')

        if not tcpdecoder.reassembler:
            raise PMErrorException('TCP segments reassembling disabled '
                                   'in TCPDecoder.')

        tcpdecoder.reassembler.inject_cb = self.__inject_cb
        tcpdecoder.reassembler.add_analyzer(self.__tcp_callback)

        self.item = self.add_menu_entry('Injector', _('Active connections'),
                                        _('View active connections or inject '
                                          'data in active one'),
                                        gtk.STOCK_INDEX)

        self.window = ConnectionsWindow(tcpdecoder.reassembler)

    def stop(self):
        self.remove_menu_entry(self.item)
        self.window.destroy()

    def execute_attack(self, sess, inp_dict):
        self.window.session = sess

        if not self.window.flags() & gtk.VISIBLE:
            self.window.show()

    def __inject_cb(self, type, stream, mpkt, rcv):
        log.debug('Managing injection of %s' % mpkt)

        if type == INJ_MODIFIED:
            pass
        elif type == INJ_FORWARD:
            pass

    def __tcp_callback(self, stream, mpkt):
        self.window.add_connection(stream)
        stream.listeners.append(self.__follow_connection)

    def __follow_connection(self, stream, mpkt, rcv):
        if stream.state != CONN_DATA:
            self.window.remove_connection(stream)

        return INJ_COLLECT_STATS

__plugins__ = [Injector]
__plugins_deps__ = [('Injector', ['TCPDecoder'], [], [])]

__attack_type__ = 1
__protocols__ = (('tcp', None), )
