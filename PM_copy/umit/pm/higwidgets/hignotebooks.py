#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Insecure.Com LLC.
# Copyright (C) 2007-2008 Adriano Monteiro Marques
#
# Author: Adriano Monteiro Marques <adriano@umitproject.org>
#         Cleber Rodrigues <cleber.gnu@gmail.com>
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

from umit.pm.higwidgets.higspinner import HIGSpinner
from umit.pm.higwidgets.higboxes import HIGHBox
from umit.pm.higwidgets.higbuttons import HIGButton

class HIGEditableLabel(gtk.EventBox):
    # called when label is changed .. if returns True new_value is setted
    __gsignals__ = {'title-edited' : (gobject.SIGNAL_RUN_LAST,
                                      gobject.TYPE_BOOLEAN,
                                      (gobject.TYPE_STRING,
                                       gobject.TYPE_STRING))}

    def __init__(self, label=''):
        gobject.GObject.__init__(self)

        self.label = gtk.Label(label)
        self.entry = gtk.Entry()

        self.lock = False
        
        box = gtk.HBox()
        self.add(box)
        
        box.pack_start(self.label, False, False, 0)
        box.pack_start(self.entry, False, False, 0)
        
        self.set_visible_window(False)
        self.show_all()
        
        self.entry.connect('activate', self.on_entry_activated)
        self.entry.connect('focus-out-event', self.on_lost_focus)
        self.connect('realize', self.on_realize_event)
        self.connect('button-press-event', self.on_button_press_event)

    def on_lost_focus(self, widget, event):
        self.on_entry_activated(widget)

    def on_entry_activated(self, widget):
        # Muttex for focus
        if self.lock:
            return False

        self.lock = True

        old_text = self.label.get_text()
        new_text = self.entry.get_text()

        self.switch_mode(False)

        # If returns True we can change the label
        if self.emit('title-edited', old_text, new_text):
            self.label.set_text(new_text)

        self.lock = False

        return False

    def on_realize_event(self, widget):
        self.entry.hide()

    def on_button_press_event(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.switch_mode(True)

    def switch_mode(self, editing):
        """Switches from editing (True) to label mode (False).
        """
        if editing:
            self.entry.set_text(self.label.get_text())
            self.entry.grab_focus()

            self.label.hide()
            self.entry.show()
        else:
            self.entry.set_text('')

            self.label.show()
            self.entry.hide()

        # Reallocate widget
        self.set_size_request(-1, -1)

    # Getters/setters for compatibility

    def get_text(self):
        return self.label.get_text()

    def set_text(self, label):
        self.label.set_text(label)

    def get_label(self):
        return self.label.get_label()

    def set_label(self, label):
        self.label.set_text(label)

gobject.type_register(HIGEditableLabel)
HIGAnimatedLabel = HIGEditableLabel

class HIGNotebook(gtk.Notebook):
    def __init__(self):
        gtk.Notebook.__init__(self)
        self.popup_enable()

class HIGClosableTabLabel(HIGHBox):
    __gsignals__ = { 'close-clicked' : (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE, ()) }

    def __init__(self, label_text=""):
        gobject.GObject.__init__(self)
        #HIGHBox.__init__(self, spacing=4)

        self.label_text = label_text
        self.__create_widgets()

        #self.propery_map = {"label_text" : self.label.get_label}

    def __create_widgets(self):
        self.label = HIGAnimatedLabel(self.label_text)
        
        self.close_image = gtk.Image()
        self.close_image.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_BUTTON)
        self.close_button = HIGButton()
        self.close_button.set_size_request(22, 22)
        self.close_button.set_relief(gtk.RELIEF_NONE)
        self.close_button.set_focus_on_click(False)
        self.close_button.add(self.close_image)

        self.ok_image = gtk.Image()
        self.ok_image.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)
        self.ok_button = HIGButton()
        self.ok_button.set_size_request(22, 22)
        self.ok_button.set_relief(gtk.RELIEF_NONE)
        self.ok_button.set_focus_on_click(False)
        self.ok_button.add(self.ok_image)

        self.close_button.connect('clicked', self.__close_button_clicked)
        self.ok_button.connect('clicked', self.__ok_button_clicked)
        self.label.connect('button-press-event', self.on_button_press_event)
        self.label.entry.connect('focus-out-event', self.on_entry_focus_out)

        for w in (self.label, self.close_button, self.ok_button):
            self.pack_start(w, False, False, 0)

        self.show_all()
        self.switch_button_mode(False) # Change to label mode

        # def do_get_property(self, property):
        #     func = self.property_map.get(property, None)
        #     if func:
        #         return func()
        #     else:
        #         raise 

    def on_entry_focus_out(self, widget, event):
        self.switch_button_mode(False)

    def on_button_press_event(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.switch_button_mode(True)

    def switch_button_mode(self, mode):
        """Switch button from editing mode (True) to label mode (False)
        """
        if mode:
            self.close_button.hide()
            self.ok_button.show()
        else:
            self.ok_button.hide()
            self.close_button.show()

    def __close_button_clicked(self, widget):
        self.emit('close-clicked')

    def __ok_button_clicked(self, widget):
        self.label.on_entry_activated(self.label.entry)
        self.switch_button_mode(False)

    def get_text(self):
        return self.label.get_text()

    def set_text(self, text):
        self.label.set_text(text)

    def get_label(self):
        return self.label.get_label()

    def set_label(self, label):
        self.label.set_text(label)

    def get_animated_label(self):
        return self.label

gobject.type_register(HIGClosableTabLabel)

HIGAnimatedTabLabel = HIGClosableTabLabel
