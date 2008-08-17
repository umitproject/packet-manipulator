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

import os
import sys

from PM.Core.I18N import _
from PM.Core.Atoms import Singleton

class PMApp(Singleton):
    def __init__(self):
        gobject.threads_init()

        root = False

        try:
            # FIXME: add maemo
            if sys.platform == 'win32':
                root = True
            elif os.getuid() == 0:
                root = True
        except: pass

        if not root:
            dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_WARNING,
                                       gtk.BUTTONS_YES_NO,
                                       _('You are running Packet Manipulator as non-root user!\n'
                                         'Some functionalities need root privileges to work\n\n'
                                         'Do you want to continue?'))
            ret = dialog.run()
            dialog.hide()
            dialog.destroy()
            
            if ret == gtk.RESPONSE_NO:
                sys.exit(-1)

        from Icons import register_icons

        register_icons()

        from MainWindow import MainWindow
        from PM.Manager.PreferenceManager import Prefs

        self.prefs = Prefs()
        self.main_window = MainWindow()
        self.main_window.connect_tabs_signals()

    def run(self):
        gtk.main()
