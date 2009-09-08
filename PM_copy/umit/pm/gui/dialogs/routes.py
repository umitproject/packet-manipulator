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
Dialog to show/edit routing tables defined in the backend
"""

import re
import gtk

from umit.pm import backend
from umit.pm.core.i18n import _
from umit.pm.core.logger import log

class RouteList(gtk.VBox):
    def __init__(self):
        super(RouteList, self).__init__(False, 2)
        self.set_border_width(4)

        self.frame = gtk.Frame()
        self.frame.set_shadow_type(gtk.SHADOW_NONE)

        lbl = gtk.Label(_('<b>Routing table:</b>'))
        lbl.set_use_markup(True)

        self.frame.set_label_widget(lbl)

        self.ifaces = []

        for iface in backend.find_all_devs():
            self.ifaces.append(iface.name)

        self.ip_regex = re.compile(
                "\\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
                "\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
                "\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
                "\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b"
        )

        # A ListStore model to organize all possible interfaces
        self.iface_store = gtk.ListStore(str)

        for iface in self.ifaces:
            self.iface_store.append([iface])

        # Stock, network, netmask, gw, iface, out_ip
        self.store = gtk.ListStore(str, str, str, str, str, str)
        self.tree = gtk.TreeView(self.store)

        pix_renderer = gtk.CellRendererPixbuf()
        txt_renderer = gtk.CellRendererText()

        col = gtk.TreeViewColumn(_('Network'))
        col.pack_start(pix_renderer, False)
        col.pack_start(txt_renderer)

        col.set_attributes(pix_renderer, stock_id=0)
        col.set_attributes(txt_renderer, text=1)

        txt_renderer.set_property('editable', True)
        txt_renderer.connect('edited', self.__on_field_edited, 1)

        self.tree.append_column(col)

        idx = 2
        for name in (_('Netmask'), _('Gateway'), _('Interface'),
                     _('Output IP')):
            if idx == 4:
                renderer = gtk.CellRendererCombo()
                renderer.set_property('model', self.iface_store)
                renderer.set_property('text-column', 0)
            else:
                renderer = gtk.CellRendererText()

            renderer.set_property('editable', True)
            renderer.connect('edited', self.__on_field_edited, idx)

            col = gtk.TreeViewColumn(name, renderer, text=idx)
            self.tree.append_column(col)
            idx += 1

        self.tree.set_rules_hint(True)
        self.tree.set_reorderable(True)
        self.tree.connect('button-press-event', self.__on_context)

        sw = gtk.ScrolledWindow()

        sw.set_border_width(4)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.tree)

        self.frame.add(sw)
        self.pack_start(self.frame)

        self.__populate()

    def __populate(self):
        for net, msk, gw, iface, addr in backend.route_list():
            self.store.append(
                [gtk.STOCK_CONNECT, net, msk, gw, iface, addr]
            )

    def get_selected(self):
        model, iter = self.tree.get_selection().get_selected()

        if not iter:
            return

        # The first column is the name
        return model.get_value(iter, 1)

    def __on_field_edited(self, cell, path, new_text, id):
        iter = self.store.get_iter(path)

        if not iter:
            return

        if id in (1, 2, 3, 5) and self.ip_regex.match(new_text):
            # Ok we could set the new ip
            # (TODO: check for correct network id = 1)

            self.store.set_value(iter, id, new_text)
        elif id == 4 and new_text in self.ifaces:
            # Ok corret iface.

            self.store.set_value(iter, id, new_text)

    def __on_context(self, tree, evt):
        if evt.button != 3:
            return

        menu = gtk.Menu()

        labels = (_("Add new route"), _("Remove selected route"))
        stocks = (gtk.STOCK_ADD, gtk.STOCK_REMOVE)
        callbacks = (self.__on_route_add, self.__on_route_del)

        for lbl, stock, cb in zip(labels, stocks, callbacks):
            action = gtk.Action(None, lbl, None, stock)
            action.connect('activate', cb)

            menu.append(action.create_menu_item())

        menu.show_all()
        menu.popup(None, None, None, evt.button, evt.time)

    def __on_route_add(self, action):
        self.store.append(
            [gtk.STOCK_CONNECT, "", "", "", "", ""]
        )

    def __on_route_del(self, action):
        model, iter = self.tree.get_selection().get_selected()

        if iter:
            self.store.remove(iter)

    def commit_changes(self):
        # Here there's the hard part! we need to iterate over the
        # store get the values and saves back into the backend if
        # they're valid

        routes = []

        for row in self.store:
            net, mask, gw, iface, out = row[1], row[2], row[3], row[4], row[5]

            if net and mask and gw and iface and out and \
               self.ip_regex.match(net) and \
               self.ip_regex.match(mask) and \
               self.ip_regex.match(gw) and \
               self.ip_regex.match(out) and \
               iface in self.ifaces:

                log.debug("Adding route: %s %s %s %s %s" % (net, mask, gw,
                                                            iface, out))
                routes.append((net, mask, gw, iface, out))

        if routes:
            log.debug("Saving routes.")
            backend.reset_routes(routes)
        else:
            log.debug("Skipping route saving. I need at least one route")

class RoutesDialog(gtk.Dialog):
    def __init__(self, parent):
        super(RoutesDialog, self).__init__(
            _('Routes - PacketManipulator'), parent,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT,
             gtk.STOCK_CLOSE, gtk.RESPONSE_REJECT)
        )

        self.route_list = RouteList()
        self.vbox.pack_start(self.route_list)

        self.route_list.show_all()
        self.set_size_request(500, 200)

    def save(self):
        self.route_list.commit_changes()
