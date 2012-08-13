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

from umit.pm.gui.core import app
from umit.pm.core.logger import log
from umit.pm.core.bus import ServiceBus
from umit.pm.core.netconst import NL_TYPE_TCP, NL_TYPE_UDP

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.core.views import UmitView
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import AuditManager

_ = str
AUDIT_NAME = 'John'

class John(UmitView):
    icon_name = gtk.STOCK_INFO
    tab_position = gtk.POS_BOTTOM
    label_text = _('John The Ripper')
    name = 'John'


    def create_ui(self):

        # Toolbar
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        # Load Button/Action
        act = gtk.Action('hostlist', 
                         'hostlist', 
                         _('Load Captured Information'), 
                         gtk.STOCK_GO_DOWN)
        act.connect('activate', self.__on_load)
        self.toolbar.insert(act.create_tool_item(), -1)

        # Hash File Chooser
        act = gtk.Action('hashfiles', 
                         'hashfiles', 
                         _('Load A Hash File'), 
                         gtk.STOCK_OPEN)
        act.connect('activate', self.__on_choose)
        self.toolbar.insert(act.create_tool_item(), -1)
        self.hashfile = ''
 
        # Modes Checkbox
        self.modes_combo = gtk.combo_box_new_text()
        self.modes_combo.connect('changed', self.__on_mode_change)
        self.modes_item = self.create_toolbar_item(_("Mode:"), 
                                                   self.modes_combo)
        self.toolbar.insert(self.modes_item, -1) 

        # Format Checkbox
        self.format_combo = gtk.combo_box_new_text()
        self.format_item = self.create_toolbar_item(_("Format:"), 
                                                    self.format_combo)
        self.toolbar.insert(self.format_item, -1) 

        # Rules Check 
        self.rules_check = gtk.CheckButton()
        self.rules_check.set_active(False)
        self.rules_check.unset_flags(gtk.CAN_FOCUS)
        self.rules_item = self.create_toolbar_item(_("Use Rules"), 
                                                   self.rules_check)
        self.toolbar.insert(self.rules_item, -1) 

        # Incremental Mode Options Checkbox 
        self.inc_combo = gtk.combo_box_new_text()

        # External Mode Options Checkbox
        self.ext_combo = gtk.combo_box_new_text()

        # Wordlist Chooser
        self.wordlist_chooser = gtk.Action('wordlist', 'wordlist', 
                                           _('Choose wordlist file'), 
                                           gtk.STOCK_FILE)
        self.wordlist_chooser.connect('activate', self.__on_choose)
        self.wordlist_item = self.wordlist_chooser.create_tool_item()

              
        # Toolbar
        self._main_widget.pack_start(self.toolbar, False, False)

        # Scrolled Window
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # TreeView with ListStore
        self.store = gtk.ListStore(str, str, str, str, str)
        self.tree = gtk.TreeView(self.store)

        # TreeView Items
        username = gtk.TreeViewColumn('Username', gtk.CellRendererText(), text=0)
        username.set_resizable(True)
        self.tree.append_column(username)

        hash = gtk.TreeViewColumn('Hash', gtk.CellRendererText(), text=1)
        hash.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        hash.set_min_width(200)
        hash.set_resizable(True)
        self.tree.append_column(hash)

        ip = gtk.TreeViewColumn('IP', gtk.CellRendererText(), text=2)
        ip.set_resizable(True)
        self.tree.append_column(ip)

        mac = gtk.TreeViewColumn('MAC', gtk.CellRendererText(), text=3)
        proto = gtk.TreeViewColumn('PROTO', gtk.CellRendererText(), text=4)
        proto.set_resizable(True)
        self.tree.append_column(proto)

        result = gtk.TreeViewColumn('Result', gtk.CellRendererText(), text=5)
        result.set_resizable(True)
        self.tree.append_column(result)

        # Start Button / EXECUTE
        self.execute = gtk.ToggleToolButton(gtk.STOCK_EXECUTE)
        self.execute.set_tooltip_text(_('Start cracking'))
        self.execute.connect("toggled", self.__on_crack)
        self.toolbar.insert(self.execute, -1)

        # Add treeview to sw
        sw.add(self.tree)

        # John Progress Bar
        self.progressbar = gtk.ProgressBar()

        # John Output TextView
        self.textview = CommandTextView()

        bottom_vbox = gtk.VBox(False, 5)
        bottom_vbox.pack_start(self.progressbar, False, False, 2)
        bottom_vbox.pack_start(self.textview, False, False, 2)

        # Show all
        self._main_widget.pack_start(sw)
        self._main_widget.pack_end(bottom_vbox, False, False)
        self._main_widget.show_all()

        # before doing anything, parse john.conf and fill widgets
        self.parseConf()


    def create_toolbar_item(self, label, widget):
        
        item = gtk.ToolItem()

        lbl = gtk.Label(label)
        lbl.set_alignment(5, 0.5)

        hbox = gtk.HBox(False, 5)
        hbox.set_border_width(2)

        hbox.pack_start(lbl, False, False)
        hbox.pack_start(widget)

        item.add(hbox)

        return item


    def __on_load(self, action):

        log.warning('__on_load called')

        # Clean our store list
        self.store.clear()

        host_info = self.get_host_info()
        if host_info:
            for host in host_info:
                self.store.append(host)
        else:
            # No information found in hostlist
            warn_dialog = gtk.MessageDialog(
                          PMApp().main_window,
                          gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING,
                          gtk.BUTTONS_CLOSE, "No information found")
            warn_dialog.run()
            warn_dialog.destroy()


    def __on_choose(self, act):
        log.warning('__on_choose is called')

        if act.get_name() == 'wordlist':
            text = 'Select a wordlist file'
            flag = False
        else:
            text = 'Select a hash file'
            flag = True
            
        dialog = gtk.FileChooserDialog(
            _(text),
            PMApp().main_window,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT,
             gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            if flag:
                # TODO: It should get more than one file 
                # and combine them into one file.
                self.hashfile = dialog.get_filename()
                log.warning('self.hashfile is assigned')
                self.parseHashFile(self.hashfile)
            else:
                self.wordlist = dialog.get_filename()
                log.warning('self.wordlist is assigned')

        dialog.hide()
        dialog.destroy()


    def __on_mode_change(self, action):
        '''
            get mode type and add widgets to toolbar dynamically
        '''
        log.warning('__on_mode_change is called')
        index = self.modes_combo.get_active()
        modes = self.modes_combo.get_model()
        mode = modes[index][0]

        log.warning(mode)

        # remove existing object from the toolbar
        if self.widget_swap:
            log.warning('removing existing widget')
            self.toolbar.remove(self.widget_swap)

        # TODO: only wordlist object is working not combo items!
        if mode == 'incremental':
            log.warning('adding inc_item')
            self.widget_swap = self.inc_item
            self.toolbar.insert(self.widget_swap, 3)
        elif mode == 'wordlist':
            log.warning('adding wordlist_item')
            self.widget_swap = self.wordlist_item
            self.toolbar.insert(self.widget_swap, 3)
        elif mode == 'external':
            log.warning('adding external_item')
            self.widget_swap = self.ext_item
            self.toolbar.insert(self.widget_swap, 3)
        

    def __on_crack(self, action):
        log.warning("__on_crack")
        if not self.execute.get_active():
            self.execute.set_stock_id(gtk.STOCK_EXECUTE)
            self.execute.set_tooltip_text(_('Start cracking'))
            self.progressbar.set_fraction(0)
            self.textview.stop()
            return
        else:
            self.execute.set_stock_id(gtk.STOCK_STOP)
            self.execute.set_tooltip_text(_('Stop cracking'))
            self.execute.set_active(True)

        params = []
        manager = AuditManager()
        john = manager.get_configuration(AUDIT_NAME)['john_binary']
        params.append(john)

        # get mode
        index = self.modes_combo.get_active()
        modes = self.modes_combo.get_model()
        mode = modes[index][0]

        # default - single cracking mode 
        if index <= 0:
            log.warning("running single cracking mode ")
            params.append('--single')

        # wordlist mode
        elif mode == 'wordlist':
            log.warning("running wordlist cracking mode")
            if self.wordlist:
                params.append('--wordlist=' + self.wordlist)
            else:
                log.critical('Please choose a wordlist file!')
                return  

            # check if rules enabled
            rules = self.rules_check.get_active()
            if rules:
                log.warning("word mangling is enabled")
                params.append('--rules')

        # incremental mode
        elif mode == 'incremental':
            log.warning("running incremental cracking mode")
            pass
            #TODO: Here we should get mode name from the combobox
            # which will be generated when the incremental mode is 
            # selected

        # external mode
        elif mode == 'external':
            log.warning("running %s cracking mode" % self.modes_combo.get_active_text())
            pass
            #TODO: Here we should get mode name from the combobox
            # which will be generated when the incremental mode is 
            # selected

        # get format 
        format = self.format_combo.get_active_text()
        if format:
            log.warning("format : %s" % format)
            params.append(' --format=' + format)
        else:
            log.warning("format : default")

        # get hash filenames
        if self.hashfile:
            params.append(self.hashfile)
        else:
            log.critical("Please choose a hash file!")
            return

        # run john 
        log.info('running john with the following parameters : ')
        log.info(params)
        try:
            self.progressbar.pulse()
            self.textview.command = params
            self.textview.start()
            #process = subprocess.Popen(params, 
            #                           stdout=subprocess.PIPE, 
            #                           stderr=subprocess.PIPE)
            ##output = subprocess.check_output([john, params])
            ##output = process.communicate()
            #log.warning(output)
        except subprocess.CalledProcessError, e:
            print "John stdout output:\n", e.outp

    
    def parseHashFile(self, hash_file=None):
        '''
            Parses password hash file which consists of username:password
            fields. 
        '''
        self.hashlist = []

        # Try to open file
        try:
            hashfile = open(hash_file, 'r')
        except IOError, e:
            log.critical(e)
            # No information found in hostlist
            warn_dialog = gtk.MessageDialog(
                          PMApp().main_window,
                          gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING,
                          gtk.BUTTONS_CLOSE, "Couldn't open hash file")
            warn_dialog.run()
            warn_dialog.destroy()
            log.critical(e) # This could be printed from e
            return
        
        # Clean our store list
        self.store.clear()

        for line in hashfile:
            try:
                username, password = (line.split('\n'))[0].split(':')
                self.hashlist.append({username:password})
                self.store.append([username,password,'','',''])
            except Exception,e:
                log.critical(e)
                warn_dialog = gtk.MessageDialog(
                          PMApp().main_window,
                          gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING,
                          gtk.BUTTONS_CLOSE, "Hash File Parse Error!")
                warn_dialog.run()
                warn_dialog.destroy()
                log.critical(e)
                return

        hashfile.close()


    def parseConf(self):
        '''
            Parses john configuration file which is given with config_file
            parameter.
        '''

        #TODO: enable config file assignment with a parameter
        manager = AuditManager()
        config_file = manager.get_configuration(AUDIT_NAME)['config_file']
        log.warning(config_file)

        # Try to open file
        try:
            conf = open(config_file, 'r')
            all = conf.read()
            conf.close()
        except IOError, e:
            log.warning(e)
            #TODO: This could be extracted from exception
            log.warning('John Config File Error.') 
            return

        # ALL MODES
        mode_lst = manager.get_configuration(AUDIT_NAME)['modes'].split()
        for mode in mode_lst:
            self.modes_combo.append_text(mode)

        '''
            Parsing the conf file with regex and filling the combo boxes
        '''

        self.widget_swap = None

        # INCREMENTAL MODE OPTIONS
        p = re.compile('\[Incremental\:(.*?)\]')
        inc_opts = re.findall(p, all)

        for inc in inc_opts:
            self.inc_combo.append_text(inc)

        self.inc_item = self.create_toolbar_item(_("options:"), self.inc_combo)

        log.warning('Incremental Options')
        log.warning(inc_opts)

        # EXTERNAL MODE OPTIONS 
        p = re.compile('\[List\.External\:(.*?)\]')
        ext_opts = re.findall(p, all)

        for ext in ext_opts:
            self.ext_combo.append_text(ext)

        self.ext_item = self.create_toolbar_item(_("options:"), self.ext_combo)

        log.warning('External Options')
        log.warning(ext_opts)

        # HASH FORMAT OPTIONS
        # TODO: Find a way to get supported hash types
        format_lst = manager.get_configuration(AUDIT_NAME)['hash_formats'].split()
        for format in format_lst:
            self.format_combo.append_text(format)


    def get_host_info(self):
        # should we change the definition of pm.hostlist service 
        # callbacks : info and populate, intf looks unnecessary

        #TODO: Get interface automatically! or never use??
        intf = ""
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


class CommandTextView(gtk.TextView):
        command = None
        def __init__(self,command=None):
            super(CommandTextView,self).__init__()

            self.command = command

        def start(self):
            if self.command:
                self.proc = subprocess.Popen(self.command,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                gobject.io_add_watch(self.proc.stdout,
                                  gobject.IO_IN,
                                  self.write_to_buffer)
            else:
                log.critical("Subprocess command is not assigned\n")

        def stop(self):
            log.warning("sorry killing the process\n")
            #self.proc.kill()

        def write_to_buffer(self, fd, condition):
            data = fd.recv(12)
            print len(data)
            if len(data) > 0:
                return True #run forever
            else:
                gobject.io_add_watch(fd, gobject.IO_IN, self.write_to_buffer)
                log.info('gobject stop looping.')
                return False # stop looping

            #if condition == gobject.IO_IN:
            #    char = fd.read(12)
            #    buf = self.get_buffer()
            #    buf.insert_at_cursor(char)
            #    return True
            #else:
            #    return False


class JohnPlugin(Plugin):
    def start(self, reader):
        self.john_tab = John()
        PMApp().main_window.register_tab(self.john_tab, True)

    def stop(self):
        PMApp().main_window.deregister_tab(self.john_tab)



__plugins__ = [JohnPlugin]

__plugins_deps__ = [(AUDIT_NAME, ['Profiler'], [], [])]

__audit_type__ = 1
__protocols__ = (('tcp', None),)

__configurations__ = ((AUDIT_NAME, {
     'config_file' : ['/etc/john/john.conf', 
                      'john configuration file'],
     'john_binary' : ['/usr/sbin/john', 
                      'john binary full path'],
     'hash_formats': ['default DES BSDI MD5 BF AFS LM crypt',
                      'password hash formats'],
     'modes':        ['single wordlist incremental external', 
                      'running mode options']
    }),
)

__vulnerabilities__ = (('John The Ripper', {
    'description' : 'John the Ripper is a fast password cracker, currently '
                    'available for many flavors of Unix, Windows, DOS, BeOS'
                    ', and OpenVMS. Its primary purpose is to detect weak '
                    'Unix passwords. Besides several crypt(3) password hash '
                    'types most commonly found on various Unix systems, '
                    'supported out of the box are Windows LM hashes, plus '
                    'lots of other hashes and ciphers in the community-en'
                    'hanced version. ',
    'references' : ((None, 'http://www.openwall.com/john/'
                            'Password_Cracking'),)
    }),
)

