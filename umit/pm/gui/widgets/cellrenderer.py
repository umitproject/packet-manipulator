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

class GridRenderer(gtk.CellRendererText):
    __gtype_name__ = "SniffRenderer"

    def do_render(self, window, widget, back, cell, expose, flags):
        cr = window.cairo_create()
        cr.save()

        cr.set_line_width(0.5)
        cr.set_dash([1, 1], 1)
        cr.move_to(back.x, back.y + back.height)
        cr.line_to(back.x + back.width, back.y + back.height)
        cr.stroke()

        cr.restore()

        return gtk.CellRendererText.do_render(self, window, widget, back, cell, expose, flags)

gobject.type_register(GridRenderer)
