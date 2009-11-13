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
import re

from umit.pm.gui.core.app import PMApp
from umit.pm.core.i18n import _

from prefmanager import MSCPrefManager
from filter import Tokenizer




class MSCPreferenceDialog(gtk.Dialog):
    
    
    def __init__(self, chart):
        super(MSCPreferenceDialog, self).__init__(
            _('Preferences - MSC'), PMApp().main_window,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE,
             gtk.STOCK_APPLY, gtk.RESPONSE_APPLY,
             gtk.STOCK_OK, gtk.RESPONSE_OK)
        )
        self.set_resizable(False)
        self.chart = chart
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
        i =0 
        print self.chart.filters
        for f in  self.chart.filters:
            self.filter_page.filter_strings[i].set_text(f)
            i = i+1
        sw.add_with_viewport(self.filter_page)

        sw.set_size_request(400, 200)

        self.notebook.append_page(sw)

        hbox.show_all()

        self.vbox.pack_start(hbox)
        self.vbox.set_border_width(4)
        self.vbox.set_spacing(6)
        self.connect('response', self.__on_response)
        
    def __on_response(self, dialog, id):
        if  id == gtk.RESPONSE_CLOSE:
            self.hide()
            self.destroy()
        elif id == gtk.RESPONSE_APPLY:
            pass
            self.__apply_changes()
        elif id == gtk.RESPONSE_OK:
            self.__apply_changes()
            self.hide()
            self.destroy()


            
            
    def __apply_changes(self):
        self.chart.filters = []
        self.chart.filter_ips = []
        for i in range(0,4):
            filter_text = self.filter_page.filter_strings[i].get_text()
            if filter_text == '':
                break
            else:
                g = Tokenizer(filter_text)
                tok = 'NULL'
                while not tok == '':
                    tok = g.next()
                    if not re.match( '([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', tok) == None :
                        print tok
                        self.chart.filter_ips.append(tok)
                self.chart.filters.append(filter_text)
                print  filter_text
            
   

class FilterView(gtk.VBox):
    
     
    def __init__(self):
        super(FilterView, self).__init__(False, 0)
        
        vbox = gtk.VBox(True,0)        
        frame = gtk.Frame(None)
        frame.add(vbox)
        
        
        
        self.filter_strings = []

        
        for i in range(0,4):
            hb = gtk.HBox(False, 0)
            self.filter_strings.append(gtk.Entry(100))
            hb.add(self.filter_strings[i])

            vbox.add(hb)
            
         

            
        self.add(frame)
        
  
    
    
    
