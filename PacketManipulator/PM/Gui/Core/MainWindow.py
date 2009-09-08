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
from PM.Core.Logger import log
from PM.Manager.PreferenceManager import Prefs
from PM.Manager.AttackManager import AttackManager

from PM.Gui.Widgets.StatusBar import StatusBar
from PM.higwidgets.higdialogs import HIGAlertDialog

__paned_imported = False

if Prefs()['gui.docking'].value.lower() == 'moo':
    try:
        from MooPaned import *
        __paned_imported = True
    except ImportError:
        log.info("moo library is not installed.")

elif Prefs()['gui.docking'].value.lower() == 'gdl':
    try:
        from GdlPaned import *
        __paned_imported = True
    except ImportError:
        log.info("GDL is not installed. Using fallback paned.")

if Prefs()['gui.docking'].value.lower() == 'standard' or not __paned_imported:
    from FallbackPaned import *
    __paned_imported = True

    log.info('Using fallback paned')

from PM.Gui.Tabs.VteTab import VteTab
from PM.Gui.Tabs.MainTab import MainTab
from PM.Gui.Tabs.HackTab import HackTab
from PM.Gui.Tabs.StatusTab import StatusTab
from PM.Gui.Tabs.ConsoleTab import ConsoleTab
from PM.Gui.Tabs.PropertyTab import PropertyTab
from PM.Gui.Tabs.HostListTab import HostListTab
from PM.Gui.Tabs.OperationsTab import FileOperation
from PM.Gui.Tabs.ProtocolSelectorTab import ProtocolSelectorTab
from PM.Gui.Tabs.OperationsTab import OperationsTab, SniffOperation, \
     AttackOperation, BtSniffOperation

from PM.Gui.Dialogs.Interface import InterfaceDialog
from PM.Gui.Dialogs.BtInterface import BtInterfaceDialog
from PM.Gui.Dialogs.Preferences import PreferenceDialog
from PM.Gui.Dialogs.NewAttack import NewAttackDialog
from PM.Gui.Dialogs.Routes import RoutesDialog
from PM.Gui.Plugins.Window import PluginWindow

from PM.Gui.Pages import PerspectiveType

from PM.Gui.Sessions.Base import Session
from PM.Gui.Sessions.AttackSession import AttackSession

from PM.Gui.Sessions import SessionType

from PM.Core.I18N import _
from PM.Core.Const import PM_DEVELOPMENT, PM_SVN_REVISION
from PM.Core.Const import PIXMAPS_DIR, PM_VERSION, PM_SITE

class MainWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_title("Packet Manipulator")
        self.set_icon_from_file(os.path.join(PIXMAPS_DIR, 'pm-logo.png'))
        self.set_default_size(600, 400)

        self.registered_tabs = {}

        # Binders for plugins
        self.perspective_binder = []
        self.session_binder = []

        for i in PerspectiveType.types:
            self.perspective_binder.append(list())

        for i in SessionType.types:
            self.session_binder.append(list())

        self.perspective_binder = tuple(self.perspective_binder)
        self.session_binder = tuple(self.session_binder)

        self.__create_widgets()
        self.__pack_widgets()
        self.__connect_signals()

        self.statusbar.push(_("Ready."), image=gtk.STOCK_YES)

        self.show_all()

    def __create_widgets(self):
        "Create widgets"

        self.main_actions = [
            ('File', None, _('File'), None),

            ('NewAttack', gtk.STOCK_NEW, _('New A_ttack'), '<Control>t',
                _('Create a new attack'), self.__on_new_attack),

            ('NewSequence', gtk.STOCK_NEW, _('_New sequence'), '<Control>n',
                _('Create a new sequence'), self.__on_new_sequence),

            ('Open', gtk.STOCK_OPEN, _('_Open'), '<Control>o',
                _('Open session'), self.__on_open_session),

            ('Save', gtk.STOCK_SAVE, _('_Save'), '<Control>s',
                _('Save session'), self.__on_save_session),

            ('SaveAs', gtk.STOCK_SAVE_AS, _('_Save as'), '<Control><Shift>s',
                _('Save session as'), self.__on_save_session_as),

            ('Quit', gtk.STOCK_QUIT, _('_Quit'), '<Control>q',
                _('Quit from application'), self.__on_quit),

            ('Capture', None, _('Capture'), None),

            ('Interface', gtk.STOCK_CONNECT, _('_Interface'), '<Control>i',
                _('Capture from interface'), self.__on_select_iface),
                
            ('Bluetooth', gtk.STOCK_CONNECT, _('Bluetooth'), None,
            _('Capture from Bluetooth interface'), self.__on_select_btiface),

            ('Attacks', None, _('Attacks'), None),

            ('Options', None, _('Options'), None),

            ('Routes', gtk.STOCK_NETWORK, _('Routing table'), '<Control>r',
                _('Routes editor'), self.__on_routing),

            ('Plugins', 'extension_small', _('Plugins'), None,
                _('Plugin manager'), self.__on_plugins),

            ('Preferences', gtk.STOCK_PREFERENCES, _('_Preferences'),
                '<Control>p', _('Preferences'), self.__on_preferences),

            ('Views', None, _('Views'), None),

            ('Help', None, _('Help'), None),

            ('About', gtk.STOCK_ABOUT, _('About'), None, None, self.__on_about),
        ]

        self.default_ui = """<menubar>
            <menu action='File'>
                <menuitem action='NewSequence'/>
                <menuitem action='NewAttack'/>
                <separator/>
                <menuitem action='Open'/>
                <menuitem action='Save'/>
                <menuitem action='SaveAs'/>
                <separator/>
                <menuitem action='Quit'/>
            </menu>
            <menu action='Capture'>
                <menuitem action='Interface'/>
                <menuitem action='Bluetooth'/>
            </menu>
            <menu action='Attacks'/>
            <menu action='Options'>
                <menuitem action='Routes'/>
                <separator/>
                <menuitem action='Plugins'/>
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

        self.ui_manager.connect('connect-proxy', self.__on_connect_proxy)
        self.ui_manager.connect('disconnect-proxy', self.__on_disconnect_proxy)

        # Set unsensitive the attack menu
        item = self.ui_manager.get_widget('/menubar/Attacks')
        item.set_sensitive(False)

        # Central widgets
        self.main_paned = UmitPaned()

        self.vbox = gtk.VBox(False, 2)
        self.statusbar = StatusBar()

        self.plugin_window = PluginWindow()

    def register_attack_item(self, name, lbl, tooltip, stock, callback):
        attackitem = self.ui_manager.get_widget('/menubar/Attacks')
        menu = attackitem.get_submenu()

        attackitem.show()

        if not menu:
            menu = gtk.Menu()
            attackitem.set_submenu(menu)

        act = gtk.Action(name, lbl, tooltip, stock)
        act.connect('activate', callback)

        item = act.create_menu_item()
        item.show()

        menu.append(item)

        return act, item

    def deregister_attack_item(self, item):
        attackitem = self.ui_manager.get_widget('/menubar/Attacks')
        menu = attackitem.get_submenu()

        if not menu:
            return

        for citem in menu:
            if citem is item:
                citem.hide()
                menu.remove(citem)

                if not menu.get_children():
                    attackitem.set_sensitive(False)

                return True

        return False

    def get_tab(self, name):
        """
        Get a tab from its name

        @param name the name of the tab
        """

        return self.registered_tabs[name]

    def deregister_tab(self, tab):
        """
        Deregister a tab deleting his CheckMenu and tab from the paned

        @param tab the tab to deregister
        @return True if is ok or False
        """

        item = self.ui_manager.get_widget('/menubar/Views')
        menu = item.get_submenu()

        def find_tab(item, udata):
            tab, find = udata

            if item.get_data('tab-object') is tab:
                find = item
                return True

        find = None
        menu.foreach(find_tab, (tab, find))

        if find is not None:
            menu.remove(find)
            self.main_paned.remove_view(tab)
            del self.registered_tabs[tab.name]

            return True

        return False

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

        if tab.name in self.registered_tabs:
            raise Exception("Tab already present")

        # Ok we should add a CheckMenuItem to this fucking menu
        self.registered_tabs[tab.name] = tab

        log.debug("Tab %s registered as %s" % (tab.label_text, tab.name))

        if tab.tab_position is None:
            # This is the central widget so it should be added
            # with no MenuItem
            self.main_paned.add_view(tab)
            return

        new_item = gtk.CheckMenuItem(tab.label_text)
        new_item.set_data('tab-object', tab)
        new_item.connect('toggled', self.__on_toggle_tab_menu, tab)

        if show:
            new_item.set_active(True)

        new_item.show()
        menu.append(new_item)

    def create_session(self, menu, tup):
        """
        Create a new session using ctxklass and sessklass

        @param menu gtk.MenuItem
        @param tuple a tuple containing (sessklass, ctxklass)
        """
        sessklass, ctxklass = tup
        maintab = self.get_tab("MainTab")
        maintab.session_notebook.create_session(sessklass, ctxklass)

    def register_session(self, sessklass, ctxklass=None):
        """
        Register a custom session class and returns the new id
        of the SessionType

        @param sessklass the custom session class
        @param ctxklass the context class to use
        @return id
        """

        log.debug('Registering a new session')

        if sessklass.session_menu is not None:
            log.debug('Creating new menu entry named %s for the session' % \
                      sessklass.session_menu)

            item = self.ui_manager.get_widget('/menubar/File')
            menu = item.get_submenu()

            item = gtk.MenuItem(sessklass.session_menu)
            item.connect('activate', self.create_session, (sessklass, ctxklass))
            item.show()

            menu.insert(item, 2)

            sessklass.session_menu_object = item

        return SessionType.add_session(sessklass)

    def deregister_session(self, sessklass):
        if sessklass.session_menu_object:
            menu = self.ui_manager.get_widget('/menubar/File').get_submenu()
            sessklass.session_menu_object.hide()

            menu.remove(sessklass.session_menu_object)

        return SessionType.remove_session(sessklass)

    def bind_session(self, ptype, persp_klass, show_pers=True, resize=False, \
                     shrink=True):
        """
        Bind the perspective 'pers_klass' to Session 'ptype'

        @param ptype the Session type to customize
        @param persp_klass the perspective class to add to the selected Session
        @param show_pers choose to show the perspective
        @param resize if True child should resize when the paned is resized
        @param shrink if True child can be made smaller than its minimum size
                      request
        """

        log.debug(
            "Binding perspective %s to Session %s" % \
            (persp_klass, SessionType.types[ptype])
        )

        self.session_binder[ptype].append((persp_klass, show_pers, \
                                           resize, shrink))

        klass = SessionType.types[ptype]
        maintab = self.get_tab("MainTab")

        for page in maintab.session_notebook:
            if isinstance(page, klass):
                self.apply_bindings(page, ptype)

    def unbind_session(self, type, persp_klass):
        try:
            for i in range(len(self.session_binder[ptype])):
                (klass, show, resize, shrink) = self.session_binder[ptype][i]

                if klass is not persp_klass:
                    continue

                del self.session_binder[type][i]

                klass = SessionType.types[type]
                maintab = self.get_tab("MainTab")

                for page in maintab.session_notebook:
                    if isinstance(page, klass):
                        page.remove_perspective(klass)

                log.debug(
                    "Binding method %s for perspective of type %s removed" % \
                    (persp_klass, SessionType.types[type])
                )

                return True
        except:
            log.error(
                "Failed to remove binding method %s for session of type %s" % \
                (persp_klass, SessionType.type[ptype])
            )

        return False

    def apply_bindings(self, page, ptype):
        for persp_klass, show, resize, shrink in self.session_binder[ptype]:
            page.add_perspective(persp_klass, show, resize, shrink)

    def bind_perspective(self, ptype, callback):
        """
        Bind the perspective 'type'

        The callback should be of the type
          def perspective_cb(perspective, type, already_present, added)

        @param type the perspective's type (see also PerspectiveType)
        @param callback the callback to execute when a new
               perspective of type 'type' is created
        """

        log.debug(
            "Binding method %s for perspective of type %s" % \
            (callback, PerspectiveType.types[ptype])
        )

        self.perspective_binder[ptype].append(callback)

        maintab = self.get_tab("MainTab")

        for page in maintab.session_notebook:
            if not isinstance(page, Session):
                continue

            for perspective in page.perspectives:
                idx = PerspectiveType.types[type(perspective)]

                callback(perspective, idx, True, True)

    def debind_perspective(self, type, callback):
        """
        Remove the binding callback for perspective of type 'type'

        @param type the perspective type
        @param callback the callback to remove
        @return True if the callback is removed correctly
        """

        try:
            self.perspective_binder[type].remove(callback)

            maintab = self.get_tab("MainTab")

            for page in maintab.session_notebook:
                if not isinstance(page, Session):
                    continue

                for perspective in page.perspectives:
                    idx = PerspectiveType.types[type(perspective)]

                    callback(perspective, idx, True, False)

            log.debug(
                "Binding method %s for perspective of type %s removed" % \
                (callback, PerspectiveType.types[type])
            )

            return True
        except:
            log.error(
                "Failed to remove binding method %s "
                "for perspective of type %s" % \
                (callback, PerspectiveType.types[type])
            )

        return False

    def __pack_widgets(self):
        "Pack widgets"

        self.menubar = self.ui_manager.get_widget("/menubar")
        self.vbox.pack_start(self.menubar, False, False, 0)

        self.toolbar = self.ui_manager.get_widget("/toolbar")
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        self.vbox.pack_start(self.toolbar, False, False, 0)

        item = self.ui_manager.get_widget('/menubar/Views')
        item.remove_submenu()

        item = self.ui_manager.get_widget('/menubar/Attacks')
        item.remove_submenu()

        self.vbox.pack_start(self.main_paned)
        self.vbox.pack_start(self.statusbar, False, False)

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
        self.register_tab(HostListTab(),
                          Prefs()['gui.views.hostlist_tab'].value)

        self.add(self.vbox)

    def __on_menuitem_selected(self, menuitem, tooltip):
        self.statusbar.push(tooltip)

    def __on_menuitem_deselected(self, menuitem):
        self.statusbar.pop()

    def __on_connect_proxy(self, uimgr, action, widget):
        tooltip = action.get_property('tooltip')

        if isinstance(widget, gtk.MenuItem) and tooltip:
            cid = widget.connect('select', self.__on_menuitem_selected, tooltip)
            cid2 = widget.connect('deselect', self.__on_menuitem_deselected)
            widget.set_data('pm::cids', (cid, cid2))

    def __on_disconnect_proxy(self, uimgr, action, widget):
        cids = widget.get_data('pm::cids')

        if not isinstance(cids, tuple):
            return

        try:
            for name, cid in cids:
                widget.disconnect(cid)
        except:
            pass

    def __connect_signals(self):
        "Connect signals"
        self.connect('delete-event', self.__on_quit)

        # Ok we need also to connect signals from main notebook
        # so we could manage easilly the bind_perspective calls

        maintab = self.get_tab("MainTab")
        maintab.session_notebook.connect('page-added',
                                         self.__on_maintab_page_added)
        maintab.session_notebook.connect('page-removed',
                                         self.__on_maintab_page_removed)
        maintab.session_notebook.connect('switch-page',
                                         self.__on_maintab_page_switched)

    def connect_tabs_signals(self):
        "Used to connect signals between tabs"

        for key, tab in self.registered_tabs.items():
            tab.connect_tab_signals()

    def __on_maintab_page_added(self, notebook, page, pagenum):
        if not isinstance(page, Session):
            return

        for perspective in page.perspectives:
            try:
                idx = PerspectiveType.types[type(perspective)]

                for callback in self.perspective_binder[idx]:
                    callback(perspective, idx, False, True)
            except:
                pass

    def __on_maintab_page_removed(self, notebook, page, pagenum):
        if not isinstance(page, Session):
            return

        for perspective in page.perspectives:
            try:
                idx = PerspectiveType.types[type(perspective)]

                for callback in self.perspective_binder[idx]:
                    callback(perspective, idx, True, False)
            except:
                pass

    def __on_maintab_page_switched(self, notebook, page, pagenum):
        page = notebook.get_nth_page(pagenum)
        item = self.ui_manager.get_widget('/menubar/Attacks')

        if not isinstance(page, AttackSession):
            item.set_sensitive(False)
        else:
            submenu = item.get_submenu()

            if submenu and submenu.get_children():
                item.set_sensitive(True)

    def __on_toggle_tab_menu(self, menuitem, tab):
        if menuitem.get_active():
            self.main_paned.add_view(tab)
        else:
            self.main_paned.remove_view(tab)

    def __on_routing(self, action):
        dialog = RoutesDialog(self)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            dialog.save()

        dialog.hide()
        dialog.destroy()

    def __on_plugins(self, action):
        self.plugin_window.show()

    def __on_preferences(self, action):
        dialog = PreferenceDialog(self)
        dialog.show()

    def __on_about(self, action):
        dialog = gtk.AboutDialog()

        dialog.set_logo(
            gtk.gdk.pixbuf_new_from_file(os.path.join(PIXMAPS_DIR,
                                                      'pm-logo.png'))
        )
        dialog.set_name("PacketManipulator")
        dialog.set_version(PM_VERSION)

        dialog.set_website(PM_SITE)
        dialog.set_website_label(PM_SITE)

        dialog.set_comments(_("Packet manipulation made easy%s" \
                              "\n«Audaces fortuna adiuvat»") % \
                            ((PM_DEVELOPMENT) and \
                                (' (SVN revision %s)' % PM_SVN_REVISION) or \
                                ('')))

        dialog.set_authors(['Francesco Piccinno <stack.box@gmail.com>'])

        dialog.set_copyright('\n'.join(
            ('Copyright (C) 2008 Francesco Piccinno' \
                     ' <stack.box at gmail dot com>',
             'Copyright (C) 2008 Adriano Monteiro Marques' \
                          ' <py.adriano at gmail dot com>')))

        dialog.set_license(_('This program is relased '
                             'under the terms of GPLv2'))

        dialog.run()
        dialog.hide()
        dialog.destroy()

    def __on_select_iface(self, action):
        dialog = InterfaceDialog(self)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            iface = dialog.get_selected()
            args = dialog.get_options()

            if iface or args['capmethod'] == 1:
                tab = self.get_tab('OperationsTab')
                tab.tree.append_operation(SniffOperation(iface, **args))

        dialog.hide()
        dialog.destroy()
    
    def __on_select_btiface(self, action):
        log.debug('On_select_btiface')
        dialog = BtInterfaceDialog(self)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            
            
            iface = dialog.get_selected()
            args = dialog.get_options()
            
            if iface:
                log.debug('MainWindow: BtSniff: %s selected' % iface)
                tab = self.get_tab('OperationsTab')
                tab.tree.append_operation(BtSniffOperation(iface, **args))
        
        dialog.hide()
        dialog.destroy()

    def start_new_attack(self, dev1, dev2, bpf_filter):
        log.debug('Creating a new AttackOperation using %s %s %s' \
                  % (dev1, dev2, bpf_filter))

        tab = self.get_tab('OperationsTab')
        tab.tree.append_operation(AttackOperation(dev1, dev2, bpf_filter))

    def __on_new_attack(self, action):
        dialog = NewAttackDialog(self)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            inputs = dialog.get_inputs()
            self.start_new_attack(*inputs)

        dialog.hide()
        dialog.destroy()

    def __on_new_sequence(self, action):
        tab = self.get_tab('MainTab')
        tab.session_notebook.create_sequence_session([])

    def __on_open_session(self, action):
        types = {}
        sessions = (Backend.StaticContext,
                    Backend.SequenceContext,
                    Backend.SniffContext)

        for ctx in sessions:
            for name, pattern in ctx.file_types:
                types[pattern] = (name, ctx)

        dialog = gtk.FileChooserDialog(_("Select a session"), self,
                               buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))

        filterall = gtk.FileFilter()
        filterall.set_name(_('All supported files'))
        [filterall.add_pattern(k) for k in types]
        dialog.add_filter(filterall)

        for pattern, (name, ctx) in types.items():
            filter = gtk.FileFilter()
            filter.set_name(name)
            filter.add_pattern(pattern)
            dialog.add_filter(filter)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            ctx = None
            fname = dialog.get_filename()

            try:
                find = fname.split('.')[-1]

                for pattern in types:
                    if pattern.split('.')[-1] == find:
                        ctx = types[pattern][1]
            except:
                pass

            if ctx is not Backend.SequenceContext and \
               ctx is not Backend.SniffContext and \
               ctx is not Backend.StaticContext:

                d = HIGAlertDialog(type=gtk.MESSAGE_ERROR,
                    message_format=_("Unable to open selected session"),
                    secondary_text=_("PacketManipulator is unable to guess the "
                                     "file type. Try to modify the extension "
                                     "and to reopen the file."))
                d.run()
                d.destroy()
            else:
                self.open_generic_file_async(fname)

        dialog.hide()
        dialog.destroy()

    def open_generic_file_async(self, fname):
        """
        Open a generic file (pcap/sequence and other supported file format)
        @param fname the path to the file to open
        """
        tab = self.get_tab("OperationsTab")
        tab.tree.append_operation(FileOperation(fname, FileOperation.TYPE_LOAD))

    def open_generic_file(self, fname):
        """
        Open a generic file (pcap/sequence and other supported file format)
        @param fname the path to the file to open
        @return a PM.Session.Base.Session object or None on errors
        """

        if not os.path.isfile(fname):
            return None

        types = {}
        sessions = (Backend.StaticContext,
                    Backend.SequenceContext,
                    Backend.SniffContext)

        for ctx in sessions:
            for name, pattern in ctx.file_types:
                types[pattern] = (name, ctx)

        try:
            find = fname.split('.')[-1]

            for pattern in types:
                if pattern.split('.')[-1] == find:
                    ctx = types[pattern][1]
        except:
            pass

        tab = self.get_tab("MainTab")

        if ctx is Backend.SequenceContext:
            return tab.session_notebook.load_sequence_session(fname)

        elif ctx is Backend.SniffContext:
            return tab.session_notebook.load_sniff_session(fname)

        elif ctx is Backend.StaticContext:
            return tab.session_notebook.load_static_session(fname)

    def __on_save_session(self, action):
        maintab = self.get_tab("MainTab")
        session = maintab.get_current_session()

        if session:
            session.save()

    def __on_save_session_as(self, action):
        maintab = self.get_tab("MainTab")
        session = maintab.get_current_session()

        if session:
            session.save_as()

    def __on_quit(self, *args):
        self.hide()

        # We need to stop the pending sniff threads
        maintab = self.get_tab("MainTab")

        lst = []

        for page in maintab.session_notebook:
            if isinstance(page, Session) and \
               isinstance(page.context, Backend.TimedContext):
                lst.append(page.context)

        for ctx in lst:
            ctx.stop()

        # Avoids joining all threads are daemon
        #for ctx in lst:
        #    ctx.join()

        log.debug('Saving options before exiting')
        Prefs().write_options()

        log.debug('Saving attack configurations')
        AttackManager().write_configurations()

        gtk.main_quit()
