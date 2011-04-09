#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2010 Adriano Monteiro Marques
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
import gobject

import string
import threading

from umit.pm.core.i18n import _
from umit.pm.core.netconst import *
from umit.pm.core.atoms import defaultdict

from umit.pm.gui.core.app import PMApp
from umit.pm.core.errors import PMErrorException

from umit.pm.gui.plugins.core import Core
from umit.pm.gui.plugins.engine import Plugin

from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import TCPIdent, SessionManager

from umit.pm.backend import MetaPacket

COLUMN_SRC,    \
COLUMN_PSRC,   \
COLUMN_DST,    \
COLUMN_PDST,   \
COLUMN_PROTO,  \
COLUMN_STATUS, \
COLUMN_BYTES,  \
COLUMN_OBJECT = range(8)

escape_table = '.........\t\n\x0b\x0c\r..................' \
               ' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFG' \
               'HIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmno' \
               'pqrstuvwxyz{|}~..........................' \
               '.........................................' \
               '.........................................' \
               '.....................'

escape_raw = lambda x: string.translate(x, escape_table)

def inject_buffer(ctx, conn, index, buff):
    if conn.l4_proto == NL_TYPE_TCP:
        proto = 'tcp'
    elif conn.l4_proto == NL_TYPE_UDP:
        proto = 'udp'
    else:
        return False

    mpkt = MetaPacket.new('ip') / MetaPacket.new(proto)

    if index == 0:
        mpkt.l3_src = conn.l3_addr1
        mpkt.l3_dst = conn.l3_addr2

        mpkt.l4_src = conn.l4_addr1
        mpkt.l4_dst = conn.l4_addr2
    else:
        mpkt.l3_src = conn.l3_addr2
        mpkt.l3_dst = conn.l3_addr1

        mpkt.l4_src = conn.l4_addr2
        mpkt.l4_dst = conn.l4_addr1

    mpkt.l4_proto = conn.l4_proto

    mpkt.set_fields('ip', {
        'src' : mpkt.l3_src,
        'dst' : mpkt.l3_dst})
    mpkt.set_fields(proto, {
        'sport' : mpkt.l4_src,
        'dport' : mpkt.l4_dst})

    mpkt.inject = buff
    mpkt.inject_len = len(buff)

    index += 2
    conn.flags = CN_INJECTED
    conn.buffers.append((index, buff))

    ctx.inject_buffer(mpkt)

    return True

def send_tcpkill(ctx, src, dst, sport, dport, seq):
    mpkt = MetaPacket.new('ip') / MetaPacket.new('tcp')

    mpkt.set_fields('ip', {
        'src' : src,
        'dst' : dst})

    mpkt.set_fields('tcp', {
        'sport' : sport,
        'dport' : dport,
        'seq' : seq,
        'ack' : 0,
        'flags' : TH_RST})

    ctx.si_l3(mpkt)

def kill_connection(ctx, conn):
    if conn.l4_proto != NL_TYPE_TCP:
        log.debug('I can kill only TCP connections')
        return False

    ident = TCPIdent(conn.l3_addr1, conn.l3_addr2,
                     conn.l4_addr1, conn.l4_addr2)

    sess = SessionManager().get_session(ident)

    if not sess:
        log.debug('Cannot find the TCP session')
        return False

    if ident.l3_src == sess.ident.l3_src:
        status = sess.data[1]
        ostatus = sess.data[0]
    else:
        status = sess.data[0]
        ostatus = sess.data[1]

    send_tcpkill(ctx, conn.l3_addr1, conn.l3_addr2,
                 conn.l4_addr1, conn.l4_addr2, ostatus.last_ack)
    send_tcpkill(ctx, conn.l3_addr2, conn.l3_addr1,
                 conn.l4_addr2, conn.l4_addr1, status.last_ack)

    conn.status = CN_KILLED

    return True

class InjectDialog(gtk.Dialog):
    def __init__(self, conn, inj_file=False):
        gtk.Dialog.__init__(self, _('Active connections'), PMApp().main_window,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        tbl = gtk.Table(2, 2, False)

        self.rsrc = gtk.RadioButton(None, '%s:%d' % (conn.l3_addr1,
                                                     conn.l4_addr1))
        self.rdst = gtk.RadioButton(self.rsrc, '%s:%d' % (conn.l3_addr2,
                                                          conn.l4_addr2))
        self.rdst.set_active(True)

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
        if self.rsrc.get_active():
            index = 1
        else:
            index = 0

        if hasattr(self, 'entry'):
            fname = self.entry.get_text()

            try:
                return index, open(fname, 'r').read()
            except:
                return index, None
        else:
            return index, self.view.get_buffer().get_text(
                *self.view.get_buffer().get_bounds()
            )

class TabDetails(gtk.VBox):
    tagtable = None

    def __init__(self, connw, conn):
        gtk.VBox.__init__(self, False, 2)

        self.connw = connw
        self.conn = conn
        self.conn.flags |= CN_VIEWING
        self.index = 0

        if not self.tagtable:
            # Create tag table if not yet allocated
            self.tagtable = gtk.TextTagTable()

            tag = gtk.TextTag('src')
            tag.set_property('foreground', 'blue')
            self.tagtable.add(tag)

            tag = gtk.TextTag('dst')
            tag.set_property('foreground', 'red')
            self.tagtable.add(tag)

            tag = gtk.TextTag('srcinj')
            tag.set_property('weight', pango.WEIGHT_BOLD)
            tag.set_property('foreground', 'blue')
            self.tagtable.add(tag)

            tag = gtk.TextTag('dstinj')
            tag.set_property('weight', pango.WEIGHT_BOLD)
            tag.set_property('foreground', 'red')
            self.tagtable.add(tag)

        self.buff = gtk.TextBuffer(self.tagtable)
        self.endmark = self.buff.create_mark('end',
                                             self.buff.get_end_iter(), 0)

        self.view = gtk.TextView(self.buff)
        self.view.set_wrap_mode(gtk.WRAP_CHAR)
        self.view.set_editable(False)
        self.view.modify_font(pango.FontDescription('Monospace 9'))

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
        kill_connection(self.connw.session.context, self.conn)

    def __on_inject(self, btn, is_file):
        dialog = InjectDialog(self.conn, is_file)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            index, data = dialog.get_inject_data()

            if data:
                inject_buffer(self.connw.session.context, self.conn, index, data)

        dialog.hide()
        dialog.destroy()

    def update(self):
        if not self.conn:
            return

        tags = ('src', 'dst', 'dstinj', 'srcinj')

        if self.index > len(self.conn.buffers):
            self.index = 0
            self.buff.set_text('')

        while self.index < len(self.conn.buffers):
            is_client, buff = self.conn.buffers[self.index]
            self.buff.insert_with_tags(self.buff.get_end_iter(),
                                       escape_raw(buff),
                                       self.tagtable.lookup(tags[is_client]))

            self.index += 1

        self.view.scroll_to_mark(self.endmark, 0, False, 0, 0)

class ConnectionsWindow(gtk.Dialog):
    def __init__(self, session):
        self.session = session

        self.following = {}

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
        self.last_conn = None
        self.set_size_request(400, 200)

    def start_update(self):
        if not self.update_id:
            gobject.timeout_add(1000, self.__on_update_tree)

    def add_connection(self, conn):
        self.store.append(
            [conn.l3_addr1, conn.l4_addr1,
             conn.l3_addr2, conn.l4_addr2,
             conn.l4_proto == NL_TYPE_TCP and 'TCP' or 'UDP',
             conn.status, conn.xferred, conn]
        )
        self.last_conn = conn

    def remove_tab_details(self, tab):
        log.debug('Removing page')

        pagenum = self.notebook.page_num(tab)
        self.notebook.remove_page(pagenum)

        if tab.conn in self.following:
            tab.conn.flags &= ~CN_VIEWING
            del self.following[tab.conn]

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
            conn = self.store.get_value(iter, COLUMN_OBJECT)

            if conn and not isinstance(conn, (tuple, int)):
                details = TabDetails(self, conn)
                details.show_all()

                self.following[conn] = details

                self.notebook.append_page(details, gtk.Label('%s:%d <-> %s:%d' \
                    % (conn.l3_addr1, conn.l4_addr1,
                       conn.l3_addr2, conn.l4_addr2)))

    def __on_kill(self, action):
        sel = self.tree.get_selection()
        model, iter = sel.get_selected()

        if iter:
            conn = self.store.get_value(iter, COLUMN_OBJECT)

            if conn and not isinstance(conn, (tuple, int)):
                kill_connection(self.session.context, conn)

    def __on_clear(self, action):
        self.store.clear()
        self.last_conn = None

    def __on_button_pressed(self, widget, evt):
        sel = self.tree.get_selection()
        model, iter = sel.get_selected()

        if evt.button != 3:
            return

        if iter:
            conn = self.store.get_value(iter, COLUMN_OBJECT)

            if conn and not isinstance(conn, (tuple, int)):
                self.menu.show()
                self.menu.popup(None, None, None, evt.button, evt.time, None)

    def __on_update_tree(self):
        page = self.notebook.get_current_page()

        if page == 0:
            log.debug('Updating tree view (%d connections)' % \
                      self.store.iter_n_children(None))

            for row in self.store:
                if row[COLUMN_OBJECT] is None:
                    self.store.remove(row.iter)

            start, end = self.get_extern_iter(), self.get_extern_iter(False)

            while start and start != end:
                try:
                    conn = self.store.get_value(start, COLUMN_OBJECT)
                except Exception, err:
                    break

                if isinstance(conn, tuple):
                    self.store.set_value(start, COLUMN_BYTES, conn[0])
                    self.store.set_value(start, COLUMN_STATUS, conn[1])
                    self.store.set_value(start, COLUMN_OBJECT, None)
                elif conn is not None:
                    self.store.set_value(start, COLUMN_BYTES, conn.xferred)
                    self.store.set_value(start, COLUMN_STATUS, conn.status)

                start = self.store.iter_next(start)

            # Ok now let's add newer connections
            conn_man = self.session.context.audit_dispatcher.\
                     get_connection_manager()

            try:
                idx = conn_man.conn_list.index(self.last_conn) + 1
            except ValueError, exc:
                idx = 0

            while idx < len(conn_man.conn_list):
                self.add_connection(conn_man.conn_list[idx])
                idx += 1

        else:
            page = self.notebook.get_nth_page(page)

            if not page:
                return True

            page.update()

        return True

    def __status_data_func(self, col, cell, model, iter):
        idx = model.get_value(iter, COLUMN_STATUS)

        if idx == CN_IDLE:      out = 'idle'
        elif idx == CN_OPENING: out = 'opening'
        elif idx == CN_OPEN:    out = 'open'
        elif idx == CN_ACTIVE:  out = 'active'
        elif idx == CN_CLOSING: out = 'closing'
        elif idx == CN_CLOSED:  out = 'closed'
        elif idx == CN_KILLED:  out = 'killed'

        cell.set_property('text', out)

    def __on_response(self, dialog, rid):
        if rid == gtk.RESPONSE_CLOSE:
            if self.update_id:
                gobject.source_remove(self.update_id)

            self.hide()

class Injector(Plugin, ActiveAudit):
    def start(self, reader):
        self.item = self.add_menu_entry('Injector', _('Active connections'),
                                        _('View active connections or inject '
                                          'data in active one'),
                                        gtk.STOCK_INDEX)
        self.window = None

    def stop(self):
        self.remove_menu_entry(self.item)
        self.window.destroy()

    def execute_audit(self, sess, inp_dict):
        if self.window is None:
            self.window = ConnectionsWindow(sess)

        if not self.window.flags() & gtk.VISIBLE:
            self.window.show()
            self.window.start_update()

__plugins__ = [Injector]
__plugins_deps__ = [('Injector', ['TCPDecoder'], [], [])]

__audit_type__ = 1
__protocols__ = (('tcp', None), )
__vulnerabilities__ = (('TCP session hijacking', {
    'description' : 'TCP session hijacking is when a hacker takes over a TCP '
                    'session between two machines. Since most authentication '
                    'only occurs at the start of a TCP session, this allows '
                    'the hacker to gain access to a machine.\n\n'
                    'A popular method is using source-routed IP packets. This '
                    'allows a hacker at point A on the network to participate '
                    'in a conversation between B and C by encouraging the IP '
                    'packets to pass through its machine.\n\n'
                    'If source-routing is turned off, the hacker can use '
                    '"blind" hijacking, whereby it guesses the responses of '
                    'the two machines. Thus, the hacker can send a command, '
                    'but can never see the response. However, a common command '
                    'would be to set a password allowing access from somewhere '
                    'else on the net.\n\n'
                    'A hacker can also be "inline" between B and C using a '
                    'sniffing program to watch the conversation. This is known '
                    'as a "man-in-the-middle attack".',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'Session_hijacking'),)
    }),
)
