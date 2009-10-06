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

import gtk, gobject

from umit.pm import backend
from umit.pm.backend import StaticContext
from umit.pm.core.logger import log
from umit.pm.gui.core.app import PMApp
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.gui.sessions.base import Session
from umit.pm.gui.widgets.interfaces import InterfacesCombo
from umit.pm.gui.pages.base import Perspective
from umit.pm.core.errors import PMErrorException
from umit.pm.manager.preferencemanager import Prefs
from umit.pm.higwidgets.higdialogs import HIGAlertDialog
from umit.pm.gui.sessions import SessionType

from chart import Chart

if Prefs()['backend.system'].value.lower() != 'scapy':
    raise PMErrorException("I need scapy to work!")

_ = str
glocator = None

class MSC(Perspective):
    icon = gtk.STOCK_INFO
    title = _('MSC')

    def create_ui(self):
        
        self.chart = Chart(self.session)
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        

        self.pcap_button = gtk.Action(None, None, _('Open Pcap'), gtk.STOCK_OPEN)
        self.png_button = gtk.Action(None, None, _('Save as png'), gtk.STOCK_SAVE)
        self.svg_button= gtk.Action(None, None, _('Save as svg'), gtk.STOCK_SAVE_AS)
        self.reload_button= gtk.Action(None, None, _('Reload'), gtk.STOCK_REFRESH)
        self.stop_button= gtk.Action(None, None, _('Stop'), gtk.STOCK_MEDIA_STOP)
        #self.sniff_button= gtk.Action(None, None, _('Start Drawing'), gtk.STOCK_MEDIA_PLAY)
        self.zoom_in_button= gtk.Action(None, None, _('Zoom in'), gtk.STOCK_ZOOM_IN)        
        self.zoom_out_button= gtk.Action(None, None, _('Zoom out'), gtk.STOCK_ZOOM_OUT)
        #self.filter_pack = gtk.Entry()
        
        #self.intf_combo = InterfacesCombo()
        #self.item = gtk.ToolItem()
        #self.item.add(self.intf_combo)


        self.toolbar.insert(self.pcap_button.create_tool_item(), -1)
        self.toolbar.insert(self.png_button.create_tool_item(), -1)
        self.toolbar.insert(self.svg_button.create_tool_item(), -1)
        #self.toolbar.insert(self.reload_button.create_tool_item(), -1)
        #self.toolbar.insert(self.stop_button.create_tool_item(), -1)
        #self.toolbar.insert(self.item, -1)
        #self.toolbar.insert(self.sniff_button.create_tool_item(), -1)
        self.toolbar.insert(self.zoom_out_button.create_tool_item(), -1)
        self.toolbar.insert(self.zoom_in_button.create_tool_item(), -1)        

        #self.sniff_button.connect('activate', self.__on_run)
        self.reload_button.connect('activate', self.__on_reload)
        self.stop_button.connect('activate', self.__on_stop)
        self.zoom_in_button.connect('activate', self.__zoom_in)
        self.zoom_out_button.connect('activate', self.__zoom_out)
        self.png_button.connect('activate', self.__save_as_png)  
        self.pcap_button.connect('activate', self.__open_pcap)  
        
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_ALWAYS)
        sw.set_shadow_type(gtk.SHADOW_NONE)
        sw.add_with_viewport(self.chart)
        #self.chart.connect('focus_in_event', self.__focus_in, sw.get_vadjustment())
        
        #self.session.editor_cbs.append(self.repopulate)
        
        self.pack_start(self.toolbar, False, False)
        self.pack_start(sw)
     
        self.show_all()
        
        # Register the lock/unlock callback
        self.session.context.lock_callback = \
            lambda: self.toolbar.set_sensitive(False)
        self.session.context.unlock_callback = \
            lambda: self.toolbar.set_sensitive(True)
        
        
    #def __dummy (self):
        #print len(self.session.context.data)
        #return True
    
    def __open_pcap(self, action):
        types = {}
        sessions = (backend.StaticContext,
                    backend.SequenceContext,
                    backend.SniffContext)

        for ctx in sessions:
            for name, pattern in ctx.file_types:
                types[pattern] = (name, ctx)

        dialog = gtk.FileChooserDialog(_("Select a session"), PMApp().main_window,
                               buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))
        #dialog.set_transient_for(self)

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
                #self.open_generic_file_async(fname)
                s =  StaticContext("Load Pcap", fname, False);
                s.load()
                self.chart.scan_from_list(s.data)
                
        dialog.hide()
        dialog.destroy()
        
    

    def __save_as_png(self, action):
        dialog = gtk.FileChooserDialog(_('Save as png'), PMApp().main_window,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT,
                                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        xfilter = gtk.FileFilter()
        xfilter.add_pattern('*.png')
        xfilter.add_mime_type('image/png')
        xfilter.set_name('PNG Image')

        dialog.add_filter(xfilter)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            filename = dialog.get_filename()
            print filename
            self.chart.save_as(filename)
        else:
            print "No file selected"
        dialog.hide()
        dialog.destroy()
        
    def __on_stop(self, action):
        self.chart.stop_sniffing()
        
    def __on_reload(self, action):
        self.chart.redraw(self.intf_combo.get_interface())
    
    def __zoom_in(self, action):
        self.chart.zoom_in()
        
    def __zoom_out(self, action):
        self.chart.zoom_out()
    
    def __focus_in(widget, event, adj):
        alloc = widget.get_allocation()        
        if alloc.y < adj.value or alloc.y > adj.value + adj.page_size:
            adj.set_value(min(alloc.y, adj.upper-adj.page_size))


#class MSCContext(StaticContext):
    #def __init__(self, fname=None):
        #StaticContext.__init__(self, 'MSC', fname)
        #self.status = self.SAVED

        #self.lock_callback = None
        #self.unlock_callback = None

    #def set_trace(self, ans, unans):
        #self.set_data([ans, unans])

    #def lock(self):
        #if callable(self.lock_callback):
            #self.lock_callback()

    #def unlock(self):
        #if callable(self.unlock_callback):
            #self.unlock_callback()
    
class MSCSession(Session):
    session_name = "MSC"
    session_menu = "MSC"
    session_orientation = gtk.ORIENTATION_HORIZONTAL

    def create_ui(self):
        self.msc_page = self.add_perspective(MSC, False, True)

        self.reload()
        self.pack_start(self.paned)
        self.show_all()

    
    def reload_container(self, packet=None):
        pass


class MSCPlugin(Plugin):
    def start(self, reader):
        if reader:
            catalog = reader.bind_translation("msc")

            if catalog:
                global _
                _ = catalog.gettext

        PMApp().main_window.bind_session(SessionType.SNIFF_SESSION, MSC)


    def stop(self):
        PMApp().main_window.bind_session(SessionType.SNIFF_SESSION, MSC)
        

__plugins__ = [MSCPlugin]




