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
    
    #def __init__(self):
        #super(MSCPreferenceDialog, self).__init__(
            #_('Preferences - MSC'), PMApp().main_window,
            #gtk.DIALOG_DESTROY_WITH_PARENT,
            #(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE,
             #gtk.STOCK_APPLY, gtk.RESPONSE_APPLY,
             #gtk.STOCK_OK, gtk.RESPONSE_OK)
        #)
        #self.set_resizable(False)
        #vbox = gtk.VBox(True, 0)
        #self.filters = []
        #for i in range(0,5):
            #self.filters.append(gtk.Entry(25))
            #vbox.add(self.filters[i])
        #vbox.show_all()
        #self.add(vbox)
        #self.connect('response', self.__on_response)
    
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
        for i in range(0,4):
            filter_text = self.filter_page.filter_strings[i].get_text()
            if filter_text == '':
                break
            else:
                self.chart.filters.append(filter_text)
                print  filter_text
            
   
    #def __apply_changes(self):
        #for i in range(0,self.filter_page.n_filters_enabled):
            #if self.__validate_src(self.filter_page.filter_sources[i].get_text()):
                #MSCPrefManager().set_option('filter.'+str(i)+'.src',  self.filter_page.filter_sources[i].get_text())
            #if self.__validate_type(self.filter_page.filter_types[i].get_text()):
                #MSCPrefManager().set_option('filter.'+str(i)+'.type',  self.filter_page.filter_types[i].get_text())
            #if self.__validate_dest(self.filter_page.filter_dests[i].get_text()):
                #MSCPrefManager().set_option('filter.'+str(i)+'.dest',  self.filter_page.filter_dests[i].get_text())
        #try:
            #MSCPrefManager().write_options()
        #except Exception, err:
            #print err
            #pass      
        
        
    #def __validate_src(self, value):
        #if value != 'Source':
            #return True
        #return False
        
        
    #def __validate_type(self, value):
        #if value != 'Type':
            #return True
        #return False
        
    #def __validate_dest(self, value):
        #if value != 'Destination':
            #return True
        #return False

class FilterView(gtk.VBox):
    
     
    def __init__(self):
        super(FilterView, self).__init__(False, 0)
        
        vbox = gtk.VBox(True,0)        
        frame = gtk.Frame(None)
        frame.add(vbox)
        
        
        
        self.filter_strings = []

        
        for i in range(0,4):
            hb = gtk.HBox(False, 0)
            self.filter_strings.append(gtk.Entry(50))
            hb.add(self.filter_strings[i])

            vbox.add(hb)
            
         

            
        self.add(frame)
        
  
    
    
    
    #def __init__(self):
        #super(FilterView, self).__init__(False, 0)
        #self.filter_en_check = gtk.CheckButton(_("_Enable Filter"), True)  
        #self.add(self.filter_en_check)
        
        #self.n_filters_enabled = 0

        #vbox = gtk.VBox(True,0)        
        #frame = gtk.Frame(None)
        #frame.add(vbox)
        
        
        
        #self.filter_buttons = []
        #self.filter_sources = []
        #self.filter_types = []
        #self.filter_dests = []
        
        #for i in range(0,4):
            #hb = gtk.HBox(False, 0)
            #self.filter_buttons.append(gtk.CheckButton(None, None))
            #self.filter_sources.append(gtk.Entry(15))
            #self.filter_types.append(gtk.Entry(5))
            #self.filter_dests.append(gtk.Entry(15))  
            #hb.add(self.filter_buttons[i])
            #hb.add(self.filter_sources[i])
            #hb.add(self.filter_types[i])
            #hb.add(self.filter_dests[i])
            #vbox.add(hb)
            
            
        #for i in range(0,4):
            #if (MSCPrefManager()['filter.'+str(i)+'src'].value == '' and
                #MSCPrefManager()['filter.'+str(i)+'type'].value == '' and
                #MSCPrefManager()['filter.'+str(i)+'dest'].value == '' ):
                #self.n_filters_enabled = i
                #break
            #self.filter_sources[i].set_text(MSCPrefManager()['filter.'+str(i)+'src'].value)
            #self.filter_types[i].set_text(MSCPrefManager()['filter.'+str(i)+'type'].value)
            #self.filter_dests[i].set_text(MSCPrefManager()['filter.'+str(i)+'dest'].value) 
            
        #if self.n_filters_enabled == 0:
            #self.filter_en_check.set_active(False)
            

        #for i in range(self.n_filters_enabled, 4):
            #self.filter_sources[i].set_text(_('Source'))
            #self.filter_types[i].set_text(_('Type'))
            #self.filter_dests[i].set_text(_('Destination'))
            #self.filter_sources[i].set_sensitive(False)
            #self.filter_types[i].set_sensitive(False)
            #self.filter_dests[i].set_sensitive(False)
            
        #self.add(frame)
        
        #self.filter_en_check.connect("toggled", self.__on__filter_en_toggle)
        
        #for i in range(0, 4):
            #self.filter_buttons[i].connect("toggled", self.__on_filter_toggle, i)
            
    
    #def __on_filter_toggle(self, togglebutton, index):

        #if togglebutton.get_active() :
            #if index == self.n_filters_enabled:
                #self.n_filters_enabled = self.n_filters_enabled + 1
            #self.filter_dests[index].set_sensitive(True)
            #self.filter_sources[index].set_sensitive(True)
            #self.filter_types[index].set_sensitive(True)
        #else:
            #if index <= self.n_filters_enabled -1:
                #self.n_filters_enabled = index
            #self.filter_sources[i].set_text(_('Source'))
            #self.filter_types[i].set_text(_('Type'))
            #self.filter_dests[i].set_text(_('Destination'))
            #self.filter_dests[i].set_sensitive(False)
            #self.filter_sources[i].set_sensitive(False)
            #self.filter_types[index].set_sensitive(False)            
        #print self.n_filters_enabled 

    #def __on__filter_en_toggle(self, togglebutton):
        #if not togglebutton.get_active() :
            #for i in range(0,4):
                #self.filter_sources[i].set_text(_('Source'))
                #self.filter_types[i].set_text(_('Type'))
                #self.filter_dests[i].set_text(_('Destination'))
                #self.filter_sources[i].set_sensitive(False)
                #self.filter_types[i].set_sensitive(False)
                #self.filter_dests[i].set_sensitive(False)
                
        #else :
            #for i in range(0,self.n_filters_enabled):
                #self.filter_sources[i].set_sensitive(True)
                #self.filter_types[i].set_sensitive(True)
                #self.filter_dests[i].set_sensitive(True) 
            #for i in range(self.n_filters_enabled, 4):
                #self.filter_sources[i].set_text(_('Source'))
                #self.filter_types[i].set_text(_('Type'))
                #self.filter_dests[i].set_text(_('Destination'))
                #self.filter_sources[i].set_sensitive(False)
                #self.filter_types[i].set_sensitive(False)
                #self.filter_dests[i].set_sensitive(False)
            

        
        

