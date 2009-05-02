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
This module contains the PMApp singleton object that gives access to
the all PacketManipulator functionalities
"""

import gtk
import gobject

import os
import sys

from optparse import OptionParser

from PM.Core.I18N import _
from PM.Core.Atoms import Singleton
from PM.Gui.Core.Splash import SplashScreen
from PM.Gui.Plugins.Engine import PluginEngine

class PMApp(Singleton):
    "The PacketManipulator application singleton object"

    def __init__(self, args):
        """
        PacketManipulator Application class
        @param args pass sys.argv
        """
        gobject.threads_init()

        self._args = args
        root = False

        try:
            # FIXME: add maemo
            if sys.platform == 'win32':
                import ctypes
                root = bool(ctypes.windll.shell32.IsUserAnAdmin())
            elif os.getuid() == 0:
                root = True
        except: pass

        if not root:
            dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_WARNING,
                                       gtk.BUTTONS_YES_NO,
                                       _('You are running Packet Manipulator as'
                                         ' non-root user!\nSome functionalities'
                                         ' need root privileges to work\n\nDo '
                                         'you want to continue?'))
            ret = dialog.run()
            dialog.hide()
            dialog.destroy()

            if ret == gtk.RESPONSE_NO:
                sys.exit(-1)

        self.phase = 0
        self.splash = SplashScreen()

    def _idle(self):

        if self.phase == 0:
            self.splash.text = _("Registering icons ...")

            from Icons import register_icons
            register_icons()
        elif self.phase == 1:
            self.splash.text = _("Loading preferences ...")

            from PM.Manager.PreferenceManager import Prefs
            self.prefs = Prefs()
        elif self.phase == 2:
            self.splash.text = _("Creating main window ...")

            from MainWindow import MainWindow
            self.main_window = MainWindow()
            self.main_window.connect_tabs_signals()
            self.plugin_engine = PluginEngine()
            self.plugin_engine.load_selected_plugins()

            # Destroy the splash screen
            self.splash.hide()
            self.splash.destroy()
            self.splash.finished = True

            del self.splash

            # Now let's parse the args passed in the constructor
            parser = self._create_parser()
            options, args = parser.parse_args(self._args)

            if options.fread:
                self.main_window.open_generic_file_async(options.fread)

            return False

        self.phase += 1
        return True

    def run(self):
        self.splash.show_all()
        gobject.idle_add(self._idle)
        gtk.main()

    def _create_parser(self):
        """
        @return an OptionParser object that can handle the sys.argv passed in
                the constructor.
        """

        opt = OptionParser()
        opt.add_option('-r', None, dest="fread",
                       help="Read packets/sequence from file.")

        return opt