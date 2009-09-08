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
The path page for PluginWindow
"""

import gtk

from umit.pm.core.i18n import _
from umit.pm.core.const import PIXMAPS_DIR

from umit.pm.gui.core.icons import get_pixbuf
from umit.pm.gui.plugins.engine import PluginEngine

class PathPage(gtk.VBox):
    """
    The PathPage widget
    """

    def __init__(self, parent):
        gtk.VBox.__init__(self, False, 2)

        self.p_window = parent

        self.set_spacing(6)
        self.__create_widgets()
        self.__pack_widgets()

    def __create_widgets(self):
        pix_cell = gtk.CellRendererPixbuf()
        txt_cell = gtk.CellRendererText()

        self.path_store = gtk.ListStore(gtk.gdk.Pixbuf, str)
        self.path_view = gtk.TreeView(self.path_store)

        col = gtk.TreeViewColumn('')
        col.pack_start(pix_cell, False)
        col.pack_start(txt_cell)

        col.add_attribute(pix_cell, 'pixbuf', 0)
        col.add_attribute(txt_cell, 'text', 1)

        self.path_view.append_column(col)
        self.path_view.set_headers_visible(False)

        # Enable drag moving
        entries = [('PathView', gtk.TARGET_SAME_WIDGET, 0)]

        self.path_view.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            entries,
            gtk.gdk.ACTION_MOVE
        )

        self.path_view.enable_model_drag_dest(
            entries,
            gtk.gdk.ACTION_MOVE
        )

        self.path_view.connect(
            'drag-data-received', PathPage.__on_drag_data_received
        )

        self.path_add = gtk.Button(stock=gtk.STOCK_ADD)
        self.path_remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.path_save = gtk.Button(stock=gtk.STOCK_SAVE)

        self.path_icon = get_pixbuf('paths_small')

        # Connect callbacks
        self.path_add.connect('clicked', self.__on_add_path)
        self.path_remove.connect('clicked', self.__on_remove_path)
        self.path_save.connect('clicked', self.__on_save_path)

    def __pack_widgets(self):

        scrollwin = gtk.ScrolledWindow()
        scrollwin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scrollwin.add(self.path_view)

        self.pack_start(scrollwin)

        hbb = gtk.HButtonBox()
        hbb.set_layout(gtk.BUTTONBOX_END)
        hbb.pack_start(self.path_add)
        hbb.pack_start(self.path_remove)
        hbb.pack_start(self.path_save)

        self.pack_start(hbb, False, False)

    def clear(self):
        "Clear the store"
        self.path_store.clear()

    def populate(self):
        "Populate the store"
        for path, (idx, reader) in self.p_window.engine.paths.items():
            self.path_store.insert(idx, [self.path_icon, path])

    #
    # Callabacks

    @staticmethod
    def __on_drag_data_received(view, ctx, x, y, data, info, evt_time):
        """
        Callback for managing drag/drop events

        Indipendent from self so make static
        """

        ret = view.get_dest_row_at_pos(x, y)

        if ret:
            path, pos = ret
        else:
            # Select the last path and set the proper pos
            path = (len(view.get_model()) - 1, )
            pos = gtk.TREE_VIEW_DROP_AFTER

        model, source = view.get_selection().get_selected()
        target = model.get_iter(path)

        source = model[source]

        if pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE or \
           pos == gtk.TREE_VIEW_DROP_BEFORE:
            new = model.insert_before(target, source)
        elif pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER or \
             pos == gtk.TREE_VIEW_DROP_AFTER:
            new = model.insert_after(target, source)

        ctx.finish(success=True, del_=True, time=evt_time)

    def __on_add_path(self, widget):
        "Add a path to store"

        dialog = gtk.FileChooserDialog(
            _("Select a Plugin path"),
            self.p_window,
            gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        )

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            path = dialog.get_filename()

            # Check for duplicates
            for i in self.path_store:
                if i[1] == path:
                    return dialog.destroy()

            self.path_store.append([self.path_icon, path])

        dialog.destroy()

    def __on_remove_path(self, widget):
        "Remove selected path from store"
        model, iter = self.path_view.get_selection().get_selected()
        if iter:
            model.remove(iter)

    def __on_save_path(self, widget):
        "Save the paths in umit configuration file without recaching"

        # Simple create a list from ListStore
        # and then save to umit configuration file

        ret = []

        def add_to(model, path, titer, ret):
            ret.append(model.get_value(titer, 1))

        self.path_store.foreach(add_to, ret)

        self.p_window.engine.plugins.paths = ret
        self.p_window.engine.plugins.save_changes()

        PluginEngine().recache()

        if self.p_window.plug_page.clear(False) > 0:
            # Warn the user
            self.p_window.animated_bar.label = _("Remember that you have to "
                                                 "restart PacketManipulator to changes makes"
                                                 ". Plugins disable pending.")
            self.p_window.animated_bar.start_animation(True)

            def block_row(row, blah):
                row.activatable = False
                row.message = _("Need PacketManipulator restart to disable.")

            self.p_window.plug_page.richlist.foreach(block_row, None)

        self.p_window.plug_page.populate()
        self.p_window.audit_page.populate()
