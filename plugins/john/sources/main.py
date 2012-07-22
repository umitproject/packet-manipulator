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

import sys, os, os.path

import gtk
import gobject

from umit.pm.backend import StaticContext

from umit.pm.core.bus import ServiceBus
from umit.pm.core.netconst import *
from umit.pm.core.logger import log

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.gui.sessions.base import Session
from umit.pm.gui.sessions import SessionType
from umit.pm.gui.pages.base import Perspective


_ = str

class John(Perspective):
    # icon = gtk.STOCK_INFO
    title = _('John')

    def create_ui(self):
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        # Fill combo boxes with parsed information from John.conf

        # Mode Combo
        mode_lst = ['single', 'incremental', 'external']
        self.mode_combo = gtk.combo_box_new_text()
        for iter in mode_lst:
            self.mode_combo.append_text(iter)

        # Format Combo
        format_lst = ['raw-md5', 'des', 'sha1']
        self.format_combo = gtk.combo_box_new_text()
        for iter in format_lst:
            self.format_combo.append_text(iter)

        # Rules Combo
        rules_lst = ['LinkedIN', 'myRules']
        self.rules_combo = gtk.combo_box_new_text()
        for iter in rules_lst:
            self.rules_combo.append_text(iter)


        for label, widget in zip((_("Mode:"), _("Rules:")),
                                 (self.mode_combo, self.rules_combo)):

            item = gtk.ToolItem()

            lbl = gtk.Label(label)
            lbl.set_alignment(0, 0.5)

            hbox = gtk.HBox(False, 2)
            hbox.set_border_width(2)

            hbox.pack_start(lbl, False, False)
            hbox.pack_start(widget)

            item.add(hbox)

            self.toolbar.insert(item, -1) 

        # Start Button / Play
        act = gtk.Action(None, None, _('Start cracking'), gtk.STOCK_MEDIA_PLAY)
        act.connect('activate', self.__on_crack)
        self.toolbar.insert(act.create_tool_item(), -1)

        # Add toolbar
        self.pack_start(self.toolbar, False, False)

        # Scrolled Window
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # TreeView with ListStore
        self.store = gtk.ListStore(str, str, str)
        self.tree = gtk.TreeView(self.store)

        self.tree.append_column(gtk.TreeViewColumn('USERNAME', 
                                                   gtk.CellRendererText(),
                                                   text=0))
        self.tree.append_column(gtk.TreeViewColumn('HWPASSWORD', 
                                                   gtk.CellRendererText(),
                                                   text=1))
        self.tree.append_column(gtk.TreeViewColumn('IP', 
                                                   gtk.CellRendererText(),
                                                   text=2))
        self.tree.append_column(gtk.TreeViewColumn('MAC',
                                                   gtk.CellRendererText(),
                                                   text=3))
        self.tree.append_column(gtk.TreeViewColumn('PROTO',
                                                   gtk.CellRendererText(),
                                                   text=4))
        sw.add(self.tree)

        # Add and show all
        self.pack_start(sw)
        self.show_all()

        # Register the lock/unlock callback
        self.session.context.lock_callback = \
            lambda: self.toolbar.set_sensitive(False)
        self.session.context.unlock_callback = \
            lambda: self.toolbar.set_sensitive(True)


    def __on_crack(self, action):

        log.warning('__on_crack called')
        
        # Let's disable the toolbar
        #self.session.context.lock()

        # Clean our store list
        self.store.clear()

        host_info = self.get_host_info()
        for host in host_info:
            self.store.append(host)

        #self.crack()


    def get_host_info(self):
        # should we change the definition of pm.hostlist service 
        # callbacks : info and populate, intf looks unnecessary

        intf = "wlan0"
        host_list = []
        populate_cb = ServiceBus().get_function('pm.hostlist', 'populate')
        info_cb = ServiceBus().get_function('pm.hostlist', 'info')

        if not callable(populate_cb) or not callable(info_cb):
            log.warning('returning due to uncallable methods')
            return

        for ip, mac, desc in populate_cb(intf):
            host = []
            prof = info_cb(intf, ip, mac)

            if not prof:
                log.warning('no profile found')
                continue

            # Add field checks here 
            for port in prof.ports:
                for account in port.accounts:
                    if account.password:
                        host.append(password)
                        host.append(username)
                        host.append(ip)
                        host.append(mac)
                        if port.proto == NL_TYPE_TCP:
                            proto = 'TCP'
                        elif port.proto == NL_TYPE_UDP:
                            proto = 'UDP'
                        else:
                            proto = port.proto and str(port.proto) or ''
                        host.append(proto)
                        host_list.append(host)
                        log.warning('new host added')
            
        return host_list


    def crack(self):
        log.warning("In crack")
        import time
        time.sleep(3)

        # pseudo cracking
        # assume that we have a cracked data
        self.session.context.set_crack(cracked_data)
        gobject.idle_add(self.session.reload)

        # Let's enable the toolbar
        #self.session.context.unlock()

    
    def populate(self):
        log.warning("In populate")
        
        
        out = self.session.context.data

        log.warning(out)

        if out is None:
            return

        self.store.clear()
        
        self.store.append(out[0])


class JohnContext(StaticContext):
    def __init__(self, fname=None):
        StaticContext.__init__(self, 'John', fname)
        self.status = self.SAVED

        self.lock_callback = None
        self.unlock_callback = None

    def set_crack(self, output):
        self.set_data([output])

    def lock(self):
        if callable(self.lock_callback):
            self.lock_callback()

    def unlock(self):
        if callable(self.unlock_callback):
            self.unlock_callback()


class JohnSession(Session):
    session_name = "JOHN"
    session_menu = "John"

    def create_ui(self):
        self.crack_page = self.add_perspective(John, True, True)

        self.editor_cbs.append(self.reload_editor)
        self.container_cbs.append(self.reload_container)

        super(JohnSession, self).create_ui()

    def reload_editor(self):
        #self.crack_page.__on_crack()
        log.warning('JOHN - reload_editor is called')

    def reload_container(self, packet=None):
        self.crack_page.populate()
        log.warning('JOHN - reload_container is called')


class JohnPlugin(Plugin):
    def start(self, reader):
        if reader:
            catalog = reader.bind_translation("john")

            if catalog:
                global _
                _ = catalog.gettext

        id = PMApp().main_window.register_session(JohnSession, JohnContext)
        log.debug("John session binded with id %d" % id)

    def stop(self):
        PMApp().main_window.deregister_session(JohnSession)

__plugins__ = [JohnPlugin]
