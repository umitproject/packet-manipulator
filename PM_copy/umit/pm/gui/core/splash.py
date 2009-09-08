#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
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
Splash screen module
"""

import gtk
import gobject

import os
import os.path

from umit.pm.core.const import PM_VERSION, PIXMAPS_DIR

class SplashScreen(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        self.set_position(gtk.WIN_POS_CENTER)

        vbox = gtk.VBox()
        vbox.set_border_width(4)

        self.add(vbox)

        self.image = gtk.image_new_from_file(
                               os.path.join(PIXMAPS_DIR, "pm-logo.png"))
        self.label = gtk.Label("<span size='x-large'><b>" \
                               "PacketManipulator %s" \
                               "</b></span>" % PM_VERSION)
        self.label.set_use_markup(True)

        hbox = gtk.HBox()
        hbox.set_spacing(20)
        hbox.pack_start(self.image, False, False)
        hbox.pack_start(self.label)

        self.progress = gtk.ProgressBar()
        self.progress.set_text("Loading modules ...")

        vbox.pack_start(hbox)
        vbox.pack_start(self.progress, False, False)

        self.finished = False

        gobject.timeout_add(200, self.__pulse_bar)

    def __pulse_bar(self):
        self.progress.pulse()

        return not self.finished

    def get_text(self): return self.progress.get_text()
    def set_text(self, txt): self.progress.set_text(txt)

    text = property(get_text, set_text)

if __name__ == "__main__":
    s = SplashScreen()
    s.show_all()
    s.connect('delete-event', lambda *w: gtk.main_quit())
    gtk.main()
