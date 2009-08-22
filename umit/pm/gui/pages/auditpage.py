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

import gtk
import gobject

from umit.pm.core.i18n import _
from umit.pm.core.logger import log

from umit.pm.gui.core.icons import get_pixbuf
from umit.pm.gui.pages.base import Perspective
from umit.pm.core.auditutils import AuditOperation
from umit.pm.manager.preferencemanager import Prefs

ITEM_OPEN,        \
ITEM_RESUME,      \
ITEM_PAUSE,       \
ITEM_STOP,        \
ITEM_RESTART,     \
ITEM_RECONFIGURE, \
ITEM_REMOVE = range(7)

def get_operation(func):
    """Simple decorator to get operation from gtk.TreeView selection"""

    def proxy(self, *args):
        model, iter = self.tree.get_selection().get_selected()

        if iter:
            operation = model.get_value(iter, 0)
            return func(self, args[0], operation)

    return proxy

class AuditTree(gtk.HBox):
    def __init__(self):
        super(AuditTree, self).__init__(False, 2)

        self.store = gtk.ListStore(object)
        self.tree = gtk.TreeView(self.store)

        self.__create_columns()

        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        self.toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)

        self.__create_buttons()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.tree)

        self.pack_start(sw)
        self.pack_start(self.toolbar, False, False)

        self.tree.get_selection().connect('changed', self.__on_sel_changed)
        self.__on_sel_changed(self.tree.get_selection())

        self.timeout_id = None
        self.timeout_update()

    def __create_columns(self):
        col = gtk.TreeViewColumn(_('Audits'))

        col.set_expand(True)
        col.set_resizable(True)
        col.set_resizable(True)

        col.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)

        rend = gtk.CellRendererPixbuf()
        col.pack_start(rend, False)
        col.set_cell_data_func(rend, self.__pix_data_func)

        rend = gtk.CellRendererText()
        col.pack_start(rend)
        col.set_cell_data_func(rend, self.__text_data_func)

        self.tree.append_column(col)

        rend = gtk.CellRendererProgress()
        col = gtk.TreeViewColumn(_('Status'), rend)

        col.set_expand(False)
        col.set_resizable(True)
        col.set_fixed_width(150)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

        col.set_cell_data_func(rend, self.__progress_data_func)

        self.tree.append_column(col)

        self.tree.set_rules_hint(True)
        self.icon_operation = get_pixbuf('operation_small')

    def __create_buttons(self):
        labels = (
            _('Open'),
            _('Resume operation'),
            _('Pause operation'),
            _('Stop operation'),
            _('Restart operation'),
            _('Reconfigure audit'),
            _('Remove finished')
        )

        stocks = (
            gtk.STOCK_OPEN,
            gtk.STOCK_MEDIA_PLAY,
            gtk.STOCK_MEDIA_PAUSE,
            gtk.STOCK_MEDIA_STOP,
            gtk.STOCK_REFRESH,
            gtk.STOCK_PREFERENCES,
            gtk.STOCK_CLEAR
        )

        callbacks = (
            self.__on_open,
            self.__on_resume,
            self.__on_pause,
            self.__on_stop,
            self.__on_restart,
            self.__on_reconfigure,
            self.__on_clear
        )

        self.tool_items = []

        for lbl, stock, cb in zip(labels, stocks, callbacks):
            action =  gtk.Action(None, lbl, None, stock)
            action.connect('activate', cb)

            item = action.create_tool_item()

            self.tool_items.append(item)
            self.toolbar.insert(item, -1)

    def is_someone_running(self):
        def check_running(model, path, iter, lst):
            op = model.get_value(iter, 0)

            if op.state == op.RUNNING:
                lst[0] = True
                return True

        lst = [False]
        self.store.foreach(check_running, lst)

        return lst[0]

    def timeout_update(self):
        if not self.timeout_id and self.is_someone_running():
            # We're not empty so we can set a timeout callback to update all
            # actives iters at the same time reducing the CPU usage.

            self.timeout_id = gobject.timeout_add(
                Prefs()['gui.operationstab.updatetimeout'].value or 500,
                self.__timeout_cb
            )

            log.debug('Adding a timeout function to update the AuditTree')

    def __timeout_cb(self):
        def update(model, path, iter, idx):
            operation = model.get_value(iter, 0)

            if operation.state == operation.RUNNING:
                model.row_changed(path, iter)
                idx[0] += 1

        idx = [0]
        self.store.foreach(update, idx)

        if not idx[0]:
            log.debug('Removing the timeout callback for AuditTree updates')
            self.timeout_id = None
            return False

        return True

    def __pix_data_func(self, col, cell, model, iter):
        cell.set_property('pixbuf', self.icon_operation)

    def __text_data_func(self, col, cell, model, iter):
        operation = model.get_value(iter, 0)
        cell.set_property('markup', operation.get_summary())

    def __progress_data_func(self, col, cell, model, iter):
        operation = model.get_value(iter, 0)

        if operation.get_percentage() != None:
            cell.set_property('value', operation.get_percentage())
            cell.set_property('pulse', -1)
        else:
            cell.set_property('value', 0)
            cell.set_property('pulse', operation.percentage)

    def __on_sel_changed(self, selection):
        model, iter = selection.get_selected()

        if iter:
            operation = model.get_value(iter, 0)

            if operation.state == operation.RUNNING:
                self.tool_items[ITEM_RESUME].set_sensitive(False)
                self.tool_items[ITEM_PAUSE].set_sensitive(operation.has_pause)
                self.tool_items[ITEM_STOP].set_sensitive(operation.has_stop)
            else:
                self.tool_items[ITEM_RESUME].set_sensitive(operation.has_pause)
                self.tool_items[ITEM_PAUSE].set_sensitive(False)
                self.tool_items[ITEM_STOP].set_sensitive(False)

            self.tool_items[ITEM_RESTART].set_sensitive(operation.has_restart)
            self.tool_items[ITEM_RECONFIGURE].set_sensitive(
                operation.has_reconfigure)

            self.tool_items[ITEM_OPEN].set_sensitive(True)
            self.tool_items[ITEM_REMOVE].set_sensitive(True)
        else:
            for item in self.tool_items:
                item.set_sensitive(False)

    # Public functions

    def append_operation(self, operation, start=True):
        """
        Append an operation to the store

        @param operation an AuditOperation object
        @param start if the operation should be started
        """

        assert (isinstance(operation, AuditOperation))

        iter = self.store.append([operation])

        if start:
            operation.start()

        self.timeout_update()

    def remove_operation(self, operation):
        """
        Remove an operation from the store

        @param operation the AuditOperation to remove
        """

        if not isinstance(operation, AuditOperation):
            return

        def remove(model, path, iter, operation):
            if model.get_value(iter, 0) is operation:
                model.remove(iter)
                return True

        self.store.foreach(remove, operation)

    # Callbacks section

    @get_operation
    def __on_open(self, action, operation):
        operation.activate()

    @get_operation
    def __on_resume(self, action, operation):
        operation.resume()

    @get_operation
    def __on_pause(self, action, operation):
        operation.pause()

    @get_operation
    def __on_stop(self, action, operation):
        operation.stop()

    @get_operation
    def __on_restart(self, action, operation):
        operation.restart()

    @get_operation
    def __on_reconfigure(self, action, operation):
        operation.reconfigure()

    def __on_clear(self, action):
        def scan(model, path, iter, lst):
            op = model.get_value(iter, 0)

            if op.state == op.NOT_RUNNING:
                lst.append(gtk.TreeRowReference(model, path))

        lst = []
        self.store.foreach(scan, lst)

        for ref in lst:
            self.store.remove(self.store.get_iter(ref.get_path()))

class AuditPage(Perspective):
    icon = gtk.STOCK_CONNECT
    title = _('Audit perspective')

    def create_ui(self):
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.tree = AuditTree()
        self.pack_start(self.tree)
        self.show_all()

    def reload(self):
        print "Reloading the tree"
