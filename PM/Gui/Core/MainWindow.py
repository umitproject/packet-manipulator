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

"""
This module contains the MainWindow class
"""

import gtk
import os

from PM import Backend
from PM.Manager.PreferenceManager import Prefs

if Prefs()['gui.docking'].value:
    try:
        from Paned import *
    except ImportError:
        print "moo not installed. Using fallback UmitPaned .."

        Prefs()['gui.docking'].value = False

        from FallbackPaned import *
else:
    from FallbackPaned import *

from PM.Gui.Tabs.VteTab import VteTab
from PM.Gui.Tabs.MainTab import MainTab
from PM.Gui.Tabs.HackTab import HackTab
from PM.Gui.Tabs.StatusTab import StatusTab
from PM.Gui.Tabs.ConsoleTab import ConsoleTab
from PM.Gui.Tabs.PropertyTab import PropertyTab
from PM.Gui.Tabs.OperationsTab import OperationsTab, SniffOperation
from PM.Gui.Tabs.ProtocolSelectorTab import ProtocolSelectorTab

from PM.Gui.Dialogs.Interface import InterfaceDialog
from PM.Gui.Dialogs.Preferences import PreferenceDialog
from PM.Gui.Dialogs.Routes import RoutesDialog

from PM.Core.I18N import _
from PM.Core.Const import PIXMAPS_DIR, PM_VERSION, PM_DEVELOPMENT

class MainWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_title("Packet Manipulator")
        self.set_icon_from_file(os.path.join(PIXMAPS_DIR, 'pm-logo.png'))
        self.set_size_request(600, 400)
        
        self.registered_tabs = {}

        self.__create_widgets()
        self.__pack_widgets()
        self.__connect_signals()

        self.show_all()

    def __create_widgets(self):
        "Create widgets"

        self.main_actions = [
            ('File', None, _('File'), None),
            ('Open', gtk.STOCK_OPEN, _('_Open'), '<Control>o', _('Open pcap file'), self.__on_open_pcap),
            ('Quit', gtk.STOCK_QUIT, _('_Quit'), '<Control>q', _('Quit from application'), self.__on_quit),
            
            ('Capture', None, _('Capture'), None),
            ('Interface', gtk.STOCK_CONNECT, _('_Interface'), '<Control>i', _('Capture from interface'), self.__on_select_iface),

            ('Options', None, _('Options'), None),
            ('Routes', gtk.STOCK_NETWORK, _('Routing table'), '<Control>r', _('Routes editor'), self.__on_routing),
            ('Preferences', gtk.STOCK_PREFERENCES, _('_Preferences'), '<Control>p', _('Preferences'), self.__on_preferences),

            ('Views', None, _('Views'), None),

            ('Help', None, _('Help'), None),
            ('About', gtk.STOCK_ABOUT, _('About'), None, None, self.__on_about),
        ]

        self.default_ui = """<menubar>
            <menu action='File'>
                <menuitem action='Open'/>
                <separator/>
                <menuitem action='Quit'/>
            </menu>
            <menu action='Capture'>
                <menuitem action='Interface'/>
            </menu>
            <menu action='Options'>
                <menuitem action='Routes'/>
                <separator/>
                <menuitem action='Preferences'/>
            </menu>
            <menu action='Views'/>
            <menu action='Help'>
                <menuitem action='About'/>
            </menu>
            </menubar>

            <toolbar>
                <toolitem action='Open'/>
                <toolitem action='Interface'/>
                <separator/>
                <toolitem action='Routes'/>
                <toolitem action='Preferences'/>
                <separator/>
            </toolbar>
            """

        self.ui_manager = gtk.UIManager()

        self.main_accel_group = gtk.AccelGroup()
        self.main_action_group = gtk.ActionGroup('MainActionGroup')
        self.main_action_group.add_actions(self.main_actions)
        
        self.add_accel_group(self.main_accel_group)

        for action in self.main_action_group.list_actions():
            action.set_accel_group(self.main_accel_group)
            action.connect_accelerator()

        self.ui_manager.insert_action_group(self.main_action_group, 0)
        self.ui_manager.add_ui_from_string(self.default_ui)

        # Central widgets
        self.main_paned = UmitPaned()

        self.vbox = gtk.VBox(False, 2)

    def get_tab(self, name):
        """
        Get a tab from its name

        @param name the name of the tab
        """

        return self.registered_tabs[name]

    def register_tab(self, tab, show=True):
        """
        Register a tab

        @param tab the Tab object
        @param show if the Tab should be showed
        """

        item = self.ui_manager.get_widget('/menubar/Views')
        menu = item.get_submenu()

        item.show()

        if not menu:
            menu = gtk.Menu()
            item.set_submenu(menu)

        if tab.label_text in self.registered_tabs:
            raise Exception("Tab already present")

        # Ok we should add a CheckMenuItem to this fucking menu
        self.registered_tabs[tab.name] = tab

        print "Tab %s registered as %s" % (tab.label_text, tab.name)

        if not tab.tab_position:
            # This is the central widget so it should be added
            # with no MenuItem
            self.main_paned.add_view(tab)
            return

        new_item = gtk.CheckMenuItem(tab.label_text)
        new_item.connect('toggled', self.__on_toggle_tab_menu, tab)

        if show:
            new_item.set_active(True)

        new_item.show()
        menu.append(new_item)

    def __pack_widgets(self):
        "Pack widgets"

        self.menubar = self.ui_manager.get_widget("/menubar")
        self.vbox.pack_start(self.menubar, False, False, 0)

        self.toolbar = self.ui_manager.get_widget("/toolbar")
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        self.vbox.pack_start(self.toolbar, False, False, 0)

        item = self.ui_manager.get_widget('/menubar/Views')
        item.remove_submenu()
        
        self.vbox.pack_start(self.main_paned)

        # Tabs
        self.register_tab(MainTab())

        self.register_tab(ProtocolSelectorTab(),
                          Prefs()['gui.views.protocol_selector_tab'].value)
        self.register_tab(PropertyTab(),
                          Prefs()['gui.views.property_tab'].value)
        self.register_tab(StatusTab(),
                          Prefs()['gui.views.status_tab'].value)
        self.register_tab(OperationsTab(),
                          Prefs()['gui.views.operations_tab'].value)
        self.register_tab(VteTab(),
                          Prefs()['gui.views.vte_tab'].value)
        self.register_tab(HackTab(),
                          Prefs()['gui.views.hack_tab'].value)
        self.register_tab(ConsoleTab(),
                          Prefs()['gui.views.console_tab'].value)

        self.add(self.vbox)

    def __connect_signals(self):
        "Connect signals"
        self.connect('delete-event', self.__on_quit)

    def connect_tabs_signals(self):
        "Used to connect signals between tabs"

        for key, tab in self.registered_tabs.items():
            tab.connect_tab_signals()

    def __on_toggle_tab_menu(self, menuitem, tab):
        if menuitem.get_active():
            self.main_paned.add_view(tab)
        else:
            self.main_paned.remove_view(tab)

    def __on_routing(self, action):
        dialog = RoutesDialog(self)
        dialog.run()
        dialog.hide()
        dialog.destroy()

    def __on_preferences(self, action):
        dialog = PreferenceDialog(self)
        dialog.show()

    def __on_about(self, action):
        dialog = gtk.AboutDialog()

        dialog.set_logo(gtk.gdk.pixbuf_new_from_file(os.path.join(PIXMAPS_DIR, 'pm-logo.png')))

        dialog.set_version(PM_VERSION)
        dialog.set_comments(_("Packet manipulation made easy%s") % \
                            ((PM_DEVELOPMENT) and (' (development snapshot)') or ('')))
        dialog.set_authors(['Francesco Piccinno <stack.box@gmail.com>'])
        dialog.set_license(_('This program is relased under the terms of GPLv2'))
        dialog.set_website_label('http://trac.umitproject.org/wiki/PacketManipulator/FrontEnd')

        dialog.run()
        dialog.hide()
        dialog.destroy()

    def __on_select_iface(self, action):
        dialog = InterfaceDialog(self)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            iface = dialog.get_selected()
            args = dialog.get_options()

            if iface:
                tab = self.get_tab("OperationsTab")
                tab.tree.append_operation(SniffOperation(iface, **args))

        dialog.hide()
        dialog.destroy()

    def __on_open_pcap(self, action):
        dialog = gtk.FileChooserDialog(_("Select a pcap file"), self,
                                       buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                                gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))

        for name, pattern in ((_('Pcap files'), '*.pcap'),
                              (_('Pcap gz files'), '*.pcap.gz'),
                              (_('All files'), '*')):

            filter = gtk.FileFilter()
            filter.set_name(name)
            filter.add_pattern(pattern)
            dialog.add_filter(filter)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            fname = dialog.get_filename()

            tab = self.get_tab("MainTab")
            tab.session_notebook.create_offline_session(fname)

        dialog.hide()
        dialog.destroy()

    def __on_quit(self, *args):
        self.hide()

        # We need to stop the pending sniff threads
        maintab = self.get_tab("MainTab")

        lst = []

        for page in maintab.session_notebook:
            if isinstance(page.context, Backend.TimedContext):
                lst.append(page.context)

        for ctx in lst:
            ctx.stop()

        for ctx in lst:
            ctx.join()

        gtk.main_quit()
