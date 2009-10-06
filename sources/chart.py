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


from umit.pm import backend
from umit.pm.gui.widgets.interfaces import InterfacesCombo
from umit.pm.backend import StaticContext


import scapy.all
from datetime import datetime

"""
This module contains common classes for the chart drawing
"""

class Chart(gtk.DrawingArea):
    """
    Creates the Message Sequence Chart
    """
    __gtype_name__ = "Chart"
    

    def __init__(self, session):
        
        super(Chart, self).__init__()
        self.connect('expose_event', self.do_expose_event)
        self.sniff_context = session.context
        self.sniff_context.callback = self.update_drawing_clbk
        self.scalingfactor = 10
        self.max_nodes = 6
        self.max_packets = 50
        self.left_margin = 180
        self.time_margin = 30
        self.right_margin = 100
        self.bottom_margin = 50
        self.top_margin = 50
        self.hsize = 1000
        self.vsize = 1500
        self.set_size_request(self.hsize, self.vsize)
        self.__init_vars()
        

        #Assuming that the button ordering is as follows:
            #('Restart capturing'),
            #('Stop capturing'),
            #('Reorder flow')

        session.sniff_page.toolbar.get_nth_item(0).connect('clicked', self.redraw)
        session.sniff_page.toolbar.get_nth_item(1).connect('clicked', self.stop_sniffing)

    def __init_vars(self):
        
        self.IPs = []
        self.Packets = []
        self.start_time = datetime.now()
        self.sniffing_frozen = False
        self.timeout = gobject.timeout_add(300, self.__check_for_packets)
        #add host IP
        #TODO: Need to find a way of finding the IP without using scapy
        for x in scapy.all.conf.route.routes:
            if x[2] != '0.0.0.0':
                self.IPs.append(x[4])
              
        
    def scan_from_list(self, list):
        self.IPs = []
        self.Packets = []
        self.start_time = list[0].get_datetime()
        for packet in list:
            self.update_drawing_clbk(packet)
        self.queue_draw()
            
   
    def do_expose_event(self, widget, evt):
        self.cr = self.window.cairo_create()
        self.__cairo_draw()
        return gtk.DrawingArea.do_expose_event

    def __cairo_draw(self, cr = None):
        if cr == None :
            cr = self.cr
        cr.save()
                
        vline_positions = []
        
        #set background
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(0, 0, *self.window.get_size())
        cr.fill()
        
        if len(self.IPs) == 1 :
            cr.restore()
            return
        
        #draw IPs
        cr.select_font_face("Arial",
                cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(14)
        i=0
        margin = self.left_margin
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.move_to(margin-10, self.top_margin)
        cr.line_to(margin-10, self.window.get_size()[1]-self.bottom_margin)
        cr.stroke()
        for ip in self.IPs:
            cr.set_source_rgb(0.0, 0.0, 0.0)
            x_bearing, y_bearing, width, height = cr.text_extents(ip)[:4]
            cr.move_to(margin, self.top_margin-height)
            cr.show_text(ip)
            cr.move_to(margin+width/2, self.top_margin)
            cr.line_to(margin+width/2, self.window.get_size()[1]-self.bottom_margin)
            vline_positions.append(margin+width/2)
            cr.stroke()
            margin = margin+width+20
            i=i+1
            
        
        #draw packets   
        prev_timestamp_lower = 0
        cr.set_source_rgb(0.5, 0.5, 0.5)
        for packet in self.Packets:
            time_passed = self.__get_time_passed(packet.get_datetime())
            cur_packet_ypos = self.__get_time_passed(packet.get_datetime())/self.scalingfactor\
                            + self.top_margin
            #Draw if the packet drawing does not cross the lower bound of the drawingArea
            if cur_packet_ypos < self.window.get_size()[1]-self.bottom_margin :
                x_bearing, y_bearing, width, height = cr.text_extents(str(time_passed) + "ms")[:4]  
                
                #Draw the text if it doesnt clash with the previous timestamp text
                if prev_timestamp_lower < cur_packet_ypos - height:
                    cr.move_to(self.time_margin, cur_packet_ypos)
                    cr.show_text(str(self.__get_time_passed(packet.get_datetime())) + "ms")
                
                #Draw a small marker on the time axis
                cr.move_to(self.left_margin-13, cur_packet_ypos-height/2)
                cr.line_to(self.left_margin-7, cur_packet_ypos-height/2)                
                prev_timestamp_lower = cur_packet_ypos
                cr.stroke()
                
                #Draw the arrow from source to destination
                cr.select_font_face("Arial",\
                    cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                cr.set_font_size(14)
                cr.move_to(vline_positions[self.IPs.index(packet.get_source())], cur_packet_ypos-height/2)
                cr.line_to(vline_positions[self.IPs.index(packet.get_dest())], cur_packet_ypos-height/2)
                if self.IPs.index(packet.get_source()) > self.IPs.index(packet.get_dest()):
                    cr.line_to(vline_positions[self.IPs.index(packet.get_dest())], cur_packet_ypos-height/2+cr.text_extents("<")[3]/2)
                    cr.show_text("<")
                else:
                    cr.line_to(vline_positions[self.IPs.index(packet.get_dest())] - cr.text_extents("<")[2], cur_packet_ypos-height/2+cr.text_extents("<")[3]/2)
                    cr.show_text(">")
                cr.stroke()
            elif not self.sniffing_frozen:
                self.sniffing_frozen =True
                print "Area overflow"
                break
            
        cr.restore()


    def redraw(self, toolbutton):
        self.__init_vars()
        
    def stop_sniffing(self, toolbutton):
        self.sniffing_frozen = True
    
    def update_drawing_clbk(self, packet, udata= None):
        if self.sniffing_frozen:
            return
        self.__add_node_to_list(packet.get_source())
        self.__add_node_to_list(packet.get_dest())   
        if(self.IPs.count(packet.get_source()) >=1 and self.IPs.count(packet.get_dest()) >=1 \
           and len(self.Packets) <= self.max_packets and self.__get_time_passed(packet.get_datetime()) >=0):
            self.Packets.append(packet)
            print str(self.__get_time_passed(packet.get_datetime())) + "ms :: "  + \
                packet.get_source() + "-->" + packet.get_dest()
        if len(self.Packets) > self.max_packets and not self.sniffing_frozen:
            print "Packets exceded"
            self.sniffing_frozen = True
        
    def __add_node_to_list(self, address):
        #Add only IP addresses
        if(address == "N/A" or address.find(":") != -1 or len(self.IPs) >= self.max_nodes):
            #TODO: Find a better way instead of hard-coding the bound on the number of nodes
            return None
        try:
            x = self.IPs.index(address)
        except ValueError:
            self.IPs.append(address)   
            print "(NEW): " + address


    def __check_for_packets(self):
        self.sniff_context.check_finished()
        self.queue_draw()
        if self.sniffing_frozen :
            print "Sniffing Stopped"
            return False
        return True


    def __get_time_passed(self, this_time):
        #print (str((this_time.microsecond - self.start_time.microsecond)) + ":" +str((this_time.second-self.start_time.second)*1000000)  +":" +str((this_time.minute-self.start_time.minute)*60*1000000))
        return (float((this_time.microsecond - self.start_time.microsecond)) + \
                (this_time.second - self.start_time.second)*1000000 + \
                (this_time.minute - self.start_time.minute)*60*1000000)/1000
    
    def zoom_in (self):
        if self.scalingfactor == 1:
            self.scalingfactor = float(self.scalingfactor/2)
        else:
            self.scalingfactor = self.scalingfactor - 1
        self.queue_draw()
        
    def save_as (self, filename):
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, *self.window.get_size()) 
        cr = cairo.Context(surface)
        self.__cairo_draw(cr)
        surface.write_to_png(filename)

    def zoom_out (self):
        self.scalingfactor = self.scalingfactor + 1
        self.queue_draw()