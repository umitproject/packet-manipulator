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
HIGAnimatedBar a widget like firefox bar
"""

import gtk
import gobject

class HIGAnimatedBar(gtk.EventBox):
    """
    A dummy animated bar to show message like Firefox one.
    """
    __gtype_name__ = "HIGAnimatedBar"

    def __init__(self, msg, stock=gtk.STOCK_DIALOG_INFO, file=None, markup=True):
        """
        Create a HIGAnimatedBar
        
        The stock option have priority.
        
        @param msg the message to show in the label
        @param stock the stock for gtk.Image
        @param file the file to use with gtk.Image
        @param markup if label should use markup
        """
        gtk.EventBox.__init__(self)

        if stock:
            self._image = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU)
        elif file:
            self._image = gtk.image_new_from_file(file)

        self._markup = True
        self._label = gtk.Label(msg)
        self._label.set_use_markup(markup)
        self._label.set_alignment(0, 0.5)

        self._close = gtk.Button()
        self._close.add(gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU))
        self._close.set_relief(gtk.RELIEF_NONE)
        self._close.connect('clicked', self.__on_close)

        self._hbox = gtk.HBox()
        self._hbox.set_spacing(4)
        self._hbox.set_border_width(2)

        self._hbox.pack_start(self._image, False, False, 0)
        self._hbox.pack_start(self._label)
        self._hbox.pack_start(self._close, False, False, 0)

        self._frame = gtk.Frame()
        self._frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self._frame.add(self._hbox)

        self._frame.show_all()

        self.add(self._frame)
        self.set_redraw_on_allocate(False)

        self._animate = False
        self._show = True
        self._max_height = 0
        self._first_expose = True
        self._animate_id = None
        self._current_height = 0

    def do_size_allocate(self, alloc):
        if self._animate:
            if self._show: self._current_height += 5
            else:          self._current_height -= 5

            alloc.height = self._current_height

            if not self._show and alloc.height <= 0:
                self._animate = False
                alloc.height = 0

                # uhm?
                self.hide()

            if self._show and alloc.height >= self._max_height:
                self._animate = False
                alloc.height = self._max_height

        # Check the max height
        if self._max_height > 0 and alloc.height >= self._max_height:
            alloc.height = self._max_height

        gtk.EventBox.do_size_allocate(self, alloc)

    def do_expose_event(self, evt):
        if self._first_expose:
            alloc = self.allocation; alloc.height = 0
            self.do_size_allocate(alloc)

            if self.flags() & gtk.VISIBLE:
                self.start_animation(True)

            self._first_expose = False

        return gtk.EventBox.do_expose_event(self, evt)

    def do_realize(self):
        gtk.EventBox.do_realize(self)

        self.bg_color = gtk.gdk.color_parse("#FFFFDC")
        gtk.gdk.colormap_get_system().alloc_color(self.bg_color)

        # NB: Should we add more colors here?
        self.modify_bg(gtk.STATE_NORMAL, self.bg_color)
        self._max_height = self._frame.size_request()[1]

        alloc = self.allocation; alloc.height = 0
        self.do_size_allocate(self.allocation)

    def __do_animation(self):
        """
        callback for timeout_add
        """

        self.do_size_allocate(self.allocation)
        return self._animate

    def __on_close(self, widget):
        self.start_animation(False)

    def start_animation(self, show):
        """
        Start the animation

        @param show if the widget will be showed or hided
        """
        self._animate = True
        self._show = show

        if show:
            if not self.flags() & gtk.VISIBLE:
                self.show()
            self._current_height = 0
        else:
            self._current_height = self._max_height

        if self._animate_id:
            gobject.source_remove(self._animate_id)

        self._animate_id = gobject.timeout_add(100, self.__do_animation)

    def get_image(self):
        "@return the gtk.Image widget"
        return self._image
    def set_image(self, stock):
        "Set the image to stock"
        self._image.set_from_stock(stock, gtk.ICON_SIZE_MENU)
    
    def get_label(self):
        "@return the gtk.Label widget"
        return self._label

    def set_label(self, txt):
        "Set the text to label and restore image to original"
        self._label.set_text(txt)
        self._label.set_use_markup(self._markup)
        self.image = gtk.STOCK_DIALOG_INFO
    
    image = property(get_image, set_image)
    label = property(get_label, set_label)

gobject.type_register(HIGAnimatedBar)

if __name__ == "__main__":
    w = gtk.Window()

    def add(b, v):
        anim = HIGAnimatedBar(
            "<span font-desc=\"Monospace\"><b>"
            "W00t! from stupid animated widget"
            "</b></span>"
        )
        v.pack_start(anim)
        anim.show()

    vbox = gtk.VBox()

    btn = gtk.Button(stock=gtk.STOCK_ADD)
    btn.connect('clicked', add, vbox)

    bar = HIGAnimatedBar("<b>Hey man try to click! :)</b>")

    vbox.pack_start( \
        bar, \
        False, False, 0
    )
    vbox.pack_start(btn, False, False, 0)

    hbb = gtk.HButtonBox()

    btn = gtk.Button("SHOW")
    btn.connect('clicked', lambda x, w: w.start_animation(True), bar)
    hbb.pack_start(btn)

    btn = gtk.Button("HIDE")
    btn.connect('clicked', lambda x, w: w.start_animation(False), bar)
    hbb.pack_start(btn)

    vbox.pack_start(hbb, False, False)

    w.add(vbox)
    w.set_size_request(200, 200)
    w.show_all()

    w.connect('delete-event', lambda *w: gtk.main_quit())

    gtk.main()
