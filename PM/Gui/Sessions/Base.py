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

from PM.Core.I18N import _
from PM.Core.Logger import log
from PM.Manager.PreferenceManager import Prefs

from PM.Gui.Core.App import PMApp
from PM.Gui.Tabs.OperationsTab import FileOperation

from PM.Gui.Widgets.MultiPaneds import VMultiPaned, HMultiPaned
from PM.Gui.Widgets.Expander import AnimatedExpander
from PM.Gui.Widgets.ClosableLabel import ClosableLabel

class Session(gtk.VBox):
    session_id = 0 # Setted automatically
    session_name = "" # Shoud be setted
    session_menu = None # Set it if you want a menu item added in main window
    session_menu_object = None
    session_orientation = gtk.ORIENTATION_VERTICAL

    def __init__(self, ctx):
        super(Session, self).__init__(False, 2)

        if self.session_orientation == gtk.ORIENTATION_HORIZONTAL:
            self.paned = HMultiPaned()
        else:
            self.paned = VMultiPaned()

        self.perspectives = []
        self.container_cbs = []
        self.editor_cbs = []

        self.packet = None
        self.context = ctx
        self.context.title_callback = self.__on_change_title

        self._label = ClosableLabel(ctx.title)

        self.set_border_width(4)
        self.create_ui()

        # Now apply the bindings for this Session
        PMApp().main_window.apply_bindings(self, self.session_id)

    def create_ui(self):
        pass

    def remove_perspective(self, klass):
        """
        Remove the perspective from the current session

        @param klass the perspective klass to remove
        @return True if everything is ok
        """

        for persp in self.perspectives:
            if isinstance(persp, klass):
                widget = persp

                while not isinstance(widget.get_parent(), gtk.Paned):
                    widget = widget.get_parent()

                widget.hide()
                self.perspectives.remove(persp)
                self.paned.remove_child(widget)

    def add_perspective(self, klass, show_pers=True, resize=False, shrink=True):
        """
        Add the perspective to the current session

        @param klass a Perspective base class of the perspective to add
        @param show_pers choose to show the perspective
        @param resize if True child should resize when the paned is resized
        @param shrink if True child can be made smaller than its minimum size
                      request
        @return the perspective instance
        """

        pers = klass(self)
        self.perspectives.append(pers)

        if Prefs()['gui.expander.standard'].value:
            widget = gtk.Expander(pers.title)
            widget.add(pers)
            widget.set_expanded(True)
        else:
            widget = AnimatedExpander(pers.title, pers.icon,
                                      self.session_orientation)
            widget.add_widget(pers, show_pers)

        self.paned.add_child(widget, resize, shrink)

        widget.show()

        return pers

    def reload(self):
        self.reload_containers()
        self.reload_editors()

    def save(self):
        "@return True if the content is saved or False"
        return self._on_save(None)

    def save_as(self):
        return self._on_save_as(None)

    def save_session(self, fname, async=True):
        """
        Override this method to do the real save phase
        @param fname the filename on witch save the context will be saved
        @param async specify if you want to have an async saving in a separate
                     thread (new FileOperation) without freezing the gui.
        @return True if the content is saved or False (if async is False)
        """

        if not self.context.file_types:
            log.debug("Saving is disabled (%s)" % self.context)
            return False

        self.context.cap_file = fname

        if not async:
            return self.context.save()
        else:
            tab = PMApp().main_window.get_tab("OperationsTab")
            tab.tree.append_operation(FileOperation(self,
                                                    FileOperation.TYPE_SAVE))

    def save_session_async(self, fname):
        """
        Async save in a separate thread without returing the status.
        This is done by adding a new FileOperation in OperationsTab.
        """
        self.save_session(fname, async=True)

    def add_filters(self, dialog):
        """
        Override this method to customize the save dialog
        by adding filters or others
        """

        log.debug("Using default add_filters (%s)" % self.context)

        for name, pattern in self.context.file_types:
            filter = gtk.FileFilter()
            filter.set_name(name)
            filter.add_pattern(pattern)
            dialog.add_filter(filter)

    def _on_save(self, action):
        if self.context.cap_file:
            return self.save_session(self.context.cap_file)
        else:
            return self._on_save_as(None)

    def _on_save_as(self, action):
        if not self.context.file_types:
            log.debug("Saving is disabled (%s)" % self.context)
            return False

        ret = False
        dialog = self.__create_save_dialog()

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            ret = self.save_session(dialog.get_filename())

        dialog.hide()
        dialog.destroy()

        return ret

    def __create_save_dialog(self):
        dialog = gtk.FileChooserDialog(_('Save session file to'),
                self.get_toplevel(), gtk.FILE_CHOOSER_ACTION_SAVE,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                         gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))

        self.add_filters(dialog)

        return dialog

    def reload_containers(self, packet=None):
        for cont in self.container_cbs:
            cont(packet)

    def reload_editors(self):
        for edit in self.editor_cbs:
            edit()

    def set_active_packet(self, packet):
        if packet is self.packet:
            log.debug("Packets are the same ignoring updates")
        else:
            self.packet = packet
            self.reload_editors()

    def get_label(self):
        return self._label

    def __on_change_title(self):
        if self.context:
            self._label.label.set_text(self.context.title)

    label = property(get_label)
