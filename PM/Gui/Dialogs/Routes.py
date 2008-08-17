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
Dialog to show/edit routing tables defined in the backend
"""

import gtk

from PM import Backend
from PM.Core.I18N import _

class RouteList(gtk.VBox):
    def __init__(self):
        super(RouteList, self).__init__(False, 2)
        self.set_border_width(4)

        self.frame = gtk.Frame()
        self.frame.set_shadow_type(gtk.SHADOW_NONE)

        lbl = gtk.Label(_('<b>Routing table:</b>'))
        lbl.set_use_markup(True)

        self.frame.set_label_widget(lbl)

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

        self.tree.append_column(col)
        
        idx = 2
        for name in (_('Netmask'), _('Gateway'), _('Interface'), _('Output IP')):
            col = gtk.TreeViewColumn(name, gtk.CellRendererText(), text=idx)
            self.tree.append_column(col)
            idx += 1
        
        self.tree.set_rules_hint(True)
        
        sw = gtk.ScrolledWindow()
        
        sw.set_border_width(4)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.tree)
        
        self.frame.add(sw)
        self.pack_start(self.frame)
        
        self.__populate()

    def __populate(self):
        for net, msk, gw, iface, addr in Backend.route_list():
            self.store.append(
                [gtk.STOCK_CONNECT, net, msk, gw, iface, addr]
            )
    
    def get_selected(self):
        model, iter = self.tree.get_selection().get_selected()

        if not iter:
            return
        
        # The first column is the name
        return model.get_value(iter, 1)

    # TODO: implement adding / removing / editing stuff

class RoutesDialog(gtk.Dialog):
    def __init__(self, parent):
        super(RoutesDialog, self).__init__(
            _('Routes - PacketManipulator'), parent,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_REJECT)
        )
        
        self.route_list = RouteList()
        self.vbox.pack_start(self.route_list)
        
        self.route_list.show_all()
        self.set_size_request(500, 200)
