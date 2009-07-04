#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
#
# Author: Abhiram Kasina <abhiram.casina@gmail.com>
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
import cairo
import pango
import gobject
import pangocairo

from PM import Backend
from PM.Core.Atoms import defaultdict

from PM.Backend import StaticContext, traceroute
from PM.Core.Logger import log
from PM.Core.Atoms import generate_traceback

from PM.Gui.Core.App import PMApp
from PM.Gui.Plugins.Engine import Plugin
from PM.Gui.Sessions.Base import Session
from PM.Gui.Widgets.Interfaces import InterfacesCombo

from PM.Gui.Sessions import SessionType
from PM.Gui.Pages.Base import Perspective

from PM.Core.Errors import PMErrorException
from PM.Manager.PreferenceManager import Prefs

from PM.Backend.Scapy.Context import Sniff

from math import pi

if Prefs()['backend.system'].value.lower() != 'scapy':
    raise PMErrorException("I need scapy to work!")

_ = str
glocator = None

class MSC(Perspective):
    icon = gtk.STOCK_INFO
    title = _('MSC')

    def create_ui(self):
        
        self.chart = Chart()
        
        
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        

        self.pcap_button = gtk.Action(None, None, _('Open Pcap'), gtk.STOCK_OPEN)
        self.jpg_button = gtk.Action(None, None, _('Save as svg'), gtk.STOCK_SAVE)
        self.svg_button= gtk.Action(None, None, _('Save as png'), gtk.STOCK_SAVE_AS)
        self.reload_button= gtk.Action(None, None, _('Reload'), gtk.STOCK_REFRESH)
        self.stop_button= gtk.Action(None, None, _('Stop'), gtk.STOCK_MEDIA_STOP)
        self.sniff_button= gtk.Action(None, None, _('Start Drawing'), gtk.STOCK_MEDIA_PLAY)
        self.filter_pack = gtk.Entry()
        
        self.intf_combo = InterfacesCombo()
        self.item = gtk.ToolItem()
        self.item.add(self.intf_combo)


        self.toolbar.insert(self.pcap_button.create_tool_item(), -1)
        self.toolbar.insert(self.jpg_button.create_tool_item(), -1)
        self.toolbar.insert(self.svg_button.create_tool_item(), -1)
        self.toolbar.insert(self.reload_button.create_tool_item(), -1)
        self.toolbar.insert(self.stop_button.create_tool_item(), -1)
        self.toolbar.insert(self.item, -1)
        self.toolbar.insert(self.sniff_button.create_tool_item(), -1)

        self.sniff_button.connect('activate', self.__on_run)
        self.reload_button.connect('activate', self.__on_reload)
        
        self.pack_start(self.toolbar, False, False)
        self.pack_start(self.chart)  

     
        self.show_all()

        # Register the lock/unlock callback
        self.session.context.lock_callback = \
            lambda: self.toolbar.set_sensitive(False)
        self.session.context.unlock_callback = \
            lambda: self.toolbar.set_sensitive(True)
    
    def __on_run(self, action):
        self.chart.redraw(self.intf_combo.get_interface())
        
    def __on_reload(self, action):
        self.chart.update_drawing_clbk(None, None)
        

class MSCContext(StaticContext):
    def __init__(self, fname=None):
        StaticContext.__init__(self, 'MSC', fname)
        self.status = self.SAVED

        self.lock_callback = None
        self.unlock_callback = None

    def set_trace(self, ans, unans):
        self.set_data([ans, unans])

    def lock(self):
        if callable(self.lock_callback):
            self.lock_callback()

    def unlock(self):
        if callable(self.unlock_callback):
            self.unlock_callback()
    
class MSCSession(Session):
    session_name = "MSC"
    session_menu = "MSC"
    session_orientation = gtk.ORIENTATION_HORIZONTAL

    def create_ui(self):
        self.msc_page = self.add_perspective(MSC, True,
                                               True, False)

        self.reload()
        self.pack_start(self.paned)
        self.show_all()

    
    def reload_container(self, packet=None):
        #self.trace_page.populate()
        pass


class MSCPlugin(Plugin):
    def start(self, reader):
        if reader:
            catalog = reader.bind_translation("msc")

            if catalog:
                global _
                _ = catalog.gettext


        id = PMApp().main_window.register_session(MSCSession,
                                                  MSCContext)
        log.debug("MSC session binded with id %d" % id)

    def stop(self):
        pass
        PMApp().main_window.deregister_session(MSCSession)

__plugins__ = [MSCPlugin]




class Chart(gtk.DrawingArea):
    """
    Creates the Message Sequence Chart
    """
    __gtype_name__ = "Chart"

    def __init__(self):
        super(Chart, self).__init__()
        
        
    def do_expose_event(self, evt):
        cr = self.window.cairo_create()
        self.__cairo_draw(cr)
        return True

    def __cairo_draw(self, cr):
        cr.save()
        cr.set_source_rgb(1.0 , 1.0, 1.0)
        cr.rectangle(0, 0, *self.window.get_size())
        cr.fill()
        cr.restore()
        
    def redraw(self, iface):
        self.sniff_context = Backend.SniffContext(iface, None, 0, 0, None, 0, 0, 0, \
                                      True, True, True, False, True, True, \
                                      False, 0, True, self.__update_drawing_clbk, None)
        self.timeout = gobject.timeout_add(300, self.__check_for_packets)
        self.sniff_context._start()
        
    def __update_drawing_clbk(self, packet, udata):
        
        print packet
        # packet is the MetaPacket or may be a list of it 
        
    
        
    def __check_for_packets(self):
        self.sniff_context.check_finished()
        return True

        

