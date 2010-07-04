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
#from umit.pm.gui.pages.packetpage import packetpage
from umit.pm.core.errors import PMErrorException
from umit.pm.manager.preferencemanager import Prefs
from umit.pm.higwidgets.higdialogs import HIGAlertDialog
from umit.pm.gui.sessions import SessionType

from chart import Chart
from preferences import MSCPreferenceDialog

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
        self.filter_button = gtk.Action(None, None, _('Sequential Filter'),gtk.STOCK_PREFERENCES)
        self.zoom_in_button= gtk.Action(None, None, _('Zoom in'), gtk.STOCK_ZOOM_IN)        
        self.zoom_out_button= gtk.Action(None, None, _('Zoom out'), gtk.STOCK_ZOOM_OUT)
        self.fullscreen_button= gtk.Action(None, None, _('fullscreen'), gtk.STOCK_FULLSCREEN)
        self.time_diff_button=gtk.Action(None, None, _('Time scaling'), gtk.STOCK_JUMP_TO)


        self.toolbar.insert(self.pcap_button.create_tool_item(), -1)
        self.toolbar.insert(self.png_button.create_tool_item(), -1)
        self.toolbar.insert(self.svg_button.create_tool_item(), -1)
        self.toolbar.insert(self.filter_button.create_tool_item(), -1)

        self.toolbar.insert(self.zoom_out_button.create_tool_item(), -1)
        self.toolbar.insert(self.zoom_in_button.create_tool_item(), -1)
        self.toolbar.insert(self.time_diff_button.create_tool_item(),-1)  
        self.toolbar.insert(self.fullscreen_button.create_tool_item(), -1)      
        

        self.zoom_in_button.connect('activate', self.__zoom_in)
        self.filter_button.connect('activate', self.__open_prefs)
        self.zoom_out_button.connect('activate', self.__zoom_out)
        self.png_button.connect('activate', self.__save_as_png)  
        self.pcap_button.connect('activate', self.__open_pcap)
        self.fullscreen_button.connect('activate', self.__create_fullscreen)
        self.time_diff_button.connect('activate', self.__time_diff_change)
	
        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_ALWAYS)
        self.sw.set_shadow_type(gtk.SHADOW_NONE)
        self.sw.add_with_viewport(self.chart)
	
	self.box = gtk.VBox()
        self.btn_fullscreen = gtk.Button()
        self.btn_fullscreen.set_label("FullScreen Mode")
        self.sw.add(self.box)
	self.box.pack_start(self.toolbar, False, False)
        self.box.pack_start(self.sw)
	self.pack_start(self.box)
	     
        self.show_all()
        
        # Register the lock/unlock callback
        self.session.context.lock_callback = \
            lambda: self.toolbar.set_sensitive(False)
        self.session.context.unlock_callback = \
            lambda: self.toolbar.set_sensitive(True)
        
        
    
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
        
   
    def __open_prefs(self, action):
        
        dialog = MSCPreferenceDialog(self.chart)
        dialog.set_transient_for(PMApp().main_window)
        dialog.show()
        
    
    def __zoom_in(self, action):
        self.chart.zoom_in()
        
    def __zoom_out(self, action):
        self.chart.zoom_out()
    
    def __focus_in(widget, event, adj):
        alloc = widget.get_allocation()        
        if alloc.y < adj.value or alloc.y > adj.value + adj.page_size:
            adj.set_value(min(alloc.y, adj.upper-adj.page_size))

    def __time_diff_change(self, action):
	self.chart.set_time_diff()
	

    def __create_fullscreen(self, widget=None):
        print ".."
	if self.get_children() != []:
	    self.remove(self.get_children()[0])
	self.fullscreen_button.set_visible(False)
        self.box_full = gtk.VBox()
        
        self.btn_fullscreen2 = gtk.Button()
	self.set_size_request(96,36)
        self.btn_fullscreen2.set_label("Leave FullScreen Mode")
        self.btn_fullscreen2.connect("clicked", self.__fullscreen_exit)
        
        self.__fullscreen_window = gtk.Window()
        
            
        self.box_full.pack_start(self.box)
	self.box_full.pack_start(self.btn_fullscreen2,False)
	
        self.box.show()
	self.box_full.show()
        self.btn_fullscreen2.show()

        self.__fullscreen_window.add(self.box_full)
        self.__fullscreen_window.connect('delete-event', self.__fullscreen_exit)
        self.__fullscreen_window.show()
        self.__fullscreen_window.fullscreen()

        
        
    def __fullscreen_exit(self, widget):
        self.__fullscreen_window.hide()
        if self.box_full.get_children() != []:
	    self.box_full.remove(self.box_full.get_children()[0])
	self.fullscreen_button.set_visible(True)    
	self.pack_start(self.box, True)    
	self.box.show()
	self.show_all()
        
        
        
    
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




