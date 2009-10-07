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

from umit.pm.gui.core.app import PMApp
from umit.pm.core.i18n import _

from prefmanager import MSCPrefManager



class MSCPreferenceDialog(gtk.Dialog):
    
    def __init__(self):
        super(MSCPreferenceDialog, self).__init__(
            _('Preferences - MSC'), PMApp().main_window,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE,
             gtk.STOCK_APPLY, gtk.RESPONSE_APPLY,
             gtk.STOCK_OK, gtk.RESPONSE_OK)
        )
        self.set_resizable(False)
        
        self.store = gtk.ListStore(str, str)
        self.tree = gtk.TreeView(self.store)

        self.tree.append_column(
            gtk.TreeViewColumn('', gtk.CellRendererPixbuf(), stock_id=0))

        self.tree.append_column(
            gtk.TreeViewColumn('', gtk.CellRendererText(), text=1))

        self.tree.set_headers_visible(False)
        self.tree.set_rules_hint(True)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.tree)

        hbox = gtk.HBox(False, 2)
        hbox.pack_start(sw, False, False)

        self.notebook = gtk.Notebook()
        self.notebook.set_show_border(False)
        self.notebook.set_show_tabs(False)
        hbox.pack_end(self.notebook)

        self.store.append([gtk.STOCK_DND_MULTIPLE, "Filter"])

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_NONE)
        

        self.filter_page = FilterView()
        
        sw.add_with_viewport(self.filter_page)

        sw.set_size_request(-1, 200)

        self.notebook.append_page(sw)

        hbox.show_all()

        self.vbox.pack_start(hbox)
        self.vbox.set_border_width(4)
        self.vbox.set_spacing(6)
        self.connect('response', self.__on_response)
        
    def __on_response(self, dialog, id):
        if  id == gtk.RESPONSE_CLOSE:
            self.close()
        elif id == gtk.RESPONSE_APPLY:
            self.__apply_changes
        elif id == gtk.RESPONSE_OK:
            self.__apply_changes
            self.close()
            
    def __apply_changes(self):
        pass
        

class FilterView(gtk.VBox):
    
    def __init__(self):
        super(FilterView, self).__init__(False, 0)
        self.filter_check = gtk.CheckButton(_("_Enable Filter"), True)  
        self.add(self.filter_check)
        
        self.n_filters_enabled = 1

        vbox = gtk.VBox(True,0)        
        frame = gtk.Frame(None)
        frame.add(vbox)
        
        
        
        self.filter_button = []
        self.filter_src = []
        self.filter_type = []
        self.filter_dest = []
        
        for i in range(0,4):
            hb = gtk.HBox(False, 0)
            self.filter_button.append(gtk.CheckButton(None, None))
            self.filter_src.append(gtk.Entry(15))
            self.filter_src[i].set_text(_("Source"))
            self.filter_type.append(gtk.Entry(5))
            self.filter_type[i].set_text(_("Type"))
            self.filter_dest.append(gtk.Entry(15))  
            self.filter_dest[i].set_text(_("Destination"))
            hb.add(self.filter_button[i])
            hb.add(self.filter_src[i])
            hb.add(self.filter_type[i])
            hb.add(self.filter_dest[i])
            vbox.add(hb)
        

        for i in range(self.n_filters_enabled, 4):
            self.filter_src[i].set_sensitive(False)
            self.filter_type[i].set_sensitive(False)
            self.filter_dest[i].set_sensitive(False)
            
        self.add(frame)
        
        self.filter_check.connect("toggled", self.__on_filter_toggle)
        
    
        

    def __on_filter_toggle(self, togglebutton):
        print self.filter_check.get_active()
        print self.n_filters_enabled     
        if not self.filter_check.get_active() :
            for i in range(0,4):
                self.filter_src[i].set_sensitive(False)
                self.filter_type[i].set_sensitive(False)
                self.filter_dest[i].set_sensitive(False)
                
        else :
            for i in range(0,self.n_filters_enabled):
                self.filter_src[i].set_sensitive(True)
                self.filter_type[i].set_sensitive(True)
                self.filter_dest[i].set_sensitive(True) 
            for i in range(self.n_filters_enabled, 4):
                self.filter_src[i].set_sensitive(False)
                self.filter_type[i].set_sensitive(False)
                self.filter_dest[i].set_sensitive(False)
            

        
        

