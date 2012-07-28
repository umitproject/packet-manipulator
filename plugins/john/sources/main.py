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
import re

import gtk
import gobject
import subprocess

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

    def create_ui(self):

        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        # Wordlist Chooser
        # TODO: Create this widget when wordlist mode is chosen! TODO #
        act = gtk.Action('wordlist', 'wordlist', '', gtk.STOCK_OPEN)
        act.connect('activate', self.__on_choose)
        self.toolbar.insert(act.create_tool_item(), -1)
        self.wordlist = ''


        # John the Ripper logo
        # Only for testing, I may put it somewhere
        #self.logo = gtk.Image()
        #self.logo.set_from_file("/home/serdar/Desktop/john2.png")

        self.modes_combo = gtk.combo_box_new_text()
        self.format_combo = gtk.combo_box_new_text()
        self.rules_check = gtk.CheckButton("rules")
        self.rules_check.set_active(False)
        self.rules_check.unset_flags(gtk.CAN_FOCUS)

        for label, widget in zip( (_("Mode:"), _("Format:"), _("")),
                                  (self.modes_combo, self.format_combo, 
                                   self.rules_check) ):

            item = gtk.ToolItem()

            lbl = gtk.Label(label)
            lbl.set_alignment(0, 0.5)

            hbox = gtk.HBox(False, 2)
            hbox.set_border_width(2)


            hbox.pack_start(lbl, False, False)
            hbox.pack_start(widget)

            item.add(hbox)

            self.toolbar.insert(item, -1) 

        # Hash File Chooser
        act = gtk.Action('hashfiles', 'hashfiles', '', gtk.STOCK_FILE)
        act.connect('activate', self.__on_choose)
        self.toolbar.insert(act.create_tool_item(), -1)
        self.hashfiles = ''
       
        # Load Button
        act = gtk.Action(None, None, _('Load Captured Information'), gtk.STOCK_GO_DOWN)
        act.connect('activate', self.__on_load)
        self.toolbar.insert(act.create_tool_item(), -1)

        # Start Button / Play
        act = gtk.Action(None, None, _('Start cracking'), gtk.STOCK_EXECUTE)
        act.connect('activate', self.__on_crack)
        self.toolbar.insert(act.create_tool_item(), -1)

        # Toolbar
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

        # TreeView Items
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

        # Useless Menubar for showing output
        #self.menubar = gtk.MenuBar()
        #menu = gtk.Menu()
        #john_item = gtk.MenuItem('John Output:')
        #self.menubar.append(john_item) 

        # John Output TextView
        self.text = gtk.TextView()
        self.text.set_wrap_mode(gtk.WRAP_WORD)

        # John Output Scrolled Window
        john_sw = gtk.ScrolledWindow()
        john_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        john_sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        john_sw.add(self.text)

        # Adding sw's to vertical box
        main_vbox = gtk.VBox(False, 15)
        main_vbox.pack_start(sw)
        #main_vbox.pack_start(self.menubar)
        main_vbox.pack_start(john_sw)

        # Add sw and show all
        self._main_widget.pack_start(main_vbox)

        #self._main_widget.pack_start(self.john_status)
        self._main_widget.show_all()

        # parse john.conf and fill widgets
        self.parseConf()


    def __on_load(self, action):

        log.warning('__on_load called')
        
        # Clean our store list
        self.store.clear()

        host_info = self.get_host_info()
        if host_info:
            for host in host_info:
                self.store.append(host)
        else:
            self.store.append(['No','useful','data','found','',''])


    def __on_choose(self, act):
        log.warning('__on_choose is called')

        if act.get_name() == 'wordlist':
            text = 'Select a wordlist file'
        else:
            text = 'Select hash file/s'
            multiple = True
            
        dialog = gtk.FileChooserDialog(
            _(text),
            PMApp().main_window,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT,
             gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        dialog.set_select_multiple(multiple)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            if multiple:
                self.hashfiles = dialog.get_filenames()
                log.warning('self.hashfiles is assigned')
            else:
                self.wordlist = dialog.get_filename()
                log.warning('self.wordlist is assigned')

        dialog.hide()
        dialog.destroy()


    def __on_crack(self, action):

        log.warning("\n__on_crack called")

        #TODO: get john executable path automatically :TODO#
        john = 'john'
        params = ''
        # get mode
        index = self.modes_combo.get_active()
        modes = self.modes_combo.get_model()
        mode = modes[index]

        # default - single cracking mode 
        if index <= 0:
            log.warning("running single cracking mode ")
            params += ' --single '

        # wordlist mode
        elif mode == 'wordlist':
            log.warning("running wordlist cracking mode")
            if self.wordlist:
                params += ' --wordlist=' + self.wordlist
            else:
                log.critical('Please choose a wordlist file!')
                return  

            # check if rules enabled
            rules = self.rules_check.get_active()
            if rules:
                log.warning("word mangling is enabled")
                params += ' --rules '

        # incremental mode
        elif mode == 'incremental':
            log.warning("running incremental cracking mode")
            pass
            #TODO: Here we should get mode name from the combobox
            # which will be generated when the incremental mode is 
            # selected

        # external mode
        elif mode == 'external':
            log.warning("running %s cracking mode" % self.modes_combo.get_acti)
            pass
            #TODO: Here we should get mode name from the combobox
            # which will be generated when the incremental mode is 
            # selected

        # get format 
        format = self.format_combo.get_active_text()
        if format:
            log.warning("format : %s" % format)
            params += ' --format=' + format + ' '
        else:
            log.warning("format : default")

        # get hash filenames
        log.warning(self.hashfiles)
        if self.hashfiles:
            log.warning("hash files are chosen")
            for hash in self.hashfiles:
                params += ' ' + hash 
        else:
            log.critical("Please choose a hash file!")
            return

        # run john 
        log.warning('running john with the follwing parameters : ')
        log.warning(params)
        process = subprocess.Popen(['john', params], 
                                   shell=False, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)

        log.warning(process.communicate())
            
       
    def parseConf(self, config_file='/etc/john/john.conf'):
        '''
            Parses john configuration file which is given with config_file
            parameter.
        '''
        # Try to open file
        try:
            conf = open(config_file, 'r')
            all = conf.read()
            conf.close()
        except IOError, e:
            log.warning(e)
            log.warning('Input Output Error.') # This could be printed from e
            return

        # ALL MODES
        mode_lst = ['single', 'incremental', 'external']
        for mode in mode_lst:
            self.modes_combo.append_text(mode)

        # Parse the text with regex and fill combo boxes

        # INCREMENTAL MODE OPTIONS
        log.warning('\nParsing incremental mode options:')
        p = re.compile('\[Incremental\:(.*?)\]')
        res = set(re.findall(p, all))
        if res:
            # fill the incremental mode combobox
            for inc in res:
                #self.inc_combo.append_text(format)
                log.warning(inc)
                
        
        # EXTERNAL MODE OPTIONS 
        log.warning("\nParsing external mode options:")
        p = re.compile('\[List\.External\:(.*?)\]')
        res = set(re.findall(p, all))
        if res:                                           
            # fill the external mode combobox
            for ext in res:
                #self.rules_combo.append_text(rule)
                log.warning(ext)


        # HASH FORMAT OPTIONS
        # TODO: Find a way to get supported hash types TODO #
        format_lst = ['default','DES','BSDI','MD5','BF','AFS','LM','crypt']
        for format in format_lst:
            self.format_combo.append_text(format)


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



class JohnPlugin(Plugin):
    def start(self, reader):
        self.john_tab = John()
        PMApp().main_window.register_tab(self.john_tab, True)

    def stop(self):
        PMApp().main_window.deregister_tab(self.john_tab)

__plugins__ = [JohnPlugin]
