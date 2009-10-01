#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
#
# Author: Luís A. Bastião Silva <luis.kop@gmail.com>
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
import pango

from umit.pm.core.logger import log

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.plugins.engine import Plugin

from umit.pm.gui.sessions import SessionType
from umit.pm.gui.pages.base import Perspective

from umit.pm.core.errors import PMErrorException



import cairo
import math
import random 
from gtkcairoplot import *

import gobject



# FIXME
#  * Why the hell if I click on expander of plugin it just goes off?
#  * ?

# TODO
#  * Bar graphs 
#  * Percentage of plotters
#  * Make a table 
#  * Run in fullscreen mode or also in another tab, whatever
#  * Add support to save graphs to png, jpg wtv.
# `* ? 




class Stats(Perspective):
    title = 'Network Monitoring Statistics'

    def create_ui(self):
        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        
        self.box = gtk.HBox()
        self.sw.add(self.box)
        self.pack_start(self.sw)
        self.show_all()
        
        # Define the callback to update plot
        timeout_id = gobject.timeout_add(1000, self._update_plot)
    
    def _update_plot(self):
        # If sniffer is stoped it keep also verifying in the case 
        # of restart sniifer again
        if self.session.context.state == self.session.context.NOT_RUNNING:
            timeout_id = gobject.timeout_add(1000, self._update_plot)
            return

       
        # See this objects? it's really important to understand the classes of them
        # self.session
        # self.session.context 

        # Retrieve all packets of session  # TODO Why get_data is not working? 
        # get_all_data() is dirty workaround for this case I guess.
        list_packets = self.session.context.get_all_data()

        protos = {} # Dic of protocols: {'ARP': 30, 'ICMP':20, Key:Value} 
        for packet in list_packets:
            _proto = packet.get_protocol_str()
            try:
                
                # Increment in dic
                protos[_proto] += 1 


            except:
                # Protocol doesn't not exists on the list, so let's add it
                protos[_proto] = 1 
        
        self.plot(protos, "donut") 

        # XXX Stupidness? Not the first time :)
        #if self.session.context.state == self.session.context.RUNNING:
        timeout_id = gobject.timeout_add(1000, self._update_plot)



    def plot(self, data, type):
        """
        Plot the graph - factory
        @data: 
        @type: (donut, bars, etc)
        """
        if type == "donut":
            self.__plot_donut(data)


    def __plot_donut(self, data):

        #Define a new backgrond
        background = cairo.LinearGradient(300, 0, 300, 400)
        background.add_color_stop_rgb(0,0.4,0.4,0.4)
        background.add_color_stop_rgb(1.0,0.1,0.1,0.1)

        donut = gtk_donut_plot()
        
        #Default plot, gradient and shadow, different background
        donut.set_args({'data':data, 'width':600, 'height':400, 'inner_radius':0.3})
        donut.show()
        if self.box.get_children() != []:
            self.box.remove(self.box.get_children()[0])
        self.box.pack_start(donut)
        self.box.show()

class plotstats(Plugin):
    
    def start(self, reader):
        PMApp().main_window.bind_session(SessionType.SNIFF_SESSION, Stats)

    def stop(self):
        PMApp().main_window.unbind_session(SessionType.SNIFF_SESSION, Stats)

__plugins__ = [plotstats]

