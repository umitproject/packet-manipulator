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

import string
import threading

from PM.Core.I18N import _
from PM.Core.NetConst import *
from PM.Core.Atoms import defaultdict

from PM.Gui.Core.App import PMApp

from PM.Gui.Plugins.Core import Core
from PM.Gui.Plugins.Engine import Plugin

from PM.Manager.AuditManager import *

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

escape_table = '.........\t\n\x0b\x0c\r..................' \
               ' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFG' \
               'HIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmno' \
               'pqrstuvwxyz{|}~..........................' \
               '.........................................' \
               '.........................................' \
               '.....................'

escape_raw = lambda x: string.translate(x, escape_table)

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

class InjectDialog(gtk.Dialog):
    def __init__(self, stream, inj_file=False):
        gtk.Dialog.__init__(self, _('Active connections'), PMApp().main_window,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        tbl = gtk.Table(2, 2, False)

        self.rsrc = gtk.RadioButton(None, '%s:%d' % (stream.get_source(),
                                                     stream.sport))
        self.rdst = gtk.RadioButton(rsrc, '%s:%d' % (stream.get_dest(),
                                                     stream.dport))

        lbl = gtk.Label(_('Send to:'))
        lbl.set_alignment(.0, .5)

        tbl.attach(lbl, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        tbl.attach(self.rsrc, 1, 2, 0, 1, gtk.FILL, gtk.FILL)
        tbl.attach(self.rdst, 2, 3, 0, 1, gtk.FILL, gtk.FILL)

        if inj_file:
            self.entry = gtk.Entry()
            btn = gtk.Button(stock=gtk.STOCK_OPEN)
            btn.connect('clicked', self.__on_open, self.entry)

            tbl.attach(self.entry, 0, 2, 1, 2, yoptions=gtk.FILL)
            tbl.attach(btn, 2, 3, 1, 2, gtk.FILL, gtk.FILL)

        else:
            self.view = gtk.TextView()

            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

            sw.add(self.view)

            tbl.attach(sw, 0, 3, 1, 2)

        tbl.show_all()
        self.vbox.pack_start(tbl, False, False)

    def __on_open(self, btn, entry):
        dialog = gtk.FileChooserDialog(_('Select a file to inject'),
                              PMApp().main_window, gtk.FILE_CHOOSER_ACTION_OPEN,
                              (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                               gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            entry.set_text(dialog.get_filename())

        dialog.hide()
        dialog.destroy()

    def get_inject_data(self):
        is_client = rdst.get_active()

        if hasattr(self, 'entry'):
            fname = self.entry.get_text()

            try:
                return is_client, open(fname, 'r').read()
            except:
                return is_client, None
        else:
            return is_client, self.view.get_buffer().get_text(
                *self.view.get_buffer().get_bounds()
            )

class TabDetails(gtk.VBox):
    tagtable = None

    def __init__(self, connw, stream):
        gtk.VBox.__init__(self, False, 2)

        self.stream = stream
        self.connw = connw

        # This is for data collected
        # Everything is saved in the form (is_client : bool, data : str)
        self.data_frags = []

        # This is for data to inject
        self.client_inj_frags = []
        self.server_inj_frags = ['USER test injection test :Tester\r\n', 'PING :pingthis\r\n']

        if not self.tagtable:
            self.tagtable = gtk.TextTagTable()

            tag = gtk.TextTag('src')
            tag.set_property('foreground', 'blue')
            tag.set_property('font', 'Monospace 9')
            self.tagtable.add(tag)

            tag = gtk.TextTag('dst')
            tag.set_property('foreground', 'red')
            tag.set_property('font', 'Monospace 9')
            self.tagtable.add(tag)

        self.buff = gtk.TextBuffer(self.tagtable)
        self.view = gtk.TextView(self.buff)
        self.view.set_wrap_mode(gtk.WRAP_CHAR)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        sw.add(self.view)

        self.pack_start(sw)

        bb = gtk.HButtonBox()
        bb.set_layout(gtk.BUTTONBOX_END)

        btn = gtk.Button(_('Inject file'))
        btn.set_relief(gtk.RELIEF_NONE)
        btn.connect('clicked', self.__on_inject, True)

        bb.pack_start(btn)

        btn = gtk.Button(_('Inject data'))
        btn.set_relief(gtk.RELIEF_NONE)
        btn.connect('clicked', self.__on_inject, False)

        bb.pack_start(btn)

        btn = gtk.Button(_('Kill connection'))
        btn.set_relief(gtk.RELIEF_NONE)
        btn.connect('clicked', self.__on_kill)

        bb.pack_start(btn)

        btn = gtk.Button(stock=gtk.STOCK_CLOSE)
        btn.set_relief(gtk.RELIEF_NONE)
        btn.connect('clicked', self.__on_close)

        bb.pack_start(btn)

        self.pack_start(bb, False, False)

    def __on_close(self, btn):
        self.connw.remove_tab_details(self)

    def __on_kill(self, btn):
        kill_stream(self.connw.session.context, self.stream)

    def __on_inject(self, btn, is_file):
        dialog = InjectDialog(self.stream, is_file)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            is_client, data = dialog.get_inject_data()

            if data:
                if is_client:
                    self.client_inj_frags.append(data)
                else:
                    self.server_inj_frags.append(data)

        dialog.hide()
        dialog.destroy()

class ConnectionsWindow(gtk.Dialog):
    def __init__(self, reassembler):
        self.session = None
        self.reassembler = reassembler

        self.stream_dict = {}
        self.following = {}

        self.status_string = (_('established'), _('active'), _('reset'),
                              _('closed'), _('timed out'), _('idle'))

        gtk.Dialog.__init__(self, _('Active connections'), PMApp().main_window,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        self.vbox.set_border_width(4)

        vbox = gtk.VBox(False, 2)
        vbox.set_border_width(4)

        self.notebook = gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.append_page(vbox, gtk.Label(_('Connections')))

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
        vbox.pack_start(sw)

        self.vbox.pack_start(self.notebook)
        self.notebook.show_all()

        self.menu = gtk.Menu()

        lbls = (('details', _('Details'), gtk.STOCK_INFO, self.__on_details),
                ('kill', _('Kill connection'), gtk.STOCK_CLEAR, self.__on_kill),
                ('clear', _('Clear'), gtk.STOCK_CLEAR, self.__on_clear))

        for name, lbl, stock, callback in lbls:
            act = gtk.Action(name, lbl, None, stock)
            act.connect('activate', callback)

            item = act.create_menu_item()
            item.show()

            self.menu.append(item)

        self.connect('response', self.__on_response)
        self.tree.connect('button-press-event', self.__on_button_pressed)

        self.update_id = None
        self.set_size_request(400, 200)

    def start_update(self):
        if not self.update_id:
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

        # DEBUG: remove me after injection is complete
        if stream.sport in (6667, 80) or stream.dport in (6667, 80):
            details = TabDetails(self.session, stream)
            details.show_all()

            self.following[stream] = details

            self.notebook.append_page(details, gtk.Label('%s:%d <-> %s:%d' \
                % (stream.get_source(), stream.sport,
                   stream.get_dest(), stream.dport)))

        log.debug('Connection added')

    def remove_connection(self, stream):
        if stream in self.stream_dict:
            return

        idx = self.stream_dict[stream][1]

        del self.stream_dict[stream]

        self.store[idx][COLUMN_OBJECT] = (stream.get_bytes(), stream.state)

        log.debug('Reference removed')

    def remove_tab_details(self, tab):
        pass

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
        sel = self.tree.get_selection()
        model, iter = sel.get_selected()

        if iter:
            stream = self.store.get_value(iter, COLUMN_OBJECT)

            if stream and not isinstance(stream, (tuple, int)):
                details = TabDetails(self.session, stream)
                details.show_all()

                self.following[stream] = details

                self.notebook.append_page(details, gtk.Label('%s:%d <-> %s:%d' \
                    % (stream.get_source(), stream.sport,
                       stream.get_dest(), stream.dport)))

    def __on_kill(self, action):
        sel = self.tree.get_selection()
        model, iter = sel.get_selected()

        if iter:
            stream = self.store.get_value(iter, COLUMN_OBJECT)

            if stream and not isinstance(stream, (tuple, int)):
                kill_stream(self.session.context, stream)

    def __on_clear(self, action):
        self.stream_dict.clear()
        self.store.clear()

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
        page = self.notebook.get_current_page()

        if page == 0:
            #log.debug('Updating tree view (%d connections)' % \
            #          self.store.iter_n_children(None))

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

                        print new_bytes

                start = self.store.iter_next(start)
        else:
            page = self.notebook.get_nth_page(page)

            #log.debug('Adding missing fragments %s' % page.data_frags)

            while page.data_frags:
                is_client, data = page.data_frags.pop(0)

                page.buff.insert_with_tags(
                    page.buff.get_end_iter(), escape_raw(data),
                    page.tagtable.lookup((is_client and 'src' or 'dst')),
                )

        return True

    def __status_data_func(self, col, cell, model, iter):
        idx = model.get_value(iter, COLUMN_STATUS)

        assert idx >= 0 and idx <= 5, 'Status id cannot be %d' % idx

        cell.set_property('text', self.status_string[idx])

    def __on_response(self, dialog, rid):
        if rid == gtk.RESPONSE_CLOSE:
            if self.update_id:
                gobject.source_remove(self.update_id)

            self.hide()

class Injector(Plugin, ActiveAudit):
    def start(self, reader):
        tcpdecoder = Core().get_need(reader, 'TCPDecoder')

        if not tcpdecoder:
            raise PMErrorException('TCPDecoder plugin not loaded.')

        if not tcpdecoder.reassembler:
            raise PMErrorException('TCP segments reassembling disabled '
                                   'in TCPDecoder.')

        tcpdecoder.reassembler.analyzers.insert(0, self.__tcp_callback)

        self.item = self.add_menu_entry('Injector', _('Active connections'),
                                        _('View active connections or inject '
                                          'data in active one'),
                                        gtk.STOCK_INDEX)

        self.window = ConnectionsWindow(tcpdecoder.reassembler)
        self.window.show()
        self.window.start_update()

    def stop(self):
        self.remove_menu_entry(self.item)
        self.window.destroy()

    def execute_audit(self, sess, inp_dict):
        self.window.session = sess

        if not self.window.flags() & gtk.VISIBLE:
            self.window.show()
            self.window.start_update()

    def __tcp_callback(self, stream, mpkt):
        # DEBUG: remove me
        if stream.sport in (6667, 80) or stream.dport in (6667, 80):
            self.window.add_connection(stream)
            stream.listeners.append(self.__follow_connection)

    def __follow_connection(self, stream, mpkt, rcv):
        if stream.state != CONN_DATA:
            self.window.remove_connection(stream)

        elif stream in self.window.following:
            page = self.window.following[stream]

            log.debug('Collecting data for %s' % stream)

            if rcv is stream.server:
                data = \
                    stream.server.data[stream.server.count - \
                                       stream.server.count_new:]

                if data:
                    page.data_frags.append((0, data))

                if page.server_inj_frags:
                    inj_data = page.server_inj_frags.pop(0)
                    mpkt.set_cfield('inj::payload', inj_data)

                    return INJ_MODIFIED
            else:
                data = \
                    stream.client.data[stream.client.count - \
                                       stream.client.count_new:]

                if data:
                    page.data_frags.append((1, data))

                if page.client_inj_frags:
                    inj_data = page.client_inj_frags.pop(0)
                    mpkt.set_cfield('inj::payload', inj_data)

                    return INJ_MODIFIED

        return INJ_COLLECT_DATA

__plugins__ = [Injector]
__plugins_deps__ = [('Injector', ['TCPDecoder'], [], [])]

__audit_type__ = 1
__protocols__ = (('tcp', None), )
