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

"""
This module contains the MainWindow class
"""

import gtk

import os
import random

from umit.pm import backend
from umit.pm.core.logger import log
from umit.pm.core.bus import ServiceBus
from umit.pm.manager.preferencemanager import Prefs
from umit.pm.manager.auditmanager import AuditManager

from umit.pm.gui.widgets.statusbar import StatusBar
from umit.pm.higwidgets.higdialogs import HIGAlertDialog

__paned_imported = False

if Prefs()['gui.docking'].value.lower() == 'moo':
    try:
        from moopaned import *
        __paned_imported = True
    except ImportError:
        log.info("moo library is not installed.")

elif Prefs()['gui.docking'].value.lower() == 'gdl':
    try:
        from gdlpaned import *
        __paned_imported = True
    except ImportError:
        log.info("GDL is not installed. Using fallback paned.")

if Prefs()['gui.docking'].value.lower() == 'standard' or not __paned_imported:
    from fallbackpaned import *
    __paned_imported = True

    log.info('Using fallback paned')

from umit.pm.gui.tabs.vtetab import VteTab
from umit.pm.gui.tabs.maintab import MainTab
from umit.pm.gui.tabs.hacktab import HackTab
from umit.pm.gui.tabs.statustab import StatusTab
from umit.pm.gui.tabs.consoletab import ConsoleTab
from umit.pm.gui.tabs.propertytab import PropertyTab
from umit.pm.gui.tabs.hostlisttab import HostListTab
from umit.pm.gui.tabs.operationstab import FileOperation
from umit.pm.gui.tabs.protocolselectortab import ProtocolSelectorTab
from umit.pm.gui.tabs.operationstab import OperationsTab, SniffOperation, \
     AuditOperation

from umit.pm.gui.dialogs.interface import InterfaceDialog
from umit.pm.gui.dialogs.preferences import PreferenceDialog
from umit.pm.gui.dialogs.newaudit import NewAuditDialog
from umit.pm.gui.dialogs.routes import RoutesDialog
from umit.pm.gui.plugins.window import PluginWindow

from umit.pm.gui.pages import PerspectiveType

from umit.pm.gui.sessions.base import Session
from umit.pm.gui.sessions.auditsession import AuditSession

from umit.pm.gui.sessions import SessionType

from umit.pm.core.i18n import _
from umit.pm.core.const import PM_DEVELOPMENT, PM_SVN_REVISION, \
                          PIXMAPS_DIR, PM_VERSION, PM_SITE, \
                          PM_CODENAME, PM_SLOGANS

class MainWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_title("Packet Manipulator - " + str(PM_VERSION))
        self.set_icon_list(gtk.gdk.pixbuf_new_from_file(
            os.path.join(PIXMAPS_DIR, 'pm-logo.png'))
        )
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

            ('NewAudit', gtk.STOCK_NEW, _('New A_udit'), '<Control>t',
                _('Create a new audit'), self.__on_new_audit),

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

            ('Audits', None, _('Audits'), None),

            ('Mitm', None, _('MITM'), None),

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
                <menuitem action='NewAudit'/>
                <separator/>
                <menuitem action='Open'/>
                <menuitem action='Save'/>
                <menuitem action='SaveAs'/>
                <separator/>
                <menuitem action='Quit'/>
            </menu>
            <menu action='Capture'>
                <menuitem action='Interface'/>
            </menu>
            <menu action='Audits'/>
            <menu action='Mitm'/>
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
                <toolitem action='NewSequence'/>
                <toolitem action='NewAudit'/>
                <separator/>
                <toolitem action='Open'/>
                <toolitem action='Save'/>
                <separator/>
                <toolitem action='Interface'/>
                <toolitem action='Routes'/>
                <separator/>
                <toolitem action='Plugins'/>
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

        # Set unsensitive the audit menu and also Mitm
        item = self.ui_manager.get_widget('/menubar/Audits')
        item.set_sensitive(False)

        item = self.ui_manager.get_widget('/menubar/Mitm')
        item.set_sensitive(False)

        # Central widgets
        self.main_paned = UmitPaned()

        self.vbox = gtk.VBox(False, 2)
        self.statusbar = StatusBar()

        self.plugin_window = PluginWindow()

    def register_audit_item(self, name, lbl, tooltip, stock, callback):
        return self.__register_audit_item('/menubar/Audits', name, lbl, tooltip,
                                   stock, callback)

    def register_audit_mitm_item(self, name, lbl, tooltip, stock, callback):
        return self.__register_audit_item('/menubar/Mitm', name, lbl, tooltip,
                                   stock, callback)

    def __register_audit_item(self, mname, name, lbl, tooltip, stock, cb):
        audititem = self.ui_manager.get_widget(mname)
        menu = audititem.get_submenu()

        audititem.show()

        if not menu:
            menu = gtk.Menu()
            audititem.set_submenu(menu)

        act = gtk.Action(name, lbl, tooltip, stock)
        act.connect('activate', cb)

        item = act.create_menu_item()
        item.set_name(name)
        item.show()

        menu.append(item)

        return act, item

    def deregister_audit_item(self, item):
        return self.__deregister_audit_item('/menubar/Audits', item)

    def deregister_audit_mitm_item(self, item):
        return self.__deregister_audit_item('/menubar/Mitm', item)

    def __deregister_audit_item(self, mname, item):
        audititem = self.ui_manager.get_widget(mname)
        menu = audititem.get_submenu()

        if not menu:
            return False

        for citem in menu:
            if citem is item:
                citem.hide()
                menu.remove(citem)

                if not menu.get_children():
                    audititem.set_sensitive(False)

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
        ServiceBus().call('pm.sessions', 'create_session', sessklass, ctxklass)

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

    def bind_session(self, ptype, persp_klass, show_pers=True, resize=False):
        """
        Bind the perspective 'pers_klass' to Session 'ptype'

        @param ptype the Session type to customize
        @param persp_klass the perspective class to add to the selected Session
        @param show_pers choose to show the perspective
        @param resize if True child should resize when the paned is resized
        """

        log.debug(
            "Binding perspective %s to Session %s" % \
            (persp_klass, SessionType.types[ptype])
        )

        self.session_binder[ptype].append((persp_klass, show_pers, resize))

        klass = SessionType.types[ptype]

        for page in ServiceBus().call('pm.sessions', 'get_sessions'):
            if isinstance(page, klass):
                self.apply_bindings(page, ptype, persp_klass)

    def unbind_session(self, ptype, persp_klass):
        try:
            for i in range(len(self.session_binder[ptype])):
                (klass, show, resize) = self.session_binder[ptype][i]

                if klass is not persp_klass:
                    continue

                del self.session_binder[ptype][i]

                klass = SessionType.types[ptype]

                for page in ServiceBus().call('pm.sessions', 'get_sessions'):
                    if isinstance(page, klass):
                        page.remove_perspective(persp_klass)

                log.debug(
                    "Binding method %s for perspective of type %s removed" % \
                    (persp_klass, SessionType.types[ptype])
                )

                return True
        except:
            log.error(
                "Failed to remove binding method %s for session of type %s" % \
                (persp_klass, SessionType.type[ptype])
            )

        return False

    def apply_bindings(self, page, ptype, klass=None):
        for persp_klass, show, resize in self.session_binder[ptype]:
            if not klass or (klass and persp_klass is klass):
                page.add_perspective(persp_klass, show, resize)

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

        for page in ServiceBus().call('pm.sessions', 'get_sessions'):
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

            for page in ServiceBus().call('pm.sessions', 'get_sessions'):
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

        item = self.ui_manager.get_widget('/menubar/Audits')
        item.remove_submenu()

        item = self.ui_manager.get_widget('/menubar/Mitm')
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
        self.__on_maintab_page_switched(maintab.session_notebook, None, 0)

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

        item = self.ui_manager.get_widget('/menubar/Audits')
        mitm_item = self.ui_manager.get_widget('/menubar/Mitm')

        if isinstance(page, Session) and getattr(page, 'context', None):
            enabled = (page.context.file_types and True or False)
        else:
            enabled = False

        for act in ('Save', 'SaveAs'):
            self.main_action_group.get_action(act).set_sensitive(enabled)

        if not isinstance(page, AuditSession):
            item.set_sensitive(False)
            mitm_item.set_sensitive(False)
        else:
            submenu = item.get_submenu()

            if submenu and submenu.get_children():
                item.set_sensitive(True)

            submenu = mitm_item.get_submenu()

            if submenu and submenu.get_children():
                mitm_item.set_sensitive(True)

                for item in submenu:
                    if item.get_name() in page.mitm_attacks:
                        item.set_sensitive(False)
                    else:
                        item.set_sensitive(True)

    def __on_toggle_tab_menu(self, menuitem, tab):
        if menuitem.get_active():
            self.main_paned.add_view(tab)
        else:
            self.main_paned.remove_view(tab)

    def __on_routing(self, action):
        dialog = RoutesDialog(self)
        dialog.set_transient_for(self)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            dialog.save()

        dialog.hide()
        dialog.destroy()

    def __on_plugins(self, action):
        self.plugin_window.show()

    def __on_preferences(self, action):
        dialog = PreferenceDialog(self)
        dialog.set_transient_for(self)
        dialog.show()

    def __on_about(self, action):
        dialog = gtk.AboutDialog()

        dialog.set_logo(
            gtk.gdk.pixbuf_new_from_file(os.path.join(PIXMAPS_DIR,
                                                      'pm-logo.png'))
        )
        dialog.set_transient_for(self)
        dialog.set_name("PacketManipulator")
        dialog.set_version(PM_VERSION + (PM_CODENAME \
                                         and ' (%s)' % PM_CODENAME \
                                         or ''))

        dialog.set_website(PM_SITE)
        dialog.set_website_label(PM_SITE)

        dialog.set_comments(_("Packet manipulation made easy%s\n%s") % \
                             ((PM_DEVELOPMENT \
                               and ' (SVN revision %s)' % PM_SVN_REVISION \
                               or ''),
                             "«%s»" % random.choice(PM_SLOGANS)))

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
        dialog.set_transient_for(self)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            iface = dialog.get_selected()
            args = dialog.get_options()

            if iface or args['capmethod'] == 1:
                tab = self.get_tab('OperationsTab')
                tab.tree.append_operation(SniffOperation(iface, **args))

        dialog.hide()
        dialog.destroy()

    def start_new_audit(self, dev1, dev2, bpf_filter, skipfwd, unoffensive):
        log.debug('Creating a new AuditOperation using dev1: %s dev2: %s '
                  'bpf: %s skipfwd: %s unoffensive: %s' \
                  % (dev1, dev2, bpf_filter, skipfwd, unoffensive))

        tab = self.get_tab('OperationsTab')
        tab.tree.append_operation(AuditOperation(dev1, dev2, bpf_filter, \
                                                 skipfwd, unoffensive))

    def __on_new_audit(self, action):
        dialog = NewAuditDialog(self)
        dialog.set_transient_for(self)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            inputs = dialog.get_inputs()
            self.start_new_audit(*inputs)

        dialog.hide()
        dialog.destroy()

    def __on_new_sequence(self, action):
        ServiceBus().call('pm.sessions', 'create_sequence_session', [])

    def __on_open_session(self, action):
        types = {}
        sessions = (backend.StaticContext,
                    backend.SequenceContext,
                    backend.SniffContext)

        for ctx in sessions:
            for name, pattern in ctx.file_types:
                types[pattern] = (name, ctx)

        dialog = gtk.FileChooserDialog(_("Select a session"), self,
                               buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))
        dialog.set_transient_for(self)

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

            if ctx is not backend.SequenceContext and \
               ctx is not backend.SniffContext and \
               ctx is not backend.StaticContext:

                d = HIGAlertDialog(type=gtk.MESSAGE_ERROR,
                    message_format=_("Unable to open selected session"),
                    secondary_text=_("PacketManipulator is unable to guess the "
                                     "file type. Try to modify the extension "
                                     "and to reopen the file."))
                d.set_transient_for(self)
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
        @return a umit.pm.session.base.Session object or None on errors
        """

        if not os.path.isfile(fname):
            return None

        types = {}
        sessions = (backend.StaticContext,
                    backend.SequenceContext,
                    backend.SniffContext)

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

        if ctx is backend.SequenceContext:
            return ServiceBus().call('pm.sessions', 'load_sequence_session',
                                     fname)

        elif ctx is backend.SniffContext:
            return ServiceBus().call('pm.sessions', 'load_sniff_session',
                                     fname)

        elif ctx is backend.StaticContext:
            return ServiceBus().call('pm.sessions', 'load_static_session',
                                     fname)

    def __on_save_session(self, action):
        session = ServiceBus().call('pm.sessions', 'get_current_session')

        if session:
            session.save()

    def __on_save_session_as(self, action):
        session = ServiceBus().call('pm.sessions', 'get_current_session')

        if session:
            session.save_as()

    def __on_quit(self, *args):
        self.hide()

        # We need to stop the pending sniff threads
        lst = []

        for page in ServiceBus().call('pm.sessions', 'get_sessions'):
            if isinstance(page, Session) and \
               isinstance(page.context, backend.TimedContext):
                lst.append(page.context)

        for ctx in lst:
            ctx.stop()

        # Avoids joining all threads are daemon
        #for ctx in lst:
        #    ctx.join()

        errs = []

        try:
            log.debug('Saving options before exiting')
            Prefs().write_options()
        except IOError, err:
            errs.append(err)

        try:
            log.debug('Saving audit configurations')
            AuditManager().write_configurations()
        except IOError, err:
            errs.append(err)

        if errs:
            errstr = '\n'.join(
                map(lambda x: 'on %s (%s)' % (x.filename, x.strerror),
                errs)
            )

            dialog = HIGAlertDialog(
                type=gtk.MESSAGE_ERROR,
                message_format=_('Error while saving configurations'),
                secondary_text=errstr + '\n\n' + _('Be sure to have ' \
                                 'read and write permission.'))
            dialog.set_transient_for(self)
            dialog.run()
            dialog.destroy()

        gtk.main_quit()
