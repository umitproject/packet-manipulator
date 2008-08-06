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

try:
    from paned import *
except ImportError:
    print "moo not installed. Using fallback UmitPaned .."
    from fallbackpaned import *

from Tabs.VteTab import VteTab
from Tabs.MainTab import MainTab
from Tabs.HackTab import HackTab
from Tabs.ConsoleTab import ConsoleTab
from Tabs.PropertyTab import PropertyTab
from Tabs.ProtocolSelectorTab import ProtocolSelectorTab

from Dialogs.Interface import InterfaceDialog
from Dialogs.Preferences import PreferenceDialog
from Dialogs.Routes import RoutesDialog

from umitCore.I18N import _
from umitCore.Paths import Path

class MainWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_title("Packet Manipulator")
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
            ('Open', gtk.STOCK_OPEN, _('_Open'), '<Control>o'),
            ('Save', gtk.STOCK_SAVE, _('_Save packet'), '<Control>s', None, self.__on_save_template),
            ('SaveAs', gtk.STOCK_SAVE, _('Save as'), None),
            ('Quit', gtk.STOCK_QUIT, _('_Quit'), '<Control>q'),
            
            ('Capture', None, _('Capture'), None),
            ('Interface', gtk.STOCK_CONNECT, _('_Interface'), '<Control>i', None, self.__on_select_iface),

            ('Options', None, _('Options'), None),
            ('Routes', gtk.STOCK_NETWORK, _('Routing table'), '<Control>r', None, self.__on_routing),
            ('Preferences', gtk.STOCK_PREFERENCES, _('_Preferences'), '<Control>p', None, self.__on_preferences),

            ('Views', None, _('Views'), None),

            ('Help', None, _('Help'), None),
            ('About', gtk.STOCK_ABOUT, _('About'), None, None, self.__on_about),
        ]

        self.default_ui = """<menubar>
            <menu action='File'>
                <menuitem action='Open'/>
                <menuitem action='Save'/>
                <menuitem action='SaveAs'/>
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
                <toolitem action='Save'/>
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
        return self.registered_tabs[name]

    def register_tab(self, tab, show=True):
        item = self.ui_manager.get_widget('/menubar/Views')
        menu = item.get_submenu()

        item.show()

        if not menu:
            menu = gtk.Menu()
            item.set_submenu(menu)

        if tab.label_text in self.registered_tabs:
            raise Exception("Tab already present")

        # Ok we should add a CheckMenuItem to this fucking menu
        self.registered_tabs[tab.label_text] = tab

        print "Tab %s registered" % tab.label_text

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
        self.vbox.pack_start(self.toolbar, False, False, 0)

        item = self.ui_manager.get_widget('/menubar/Views')
        item.remove_submenu()
        
        self.vbox.pack_start(self.main_paned)

        # Tabs
        self.register_tab(MainTab())
        self.register_tab(ProtocolSelectorTab())
        self.register_tab(PropertyTab())

        # Hidden tabs
        self.register_tab(VteTab(), False)
        self.register_tab(HackTab(), False)
        self.register_tab(ConsoleTab(), False)

        self.add(self.vbox)

    def __connect_signals(self):
        "Connect signals"
        self.connect('delete-event', lambda *w: gtk.main_quit())

    def connect_tabs_signals(self):
        "Used to connect signals between tabs"

        for key, tab in self.registered_tabs.items():
            tab.connect_tab_signals()

    def __on_toggle_tab_menu(self, menuitem, tab):
        if menuitem.get_active():
            self.main_paned.add_view(tab)
        else:
            self.main_paned.remove_view(tab)

    def __on_save_template(self, action):
        session = self.get_tab("MainTab").get_current_session()

        if not session:
            return

        print "Dumping XML structure for protocol", session.protocol

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

        dialog.set_version("0.1")
        dialog.set_comments("PacketManipulator is a visual packet forger")

        dialog.run()
        dialog.hide()
        dialog.destroy()

    def __on_select_iface(self, action):
        dialog = InterfaceDialog(self)

        dialog.run()
        
        print "IFace selected:", dialog.get_selected()
        print "Options:", dialog.get_options()
        dialog.hide()
        dialog.destroy()

if __name__ == "__main__":
    app = MainWindow()
    app.run()
