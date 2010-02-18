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

"""
Here goes core implementation to access umit
functionalities
"""

import sys
import gtk
import gobject

from umit.pm.core.logger import log
from umit.pm.core.bus import ServiceBus
from umit.pm.core.atoms import Singleton
from umit.pm.gui.plugins.atoms import Version
from umit.pm.higwidgets.gtkutils import gobject_register

class Core(Singleton, gobject.GObject):
    __gtype_name__ = "UmitCore"
    __gsignals__ = {
        'ScanHostsView-created' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT, )),
        'ScanResultNotebook-created' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT, )),
        'ScanNotebookPage-created' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT, ))
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self.mainwindow = None
        self.bus = ServiceBus()
        gtk.about_dialog_set_url_hook(self.__about_dialog_url, None)

    #
    # MainWindow related functions

    def get_main_toolbar(self):
        "@return the toolbar of the MainWindow"
        return self.mainwindow.toolbar

    def get_main_menu(self):
        "@return the menubar of the MainWindow"
        return self.mainwindow.menubar

    def get_main_scan_notebook(self):
        "@return the scan_notebook of the MainWindow"
        return self.mainwindow.scan_notebook

    # This is unused
    #def get_main_statusbar(self):
    #    "@return the statusbar of the MainWindow"
    #    return self.mainwindow.statusbar

    def get_need(self, reader, needstr, classname=None, need_module=False):
        """
        Usefull function to return an instance of needstr:classname

        @param reader a PluginReader object or None
        """
        lst = []

        if reader:
            # We create a list of needs for the same package
            for need in reader.needs:
                name, op, ver = Version.extract_version(need)

                if name == needstr:
                    lst.append((op, ver, name))

        from umit.pm.gui.plugins.engine import PluginEngine
        ret = PluginEngine().tree.get_provide(needstr, lst, need_module)

        log.debug(">>> Core.get_need() -> %s (module: %s)" % (ret, need_module))

        if not ret:
            return None

        if not need_module:
            if not classname:
                log.debug(">>> Core.get_need(): No classname specified. " \
                          "Returning first instance")
                return ret[0]

            for instance in ret:
                if instance.__class__.__name__ == classname:
                    return instance
        else:
            # We need a module

            if len(ret) > 1:
                log.debug(">>> Core.get_need(): Returning the first module")

            return ret[0]

        return None

    def __about_dialog_url(self, d, link, data):
        self.open_url(link)

    def open_url(self, link):
        """
        Open the default browser at link location

        @param link the link to open
        """

        import webbrowser

        new = 0
        if sys.hexversion >= 0x2050000:
            new = 2

        webbrowser.open(link, new=new)

    def about_dialog(self, pkg):
        """
        Create a generic about dialog for PluginReader

        @return a gtk.AboutDialog
        """
        d = gtk.AboutDialog()

        def set_field(pkg, func, field, c=False):
            if hasattr(pkg, field):
                attr = getattr(pkg, field)

                if not attr or attr == "":
                    return

                if isinstance(attr, (list, tuple)):
                    attr = '\n'.join(attr)

                if c:
                    attr = [attr, ]

                func(attr)

        set_field(pkg, d.set_name, 'name')
        set_field(pkg, d.set_version, 'version')
        set_field(pkg, d.set_copyright, 'copyright')
        set_field(pkg, d.set_license, 'license')
        set_field(pkg, d.set_website, 'url')
        set_field(pkg, d.set_comments, 'description')

        set_field(pkg, d.set_authors, 'author', True)
        set_field(pkg, d.set_documenters, 'documenter', True)
        set_field(pkg, d.set_artists, 'artist', True)

        d.set_logo(pkg.get_logo())

        return d

gobject_register(Core)
