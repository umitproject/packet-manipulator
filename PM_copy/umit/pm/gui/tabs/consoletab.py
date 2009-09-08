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

from umit.pm.core.i18n import _
from umit.pm.gui.core.views import UmitView

from console import Console

class ConsoleTab(UmitView):
    name = 'PythonShellTab'
    label_text = _('Python Shell')
    tab_position = gtk.POS_BOTTOM
    icon_name = 'python_small'

    def __create_widgets(self):
        self.console = Console()
        self.console.banner()

    def __pack_widgets(self):
        self._main_widget.add(self.console)
        self._main_widget.show_all()

    def create_ui(self):
        self.__create_widgets()
        self.__pack_widgets()
