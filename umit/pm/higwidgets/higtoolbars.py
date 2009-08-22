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
This module includes:
- HIGToolBar a firefox like toolbar
- HIGToolItem a ToolItem like object for HIGToolBar
- StatusToolItem a special ToolItem that provides a label and a progressbar
"""

import gtk
import cairo
import gobject

class HIGToolItem(gtk.HBox):
    """
    A HBox that emulate the behaviour of ToolItem
    """

    def __init__(self, lbl, image_widg=None, markup=True):
        """
        Initialize an instance of HIGToolItem

        @param lbl the text for label
        @param image_widg the widget to use as image
        @param markup if you want to use markup in the label
        """

        gtk.HBox.__init__(self)
        self.set_spacing(6)

        self._markup = markup
        self._label = gtk.Label(lbl)
        self._label.set_use_markup(markup)

        self._image = None

        if isinstance(image_widg, gtk.Widget):
            self.pack_start(image_widg, False, False, 0)
            self._image = image_widg

        self.vbox = gtk.VBox()
        self.vbox.pack_start(self._label)#, False, False, 0)

        self.pack_start(self.vbox)#, False, False, 0)
        self.set_border_width(6)

        self.set_size_request(-1, 36)

        self.show_all()

    def get_label(self):
        "@return the label widget"
        return self._label

    def set_label(self, txt):
        "Set the label to text (with markup setted in __init__)"
        self._label.set_text(txt)
        self._label.set_use_markup(self._markup)

    def get_image(self):
        "@return the image widget"
        return self._image

    label = property(get_label, set_label)
    image = property(get_image)

class StatusToolItem(HIGToolItem):
    """
    StatusToolItem is a special ToolItem that
    provides a label and a progressbar
    """

    def __init__(self):
        """
        Create an instance of StatusToolItem
        """
        HIGToolItem.__init__(self, "", gtk.Image())

        self.label.set_alignment(0, 0.5)
        self.vbox.set_border_width(1)

        self.progress = gtk.ProgressBar()
        self.progress.set_size_request(-1, 12)

        self.vbox.pack_start(self.progress, False, False, 0)

        self.connect('realize', self.__on_realize)

    def __on_realize(self, widget):
        self.progress.hide()

class HIGToolBar(gtk.EventBox):
    """
    HIGToolBar is a widget that provides a toolbar
    like the firefox one
    """

    __gtype_name__ = "HIGToolBar"
    __gsignals__ = {
        # Emitted when the user click on the toolitems
        'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, \
                     (gobject.TYPE_INT,))
    }

    def __init__(self):
        """
        Create an instance of HIGToolBar
        """
        gtk.EventBox.__init__(self)

        self.vbox = gtk.VBox()
        self.add(self.vbox)
        
        self.items_hbox = gtk.HBox(False, 4)

        self.hover = None
        self.active = None

        self.show_status = False
        self.status_item = StatusToolItem()

        # We use 2 hbox to choose the visual mode
        self.vbox.pack_start(self.items_hbox, False, False, 0)
        self.vbox.pack_start(self.status_item, False, False, 0)

        self.items = []

    def draw_round_rect(self, cr, x, y, w, h, radius_x=5, radius_y=5):
        "Simple func to write a round rect with a cairo context"

        ARC_TO_BEZIER = 0.55228475
        if radius_x > w - radius_x:
            radius_x = w / 2
        if radius_y > h - radius_y:
            radius_y = h / 2
    
        c1 = ARC_TO_BEZIER * radius_x
        c2 = ARC_TO_BEZIER * radius_y
    
        cr.new_path()
        cr.move_to(x + radius_x, y)
        cr.rel_line_to(w - 2 * radius_x, 0.0)
        cr.rel_curve_to(c1, 0.0, radius_x, c2, radius_x, radius_y)
        cr.rel_line_to(0, h - 2 * radius_y)
        cr.rel_curve_to(0.0, c2, c1 - radius_x, radius_y, -radius_x, radius_y)
        cr.rel_line_to(-w + 2 * radius_x, 0)
        cr.rel_curve_to(-c1, 0, -radius_x, -c2, -radius_x, -radius_y)
        cr.rel_line_to(0, -h + 2 * radius_y)
        cr.rel_curve_to(0.0, -c2, radius_x - c1, -radius_y, radius_x, -radius_y)
        cr.close_path()

    def set_source_color(self, cr, color):
        """
        Set the source pattern from a gtk.gdk.Color

        @param cr the cairo context
        @param color a gtk.gdk.Color
        """
        cr.set_source_rgb(
                *self.to_cairo_color(color)
        )

    def to_cairo_color(self, color):
        """
        Transform a cairo color to r/g/b value

        @param the gtk.gdk.Color to convert
        @return a tuple of (r, g, b) value for color
        """
        t = (
            float(float(color.red >> 8) / 255.0),
            float(float(color.green >> 8) / 255.0),
            float(float(color.blue >> 8) / 255.0)
        )
        return t

    def do_realize(self):
        gtk.EventBox.do_realize(self)

        self.add_events(gtk.gdk.MOTION_NOTIFY | gtk.gdk.BUTTON_PRESS)

        #self.style.attach(self.window)
        self.do_size_allocate(self.allocation)

        self.status_item.hide()

    def do_size_allocate(self, alloc):
        gtk.EventBox.do_size_allocate(self, alloc)

        # We have to force to 0 0 to have the
        # correct gradient behaviour :)
        alloc = self.allocation
        alloc.x, alloc.y = 0, 0

        # Color

        self.normal_bg_begin = self.to_cairo_color(
            self.style.light[gtk.STATE_NORMAL]
        )
        self.normal_bg_end = self.to_cairo_color(
            self.style.dark[gtk.STATE_NORMAL]
        )

        self.prelight_bg_begin = self.to_cairo_color(
            self.style.bg[gtk.STATE_PRELIGHT]
        )
        self.prelight_bg_end = self.to_cairo_color(
            self.style.light[gtk.STATE_PRELIGHT]
        )

        self.selected_bg_begin = self.to_cairo_color(
            self.style.light[gtk.STATE_SELECTED]
        )
        self.selected_bg_end = self.to_cairo_color(
            self.style.mid[gtk.STATE_SELECTED]
        )

        # Gradient stuff

        self.normal_bg = cairo.LinearGradient(
            alloc.x, alloc.y, alloc.x, alloc.y + alloc.height
        )
        self.normal_bg.add_color_stop_rgb(0.3, *self.normal_bg_begin)
        self.normal_bg.add_color_stop_rgb(0.9, *self.normal_bg_end)

        self.prelight_bg = cairo.LinearGradient(
            alloc.x, alloc.y, alloc.x, alloc.y + alloc.height
        )
        self.prelight_bg.add_color_stop_rgb(0.3, *self.prelight_bg_begin)
        self.prelight_bg.add_color_stop_rgb(0.9, *self.prelight_bg_end)

        self.selected_bg = cairo.LinearGradient(
            alloc.x, alloc.y, alloc.x, alloc.y + alloc.height
        )
        self.selected_bg.add_color_stop_rgb(0.3, *self.selected_bg_begin)
        self.selected_bg.add_color_stop_rgb(0.9, *self.selected_bg_end)

        self.queue_draw()

    def do_expose_event(self, evt):
        cr = self.window.cairo_create()

        alloc = self.allocation
        alloc.x, alloc.y = 0, 0
        #alloc.width -= 3
        alloc.height -= 3

        self.draw_round_rect(cr,
                alloc.x,
                alloc.y,
                alloc.width,
                alloc.height,
                9, 9
        )

        # Fill the rect
        cr.set_source(self.normal_bg)
        cr.fill_preserve()#

        cr.set_source_rgb( \
            *self.to_cairo_color(self.style.dark[gtk.STATE_ACTIVE]) \
        )
        cr.set_line_width(2)
        cr.stroke()#

        alloc.x += 1
        alloc.y += 1
        alloc.width -= 2
        alloc.height -= 2

        self.draw_round_rect(cr, alloc.x, alloc.y, alloc.width, alloc.height)#
        cr.set_source_rgb(\
            *self.to_cairo_color(self.style.light[gtk.STATE_NORMAL]) \
        )
        cr.set_line_width(0.5)
        cr.stroke()#

        if not self.show_status:
            # hover -> active
            self.draw_item(cr, True)
            self.draw_item(cr, False)

        self.propagate_expose(self.vbox, evt)
        return False

    def draw_item(self, cr, hover=False):
        "Used to draw actived/hovered items"

        item = self.hover

        if not hover:
            item = self.active

        if not item:
            return

        alloc = item.get_allocation()

        alloc.x += 1
        alloc.y += 1
        alloc.width -= 2
        alloc.height -= 4

        # Draw the borders
        self.draw_round_rect(cr,
                alloc.x,
                alloc.y,
                alloc.width,
                alloc.height
        )
        self.set_source_color(cr, self.style.dark[gtk.STATE_NORMAL])
        cr.set_line_width(2)
        cr.stroke()

        alloc.x += 1
        alloc.y += 1
        alloc.width -= 2
        alloc.height -= 2

        if hover:
            cr.set_source(self.prelight_bg)
        else:
            cr.set_source(self.selected_bg)

        self.draw_round_rect(cr,
                alloc.x,
                alloc.y,
                alloc.width,
                alloc.height
        )
        cr.fill_preserve()
        
        cr.stroke()

    def get_item_under_cursor(self, evt):
        """
        Get the item under cursor

        @param evt a gtk.gdk.Event
        @return a item if found or None
        """

        lst = []
        self.items_hbox.foreach(lambda w, x: x.append(w), lst)

        for item in lst:
            f = item.flags()

            # If the widget is not realized or not visible
            if not f & gtk.REALIZED or not f & gtk.VISIBLE:
                continue

            alloc = item.get_allocation()

            if evt.x >= alloc.x and evt.x <= alloc.x + alloc.width and \
               evt.y >= alloc.y and evt.y <= alloc.y + alloc.height:
                return item

        return None

    def do_motion_notify_event(self, evt):
        if self.show_status:
            return

        self.hover = self.get_item_under_cursor(evt)
        self.queue_draw()

    def do_leave_notify_event(self, evt):
        if self.show_status:
            return

        self.hover = None
        self.queue_draw()

    def do_button_release_event(self, evt):
        if self.show_status:
            return

        item = self.get_item_under_cursor(evt)
        
        if item:
            self.active = self.get_item_under_cursor(evt)
            self.hover = None
            self.queue_draw()

        if self.active:
            self.emit('changed', self.items.index(self.active))

    def set_active(self, idx):
        "Set the active item from index"

        if self.show_status:
            return

        try:
            self.active = self.items[idx]
            self.emit('changed', idx)
        except:
            pass

    def get_active(self):
        "Get the index of active item"

        if self.show_status:
            return -1

        if self.active:
            return self.items.index(self.active)

    def append(self, item):
        "Append a HIGToolItem to the toolbar"

        assert isinstance(item, HIGToolItem), "must be HIGToolItem"

        self.items_hbox.pack_start(item, False, False, 0)
        self.items.append(item)

    def show_message(self, msg, stock=None, file=None):
        """
        Show a message using the StatusToolItem

        You could use stock OR file for image, not both.
        (file has precedence if both are specified)

        @param msg the message to show (could use markup)
        @param stock the stock for the image
        @param file the file for the image
        """

        self.status_item.label = msg
        self.status_item.image.show()

        if file:
            self.status_item.image.set_from_file(file)
        elif stock:
            self.status_item.image.set_from_stock(stock, \
                                                  gtk.ICON_SIZE_LARGE_TOOLBAR)
        else:
            self.status_item.image.hide()

        self.show_status = True
        self.items_hbox.hide()
        self.status_item.show()

    def set_status_progress(self, fract=0, show=True):
        """
        Set the progressbar fraction for StatusToolItem

        @param fract the fraction to set
        @param show if the progressbar should be showed or not
        """
        self.status_item.progress.set_fraction(fract)

        if show:
            self.status_item.progress.show()
        else:
            self.status_item.progress.hide()

    def get_status_progress(self):
        "Get the fraction of StatusToolItem's statusbar"
        return self.status_item.progress.get_fraction()

    def unset_status(self):
        "Hide the StatusToolItem resetting the initial situation"

        self.show_status = False

        self.status_item.label = ""
        self.status_item.image.set_from_stock(
            gtk.STOCK_MISSING_IMAGE,
            gtk.ICON_SIZE_DIALOG
        )
        self.status_item.image.hide()

        self.status_item.hide()
        self.items_hbox.show()

if __name__ == "__main__":
    w = gtk.Window()
    t = HIGToolBar()

    t.append(HIGToolItem("test"))
    t.append(HIGToolItem("test"))
    t.append(HIGToolItem("test"))
    t.append(HIGToolItem("test"))
    t.append(HIGToolItem("test"))

    box = gtk.VBox()
    box.pack_start(t, False, False, 0)
    w.add(box)

    w.show_all()
    gtk.main()
