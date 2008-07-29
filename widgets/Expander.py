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

import gtk
import gobject

from higwidgets.higbuttons import HIGArrowButton

class AnimatedExpander(gtk.VBox):
    __gtype_name__ = "AnimatedExpander"
    
    def __init__(self, label=None, image=gtk.STOCK_PROPERTIES):
        super(AnimatedExpander, self).__init__(False, 2)
        
        # What we need is the arrow button a label with markup and
        # optionally a close button :)
        
        self.arrow = HIGArrowButton(gtk.ORIENTATION_VERTICAL)
        self.arrow.set_relief(gtk.RELIEF_NONE)
        self.arrow.connect('clicked', self.__on_toggle)
        
        self._label = gtk.Label()
        self._label.set_alignment(0, 0.5)
        self.label = label
        
        self._image = gtk.Image()
        self.image = image
        
        # The layout part
        self.layout = gtk.Layout()
        self.child = None
        
        self.animating = False
        self.to_show = False
        
        self.speed = 10
        self.current = 0
        self.dest = 0

        self.tot_time = 100
        self.int_time = 5
        
        # Pack all
        hbox = gtk.HBox(False, 2)
        hbox.pack_start(self.arrow, False, False)
        hbox.pack_start(self._image, False, False)
        hbox.pack_start(self._label)
        
        frame = gtk.Frame()
        frame.add(hbox)
        
        self.happy_box = gtk.EventBox()
        self.happy_box.add(frame)
        
        self.pack_start(self.happy_box, False, False)
        self.pack_end(self.layout)
        
        self.show_all()

    def do_realize(self):
        gtk.VBox.do_realize(self)

        bg_color = gtk.gdk.color_parse("#FFFFDC")
        gtk.gdk.colormap_get_system().alloc_color(bg_color)

        self.happy_box.modify_bg(gtk.STATE_NORMAL, bg_color)

    def do_size_allocate(self, allocation):
        ret = gtk.VBox.do_size_allocate(self, allocation)

        if self.child:
            alloc = self.layout.get_allocation()
            w, h = alloc.width, alloc.height
            
            alloc = self.child.get_allocation()

            #if w > alloc.width:
            if w >= self.child.size_request()[0]:
                alloc.width = w
            else:
                alloc.width = self.child.size_request()[0]

            #if h > alloc.height:
            if h >= self.child.size_request()[1]:
                alloc.height = h
            else:
                alloc.height = self.child.size_request()[1]

            self.child.size_allocate(alloc)
            
            if self.animating:
                self.layout.show()
            else:
                if self.to_show:
                    self.layout.show()
                else:
                    self.layout.hide()
        
        return ret

    def add_widget(self, widget, show=False):
        """
        Add a widget to the expander.
        
        @param widget the widget to add
        @param show if the widget should be showed
        """
        
        if self.child:
            raise Exception("Could not add another widget as child.")
        
        self.child = widget
        
        self.layout.put(self.child, 0, 0)
        self.do_size_allocate(self.get_allocation())
        self.set_expanded(show)

    def add(self, widget):
        self.add_widget(widget, True)

    def set_expanded(self, val):
        """
        Show or hide the child widget without animation
        """
        
        if not self.child:
            return
        
        self.arrow.set_active(val)
        self.to_show = val

        if val:
            self.current = 0
            self.layout.move(self.child, 0, self.current)
            self.layout.show()
        else:
            self.layout.hide()
            self.current = self.__get_child_height()
            self.layout.move(self.child, 0, self.current)
        
        if not self.animating:
            self.__set_animating(False)

    def get_label(self):
        return self._label.get_text()

    def set_label(self, txt):
        if not txt:
            txt = ""

        self._label.set_text(txt)
        self._label.set_use_markup(True)

    def __animate_hide(self):
        if self.current > self.dest:
            self.current -= self.speed
            self.layout.move(self.child, 0, self.current)

            return True

        if self.dest < 0:
            self.layout.hide()
        
        self.current = self.__get_child_height()
        self.__set_animating(False)
        self.arrow.set_sensitive(True)
        
        return False

    def __animate_show(self):
        if self.current < 0:
            self.current += self.speed
            self.layout.move(self.child, 0, self.current)

            return True
        
        self.current = 0
        self.layout.move(self.child, 0, 0)
        self.__set_animating(False)
        self.arrow.set_sensitive(True)
        
        return False
    

    def __on_toggle(self, btn):
        if not self.child:
            return
        
        self.arrow.set_active(not self.arrow.get_active())
        self.to_show = self.arrow.get_active()
        self.__set_animating(True)
        
        self.arrow.set_sensitive(False)

        # We need to calculate the speed offset to complete
        # the scrolling in self.tot_time

        self.speed = self.__get_child_height() / (self.tot_time / self.int_time)

        # Avoid null scrolling
        if self.speed < 5:
            self.speed = 5

        if self.to_show:
            self.dest = 0
            self.current = -self.__get_child_height()
            
            gobject.timeout_add(self.int_time, self.__animate_show)
        else:
            self.dest = -self.__get_child_height()
            self.current = 0
            
            gobject.timeout_add(self.int_time, self.__animate_hide)
    
    def __get_child_height(self):
        if self.child.flags() & gtk.REALIZED:
            return self.child.get_allocation().height
        else:
            return self.child.size_request()[1]

    def __set_animating(self, val):
        self.animating = val

        if not self.child:
            return

        self.child.set_sensitive(not self.animating)

        alloc = self.layout.get_allocation()

        if self.to_show:
            alloc.height = self.__get_child_height()
            self.layout.set_size_request(-1, alloc.height + 2)
        else:
            alloc.height = 0
            self.layout.set_size_request(-1, -1)
        
        self.layout.size_allocate(alloc)
        self.size_allocate(self.get_allocation())
    
    def get_image(self):
        return self._image
    
    def set_image(self, stock):
        self._image.set_from_stock(stock, gtk.ICON_SIZE_BUTTON)

    label = property(get_label, set_label)
    image = property(get_image, set_image)

gobject.type_register(AnimatedExpander)

if __name__ == "__main__":
    w = gtk.Window()
    exp = AnimatedExpander("<b>Testinggggg</b>")
    sw = gtk.ScrolledWindow()
    exp.add_widget(gtk.Label("Miao"))
    w.add(exp)
    w.show_all()
    gtk.main()
