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

from PM.Core.Logger import log
from PM.Gui.Widgets.ClosableLabel import ClosableLabel

class Session(gtk.VBox):
    def __init__(self, ctx):
        super(Session, self).__init__(False, 2)

        self.packet = None
        self.context = ctx
        self.context.title_callback = self.__on_change_title

        self._label = ClosableLabel(ctx.title)

        self.set_border_width(4)
        self.create_ui()

    def create_ui(self):
        pass

    def reload(self):
        self.reload_container()
        self.reload_editor()
    
    def reload_container(self, packet=None):
        """
        Reload the container of the all packets list
        @param packet the instance of the packet edited to save cpu or None
        """
        pass

    def reload_editor(self):
        "Reload the editor of the single active packet"
        pass

    def set_active_packet(self, packet):
        if packet != self.packet:
            self.packet = packet
            self.reload_editor()
        else:
            log.debug("Packets are the same ignoring updates")

    def get_label(self):
        return self._label

    def __on_change_title(self):
        if self.context:
            self._label.label.set_text(self.context.title)

    label = property(get_label)
