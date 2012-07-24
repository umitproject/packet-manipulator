#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
#
# Author: Serdar Yigit <syigitisk@gmail.com>
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

from time import sleep

from umit.pm.core.logger import log
from umit.pm.core.bus import ServiceBus
from umit.pm.core.netconst import NL_TYPE_TCP, NL_TYPE_UDP

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.core.views import UmitView
from umit.pm.gui.plugins.engine import Plugin


_ = str

class John(UmitView):
    icon_name = gtk.STOCK_INFO
    tab_position = gtk.POS_LEFT
    label_text = _('John The Ripper')
    name = 'John'

    def delete(self):
        pass

    def create_ui(self):

        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        # Open Wordlist        
        act = gtk.Action('Wordlist', 'Wordlist', _('Open'), gtk.STOCK_OPEN)
        act.connect('activate', self.__on_open)
        self.toolbar.insert(act.create_tool_item(), -1)

        # John the Ripper logo
        # Only for testing, may be I'll put it somewhere
        self.logo = gtk.Image()
        self.logo.set_from_file("/home/serdar/Desktop/john2.png")

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


        for label, widget in zip((_(""), _("Mode:"), _("Format:"), _("Rules:")),
                                 (self.logo, self.mode_combo, self.format_combo, 
                                  self.rules_combo)):

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
        self._main_widget.pack_start(self.toolbar, False, False)

        # Scrolled Window
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # TreeView with ListStore
        self.store = gtk.ListStore(str, str, str, str, str)
        self.tree = gtk.TreeView(self.store)

        username = gtk.TreeViewColumn('Username', gtk.CellRendererText(), text=0)
        username.set_resizable(True)
        self.tree.append_column(username)

        hash = gtk.TreeViewColumn('Hash', gtk.CellRendererText(), text=1)
        hash.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        #hash.set_fixed_width(200)
        hash.set_min_width(200)
        hash.set_resizable(True)
        self.tree.append_column(hash)

        ip = gtk.TreeViewColumn('IP', gtk.CellRendererText(), text=2)
        ip.set_resizable(True)
        self.tree.append_column(ip)

        mac = gtk.TreeViewColumn('MAC', gtk.CellRendererText(), text=3)
        mac.set_resizable(True)
        self.tree.append_column(mac)

        proto = gtk.TreeViewColumn('PROTO', gtk.CellRendererText(), text=4)
        proto.set_resizable(True)
        self.tree.append_column(proto)

        result = gtk.TreeViewColumn('Result', gtk.CellRendererText(), text=4)
        result.set_resizable(True)
        self.tree.append_column(result)

        sw.add(self.tree)

        # Add sw and show all
        self._main_widget.pack_start(sw)
        self._main_widget.show_all()


    def __on_crack(self, action):

        log.warning('__on_crack called')
        
        # Clean our store list
        self.store.clear()

        host_info = self.get_host_info()
        for host in host_info:
            self.store.append(host)


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
                        host.append(account.username)
                        host.append(account.password)
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


    def __on_open(self, act):
        '''
            a stupid function for testing wordlist file.
        '''

        # TODO: choose and load wordlist files of user for 
        # using as a  parameter to john

        # TEST CODE!

        dialog = gtk.FileChooserDialog(
            _('Select a wordlist file'),
            PMApp().main_window,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT,
             gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            fname = dialog.get_filename()

            if fname:
                fd = open(fname, 'r')
                self.wordlist_contents = fd.read()
                fd.close()

                for line in self.wordlist_contents.splitlines():
                    line = line.strip()

                    if line:
                        log.warning(line)

        dialog.hide()
        dialog.destroy()


    def crack(self):
        log.warning("In crack")
        sleep(3)

        # pseudo cracking
        # assume that we have a cracked data
 
    def populate(self):
        log.warning("In populate")
        
        result = self.session.context.data
        
        if result is None:
            return

        log.warning(result)
        self.store.clear()

        for res in result[0]:
            self.store.append(res)


class JohnPlugin(Plugin):
    def start(self, reader):
        self.john_tab = John()
        PMApp().main_window.register_tab(self.john_tab, True)

    def stop(self):
        PMApp().main_window.deregister_tab(self.john_tab)

__plugins__ = [JohnPlugin]
