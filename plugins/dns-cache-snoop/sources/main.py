#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2010 Adriano Monteiro Marques
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

import time
import socket

from random import randint
from threading import Thread

from umit.pm.core.logger import log
from umit.pm.core.atoms import generate_traceback

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.core.views import UmitView
from umit.pm.gui.plugins.engine import Plugin

from umit.pm.backend import MetaPacket

_ = lambda x: x

class SnoopTab(UmitView):
    icon_name = gtk.STOCK_INFO
    tab_position = gtk.POS_LEFT
    label_text = _('DNS Cache snoop')
    name = 'DNSCacheSnoop'

    def create_ui(self):
        self.active = False
        self.output = []

        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        self.toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)

        for name, stock, cb in (
                ('Copy', gtk.STOCK_COPY, self.__on_copy),
                ('Open', gtk.STOCK_OPEN, self.__on_open),
                ('Execute', gtk.STOCK_EXECUTE, self.__on_execute)):

            act = gtk.Action(name, name, '', stock)
            act.connect('activate', cb)

            self.toolbar.insert(act.create_tool_item(), -1)

        self._main_widget.pack_start(self.toolbar, False, False)

        self.server = gtk.Entry()
        self._main_widget.pack_start(self.server, False, False)

        self.store = gtk.ListStore(bool, str, int)
        self.tree = gtk.TreeView(self.store)

        self.tree.append_column(
            gtk.TreeViewColumn('', gtk.CellRendererToggle(), active=0))

        rend = gtk.CellRendererText()
        rend.connect('edited', self.__edited_cb)
        rend.set_property('editable', True)

        col = gtk.TreeViewColumn('Host', rend, text=1)
        col.set_expand(True)

        self.tree.append_column(col)

        self.tree.append_column(
            gtk.TreeViewColumn('TTL', gtk.CellRendererText(), text=2))

        self.tree.set_rules_hint(True)

        self.selection = self.tree.get_selection()

        self.menu = gtk.Menu()

        for name, stock, cb in (('Add', gtk.STOCK_ADD, self.__on_add),
                                ('Remove', gtk.STOCK_REMOVE, self.__on_remove)):
            act = gtk.Action(name, name, '', stock)
            act.connect('activate', cb)
            self.menu.append(act.create_menu_item())

        self.tree.connect('button-press-event', self.__on_button)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.tree)

        self._main_widget.pack_start(sw)
        self._main_widget.show_all()

    def __edited_cb(self, rend, path, new_text):
        iter = self.store.get_iter_from_string(path)
        self.store.set_value(iter, 1, new_text)

    def __on_button(self, tree, evt):
        if evt.button != 3:
            return False

        self.menu.show_all()
        self.menu.popup(None, None, None, evt.button, evt.time)

        return True

    def __on_add(self, widget):
        model, iter = self.selection.get_selected()
        newrow = (False, 'edit me', 0)

        if not iter:
            self.store.append(newrow)
        else:
            self.store.insert_after(None, iter, newrow)

    def __on_remove(self, widget):
        model, iter = self.selection.get_selected()

        if iter:
            self.store.remove(iter)

    def __on_copy(self, act):
        out = ''

        for row in self.store:
            out += "[%s] %s (%d)\n" % (row[0] and '+' or '-',
                                       row[1], row[2])

        if out:
            clip = gtk.clipboard_get()
            clip.set_text(
                'Result for %s DNS server\n' % self.server.get_text() + out
            )

    def __on_execute(self, act):
        if self.active:
            return

        self.active = True
        self.thread = None
        self.tree.set_sensitive(False)
        self.server.set_sensitive(False)
        self.toolbar.set_sensitive(False)

        server = self.server.get_text()
        targets = [row[1] for row in self.store]

        self.thread = Thread(target=self.__main_thread,
                             name='DNSCacheSnoop',
                             kwargs={'targets' : targets, 'server' : server})
        self.thread.setDaemon(True)
        self.thread.start()

        gobject.timeout_add(1000, self.__check_finished)

    def __check_finished(self):
        if self.thread is not None:
            return True

        log.debug(str(self.output))

        idx = 0
        while idx < len(self.output):
            present, ttl = self.output[idx]

            iter = self.store.get_iter((idx, ))

            if iter:
                self.store.set(iter, 0, present, 2, ttl)

            idx += 1

        self.output = []

        self.tree.set_sensitive(True)
        self.server.set_sensitive(True)
        self.toolbar.set_sensitive(True)

        self.active = False

        return False

    def __on_open(self, act):
        dialog = gtk.FileChooserDialog(
            _('Select a query file'),
            PMApp().main_window,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT,
             gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            fname = dialog.get_filename()

            if fname:
                fd = open(fname, 'r')
                contents = fd.read()
                fd.close()

                self.store.clear()

                for line in contents.splitlines():
                    line = line.strip()

                    if line:
                        self.store.append((False, line, 0))

        dialog.hide()
        dialog.destroy()

    def __main_thread(self, server, targets):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)

        if ':' in server:
            server, port = server.split(':', 1)
        else:
            port = 53

        try:
            port = int(port)
        except:
            port = 53

        sock.connect((server, port))

        for target in targets:
            dnsqr = MetaPacket.new('dnsqr')
            dnsqr.set_field('dnsqr.qname', target)

            mpkt = MetaPacket.new('dns')
            mpkt.set_fields('dns', {
                'id' : randint(0, 2L**16-1),
                'qd' : dnsqr})

            sock.send(mpkt.get_raw())

            try:
                buff = sock.recv(1024)
                mpkt = MetaPacket.new_from_str('dns', buff)

                if mpkt.get_field('dns.ancount', 0) == 0:
                    self.output.append((False, 0))
                else:
                    found = False
                    qd = mpkt.get_field('dns.an', None)

                    while qd is not None:
                        rrname = qd.get_field('dnsrr.rrname', '')

                        if rrname.startswith(target):
                            self.output.append((True, \
                                                qd.get_field('dnsrr.ttl', 0)))
                            log.debug('Reply for %s' % target)
                            found = True
                            break

                        qd = mpkt.get_field('dnsrr.payload', None)

                    if not found:
                        self.output.append((False, 0))
                        log.debug('No reply for %s' % target)
            except Exception, exc:
                log.debug('Cannot parse DNS reply for %s ' \
                          'or timeout occurred' % target)
                log.error(generate_traceback())

                self.output.append((False, 0))

            time.sleep(0.1)

        sock.close()
        self.thread = None

class CacheSnoop(Plugin):
    def start(self, reader):
        self.snoop_tab = SnoopTab()
        PMApp().main_window.register_tab(self.snoop_tab, True)

    def stop(self):
        PMApp().main_window.deregister_tab(self.snoop_tab)

__plugins__ = [CacheSnoop]
