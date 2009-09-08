#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
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

class StatusBar(gtk.Statusbar):
    __gtype_name__ = "StatusBar"

    def __init__(self):
        super(StatusBar, self).__init__()

        self.image = gtk.Image()
        self.progress = gtk.ProgressBar()

        self.pushed = False

        self.timeout_id = None

        self.frame = gtk.Frame()
        self.frame.set_border_width(0)
        self.frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.pack_start(self.frame, False, False)
        self.reorder_child(self.frame, 0)

        hbox = gtk.HBox(False, 2)
        hbox.pack_start(self.image, False, False)
        hbox.pack_end(self.progress, False, False)

        self.frame.add(hbox)
        self.frame.show_all()

        self.set_no_show_all(True)
        self.show()

    def push(self, text, image=None, progress=None, pulse=False):
        """
        Set the status bar text

        @param text the text to set in the statusbar
        @param image the image to use (None to hide)
        @param progress the progress bar fraction (None to hide)
        @param pulse if the progress should pulse (progress has precedence)
        """

        if self.pushed:
            self.pop()
        else:
            self.pushed = True

        if isinstance(image, basestring):
            self.image.set_from_stock(image, gtk.ICON_SIZE_MENU)
            self.image.show()
        else:
            self.image.hide()

        if isinstance(progress, float):
            self.progress.set_fraction(progress)
            self.progress.show()

            self.timeout_id = None
        elif pulse:
            self.progress.show()

            if self.timeout_id is None:
                self.timeout_id = gobject.timeout_add(500, self.__pulse_step)
        else:
            self.timeout_id = None
            self.progress.hide()

        gtk.Statusbar.push(self, -1, text)

    def pop(self):
        self.pushed = False

        if self.image.flags() & gtk.VISIBLE:
            self.image.hide()

        if self.progress.flags() & gtk.VISIBLE:
            self.progress.hide()
            self.progress.set_value(0)

        if self.timeout_id:
            gobject.source_remove(self.timeout_id)
            self.timeout_id = None

        gtk.Statusbar.pop(self, -1)

    def __pulse_step(self):
        self.progress.pulse()

        return self.timeout_id != None

gobject.type_register(StatusBar)

if __name__ == "__main__":
    w = gtk.Window()
    bar = StatusBar()
    w.add(bar)
    w.show_all()

    bar.push("miao", pulse=True)
    gtk.main()
