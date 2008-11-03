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

import sys, os, os.path

import gtk
import gobject

from libtrace import tracert

from threading import Thread

from PM.Backend import StaticContext, traceroute
from PM.Core.Logger import log
from PM.Core.Atoms import generate_traceback

from PM.Gui.Core.App import PMApp
from PM.Gui.Plugins.Engine import Plugin
from PM.Gui.Sessions.Base import Session

from PM.Gui.Sessions import SessionType
from PM.Gui.Pages.Base import Perspective

from PM.Core.Errors import PMErrorException
from PM.Manager.PreferenceManager import Prefs

try:
    import webkit
except ImportError:
    raise PMErrorException("I need python binding for webkit")

if Prefs()['backend.system'].value.lower() != 'scapy':
    raise PMErrorException("I need scapy to work!")

_ = str
glocator = None

class TracerouteMap(Perspective):
    icon = gtk.STOCK_INFO
    title = _('Visual traceroute')

class Traceroute(Perspective):
    icon = gtk.STOCK_INFO
    title = _('Traceroute')

    def create_ui(self):
        self.toolbar = gtk.Toolbar()
        
        # Entry / dport / maxttl / timeout
        self.target = gtk.Entry()
        self.dport = gtk.SpinButton(gtk.Adjustment(80, 1, 65535, 1, 1))
        self.maxttl = gtk.SpinButton(gtk.Adjustment(30, 1, 255, 1, 1))
        self.timeout = gtk.SpinButton(gtk.Adjustment(2, 1, 10, 1, 1))

        for label, widget in zip((_("Target:"), _("Port:"),
                                  _("Max. TTL:"), _("Timeout:")),
                                 (self.target, self.dport,
                                  self.maxttl, self.timeout)):

            item = gtk.ToolItem()

            lbl = gtk.Label(label)
            lbl.set_alignment(0, 0.5)

            hbox = gtk.HBox(False, 2)
            hbox.set_border_width(2)

            hbox.pack_start(lbl, False, False)
            hbox.pack_start(widget)

            item.add(hbox)

            if widget is self.target:
                item.set_expand(True)

            self.toolbar.insert(item, -1)

        act = gtk.Action(None, None, _('Start tracing'), gtk.STOCK_CONNECT)
        act.connect('activate', self.__on_trace)

        self.toolbar.insert(act.create_tool_item(), -1)

        self.pack_start(self.toolbar, False, False)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # Protocol / Information
        self.store = gtk.ListStore(int, str, str)
        self.tree = gtk.TreeView(self.store)

        self.tree.append_column(gtk.TreeViewColumn('TTL', gtk.CellRendererText(), text=0))
        self.tree.append_column(gtk.TreeViewColumn('IP', gtk.CellRendererText(), text=1))
        self.tree.append_column(gtk.TreeViewColumn('Time', gtk.CellRendererText(), text=2))

        sw.add(self.tree)

        self.pack_start(sw)
        self.show_all()

    def __on_trace(self, action):
        self.toolbar.set_sensitive(False)
        self.store.clear()

        self.store.append([0, _("Tracing..."), ""])

        thread = Thread(target=self.__do_trace)
        thread.setDaemon(True)

        thread.start()

    def __do_trace(self):
        try:
            dport = self.dport.get_value_as_int()
            maxttl = self.maxttl.get_value_as_int()
            timeout = self.timeout.get_value_as_int()
            target = self.target.get_text()

            log.debug("Starting %s (%s, dport=%d, maxttl=%d, timeout=%d)" %
                      (traceroute, target, dport, maxttl, timeout))

            ans, unans = traceroute(target, dport, maxttl=maxttl,
                                    timeout=timeout, verbose=False)

            self.session.context.set_trace(ans, unans)
            gobject.idle_add(self.session.reload)

        except Exception, err:
            self.session.context.set_trace(None, err)
            gobject.idle_add(self.session.reload)

            log.error("Exception in tracert:")
            log.error(generate_traceback())
        finally:
            self.toolbar.set_sensitive(True)

    def populate(self):
        ret = self.session.context.data

        if ret is None or len(ret) != 2 or not isinstance(ret, list):
            return
        
        if ret[0] is None and isinstance(ret[1], Exception):
            self.store.clear()
            self.store.append([0, str(ret[1]), ""])
            return

        if not hasattr(ret[0], '__iter__') or \
           not hasattr(ret[1], '__iter__'):
            log.debug("Not a valid trace")
            return

        self.store.clear()

        for i in ret[0]:
            self.store.append([i[0].ttl, i[1].src, "%.3f" % (i[1].time - i[0].time)])

class TracerouteMap(Perspective):
    icon = gtk.STOCK_INFO
    title = _('Visual traceroute')

    def create_ui(self):
        self.webview = webkit.WebView()
        
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.webview)

        self.pack_start(sw)

        self.show_all()

    def create_map(self):
        log.debug("Trying to create a valid map")

        ret = self.session.context.data

        if ret is None or len(ret) != 2 or \
           not isinstance(ret, list) or \
           not hasattr(ret[0], '__iter__') or \
           not hasattr(ret[1], '__iter__'):

            self.webview.load_string("", "text/html", "iso-8859-15", "about:blank")
            return

        try:
            global glocator

            map = tracert.create_map(ret[0])
            self.webview.load_string(map, "text/html", "iso-8859-15", "file:///")

            log.info("Plotted")
        except Exception, err:
            log.error("Error while plotting")
            log.error(generate_traceback())

            self.webview.load_string("", "text/html", "iso-8859-15", "about:blank")

class TracerouteContext(StaticContext):
    def __init__(self, fname=None):
        StaticContext.__init__(self, 'Traceroute', fname)
        self.status = self.SAVED

    def set_trace(self, ans, unans):
        self.set_data([ans, unans])

class TracerouteSession(Session):
    session_name = "TRACEROUTE"
    session_menu = "Traceroute"
    session_orientation = gtk.ORIENTATION_HORIZONTAL

    def create_ui(self):
        self.trace_page = self.add_perspective(Traceroute, True,
                                               True, False)
        self.map_page = self.add_perspective(TracerouteMap, False,
                                             True, False)

        self.reload()
        self.pack_start(self.paned)
        self.show_all()

    def reload_editor(self):
        self.map_page.create_map()
    
    def reload_container(self, packet=None):
        self.trace_page.populate()

class TraceroutePlugin(Plugin):
    def start(self, reader):
        if reader:
            catalog = reader.bind_translation("traceroute")

            if catalog:
                global _
                _ = catalog.gettext

            ret = reader.extract_file('data/GeoLiteCity.dat')

            tracert.glocator = tracert.Locator(os.path.dirname(ret))

        id = PMApp().main_window.register_session(TracerouteSession,
                                                  TracerouteContext)
        log.debug("Traceroute session binded with id %d" % id)

__plugins__ = [TraceroutePlugin]
