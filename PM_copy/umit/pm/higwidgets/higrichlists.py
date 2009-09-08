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

"""
This module contains:
- HIGRichList like firefox one
- HIGRichRow a row for HIGRichList
- PluginRow a custom HIGRichRow for HIGRichList
"""

import gtk
import pango
import gobject
from umit.pm.higwidgets.higbuttons import HIGButton
from umit.pm.core.i18n import _

class HIGRichRow(gtk.EventBox):
    """
    Represent a single row for HIGRichList
    """

    __gtype_name__ = "HIGRichRow"
    __gsignals__ = {
        # Emitted when the user activate (selected)
        'activate' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),

        # Emitted when the user click with mouse
        'clicked'  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),

        # Emitted when the user click with the right button
        'popup'  : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, \
                    (gtk.gdk.Event,))
    }

    def __init__(self, tree):
        """
        Create a HIGRichRow

        @param tree a PluginRichList object to use as parent
        """

        assert isinstance(tree, HIGRichList), "must be a HIGRichList object"

        gtk.EventBox.__init__(self)

        self.tree = tree

        self.__create_widgets()
        self.__pack_widgets()

        self._vbox.show()

    def __create_widgets(self):
        self._vbox = gtk.VBox()

    def __pack_widgets(self):
        self.add(self._vbox)

    def do_expose_event(self, evt):
        "Override this function"

        gtk.EventBox.do_expose_event(self, evt)

        alloc = self.allocation
        cr = self.window.cairo_create()

        # Only draw an end-line
        cr.set_line_width(0.5)
        cr.set_dash([1, 1], 1)
        cr.move_to(0, alloc.height)
        cr.line_to(alloc.width, alloc.height)
        cr.stroke()

        return True
    
    def do_realize(self):
        gtk.EventBox.do_realize(self)
        self.active = False

    def do_button_press_event(self, evt):
        if (evt.button == 1) and \
           (evt.type == gtk.gdk._2BUTTON_PRESS) and \
           (self.tree.change_selection(self)):
            
            self.active = True
            self.emit('clicked')

        elif (evt.type == gtk.gdk.BUTTON_PRESS) and \
             (self.tree.change_selection(self)):

            self.active = True

            if evt.button == 3:
                self.emit('popup', evt)

    def get_active(self):
        return self._active

    def set_active(self, value):
        self._active = value
        self.emit('activate')

        if self.flags() & gtk.REALIZED:
            if value:
                self.modify_bg(gtk.STATE_NORMAL, \
                               self.style.base[gtk.STATE_PRELIGHT])
            else:
                self.modify_bg(gtk.STATE_NORMAL, self.style.white)

    def get_vbox(self):
        return self._vbox

    active = property(get_active, set_active)
    vbox = property(get_vbox)

class PluginRow(HIGRichRow):
    """
    A custom HIGRichRow to contains Plugin informations
    """

    __gtype_name__ = "PluginRow"

    def __init__(self, tree, reader):
        """
        Create a PluginRow

        @param tree a PluginRichList object to use as parent
        @param reader a PluginrReader object to be represented
        """

        HIGRichRow.__init__(self, tree)

        self._reader = reader
        self._enabled = False

        self._message = reader.description
        self._show_progress = False
        self._show_include = False
        self._activatable = True
        self._saturate = False

        self.__create_widgets()
        self.__pack_widgets()

        self.enabled = self._reader.enabled
        self.connect('activate', self.__on_activate)
        
        self.show_all()

        self.progressbar.hide()
        self.box_act.hide()
        self.include_button.hide()

    def __create_widgets(self):
        self.image = gtk.image_new_from_pixbuf(self._reader.get_logo())

        self.label = gtk.Label('')
        self.label.set_ellipsize(pango.ELLIPSIZE_END)
        
        self.include_button = gtk.CheckButton(_('Include update'))

        self.img_play = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, \
                                                 gtk.ICON_SIZE_BUTTON)
        self.img_stop = gtk.image_new_from_stock(gtk.STOCK_MEDIA_STOP, \
                                                 gtk.ICON_SIZE_BUTTON)

        self.action_btn = HIGButton('')
        self.uninstall_btn = HIGButton(_("Uninstall"), gtk.STOCK_CLEAR)
        self.preference_btn = HIGButton(stock=gtk.STOCK_PREFERENCES)

        self.progressbar = gtk.ProgressBar()

    def __pack_widgets(self):

        # Visible part
        hbox = gtk.HBox(False, 4)
        hbox.set_border_width(4)

        hbox.pack_start(self.image, False, False, 0)

        vbox = gtk.VBox(False, 2)
        
        mhbox = gtk.HBox(False, 2)
        self.label.set_alignment(0, 0.5)
        
        mhbox.pack_start(self.label)
        mhbox.pack_start(self.include_button, False, False)
        
        vbox.pack_start(mhbox)
        vbox.pack_start(self.progressbar, False, False, 0)

        hbox.pack_start(vbox)

        self.vbox.pack_start(hbox, False, False, 0)

        # Buttons part
        align = gtk.Alignment(0, 0.5)
        align.add(self.preference_btn)

        self.box_act = gtk.HBox(False, 2)
        self.box_act.pack_start(align, True, True, 0)
        self.box_act.pack_start(self.uninstall_btn, False, False, 0)
        self.box_act.pack_start(self.action_btn, False, False, 0)

        self.box_act.set_border_width(4)
        self.vbox.pack_start(self.box_act, False, False, 0)

    def __on_activate(self, widget):
        if not self._activatable:
            self.box_act.hide()
            return

        if self._show_progress:
            self.box_act.hide()
            self.progressbar.show()
        else:
            self.progressbar.hide()

            if self.active:
                self.box_act.show()
            else:
                self.box_act.hide()

    def get_enabled(self):
        return self._enabled

    def set_enabled(self, val):
        self._enabled = val

        # We need more testing on color/saturate on enabled

        if self._enabled:
            self.action_btn.set_label(_("Disable"))
            self.action_btn.set_image(self.img_stop)

            #
            color = self.style.text[gtk.STATE_NORMAL]
            self.saturate = False
        else:
            self.action_btn.set_label(_("Enable"))
            self.action_btn.set_image(self.img_play)

            #
            color = self.style.text[gtk.STATE_INSENSITIVE]
            self.saturate = True

        self.label.set_text( \
            "<span color=\"%s\">"
            "<span size=\"x-large\" weight=\"bold\">%s</span>" \
            "    %s" \
            "\n<tt>%s</tt>" \
            "</span>" % \
            ( \
                color.to_string(), \
                self._reader.name, \
                self._reader.version, \
                self._message \
            ) \
        )
        self.label.set_use_markup(True)

    def get_reader(self):
        return self._reader

    enabled = property(get_enabled, set_enabled)
    reader  = property(get_reader)

    def get_message(self):
        return self._message
    
    def set_message(self, value):
        """
        If not defined don't update
        """
        
        if value != None:
            self._message = value
            
            # Used to update the label
            self.enabled = self.enabled

    def get_progress(self):
        if self._show_progress:
            return self.progressbar.get_fraction()
        return None

    def set_progress(self, val):
        self.box_act.hide()

        if not val or val < .0:
            self._show_progress = False
            self.progressbar.set_fraction(0)
            self.progressbar.hide()
        else:
            self._show_progress = True
            self.progressbar.set_fraction(val)
            self.progressbar.set_text('%d %%' % int(val * 100))
            self.progressbar.show()
    
    def get_include(self):
        if self._show_include:
            return self.include_button.get_active()
        else:
            return False
    
    def set_include(self, value):
        self._show_include = value
        
        if value:
            self.include_button.show()
        else:
            self.include_button.hide()

    def get_activatable(self):
        return self._activatable
    def set_activatable(self, value):
        self._activatable = value
        self.__on_activate(self)

    def get_saturate(self):
        return self._saturate

    def set_saturate(self, val):
        self._saturate = val

        if self._saturate:
            logo = self._reader.get_logo()
            logo.saturate_and_pixelate(logo, 0.3, False)
            self.image.set_from_pixbuf(logo)
        else:
            self.image.set_from_pixbuf(self._reader.get_logo())

    message = property(get_message, set_message)
    progress = property(get_progress, set_progress)
    show_include = property(get_include, set_include)
    activatable = property(get_activatable, set_activatable)
    saturate = property(get_saturate, set_saturate)

class HIGRichList(gtk.ScrolledWindow):
    """
    A simil-treeview widget like firefox RichList
    """

    def __init__(self):
        """
        Create a HIGRichList object
        """

        gtk.ScrolledWindow.__init__(self)
        
        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.vbox = gtk.VBox()

        self.add_with_viewport(self.vbox)

        # We set the background of viewport to white
        self.get_child().modify_bg(gtk.STATE_NORMAL, \
                                   self.get_child().style.white)

        self.prev_sel = None

        self.show_all()

    def append_row(self, widget):
        """
        Append a row to the tree

        @param widget a HIGRichRow type object
        """

        assert isinstance(widget, HIGRichRow), "must be a HIGRichRow object"

        self.vbox.pack_start(widget, False, False, 0)

    def remove_row(self, widget):
        """
        Remove a row from the tree

        @param widget a HIGRichRow type object
        """
        assert isinstance(widget, HIGRichRow), "must be a HIGRichRow object"

        self.vbox.remove(widget)

    def clear(self):
        """
        Remove all the row
        """

        def remove(widget, parent):
            #
            widget.hide()
            parent.remove(widget)

        self.vbox.foreach(remove, self.vbox)
    
    def get_rows(self):
        return len(self.vbox)

    def foreach(self, callback, userdata):
        "Foreach in any widgets"

        self.vbox.foreach(callback, userdata)

    def change_selection(self, row):
        """
        Change the selected item in the tree

        @return True if selection was changed
        """
        assert row != None

        if self.prev_sel:
            self.prev_sel.active = False

        self.prev_sel = row

        # Grab the focus!
        self.grab_focus()

        # Scroll to active item
        adj = self.get_vadjustment()
        alloc = row.get_allocation()

        if alloc.y < adj.value:
            adj.set_value(alloc.y)
        elif alloc.y + alloc.height > adj.value + adj.page_size:
            adj.set_value(alloc.y)

        return True
