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
from umitCore.I18N import _

class InterfaceList(gtk.VBox):
    def __init__(self):
        super(InterfaceList, self).__init__(False, 2)
        self.set_border_width(4)

        self.frame = gtk.Frame()
        self.frame.set_shadow_type(gtk.SHADOW_NONE)

        lbl = gtk.Label(_('<b>Avaiable Interfaces:</b>'))
        lbl.set_use_markup(True)

        self.frame.set_label_widget(lbl)

        # Stock, Name, Desc, IP, Packets
        self.store = gtk.ListStore(str, str, str, str, int)
        self.tree = gtk.TreeView(self.store)

        pix_renderer = gtk.CellRendererPixbuf()
        txt_renderer = gtk.CellRendererText()

        col = gtk.TreeViewColumn(_('Name'))
        col.pack_start(pix_renderer, False)
        col.pack_start(txt_renderer)
        
        col.set_attributes(pix_renderer, stock_id=0)
        col.set_attributes(txt_renderer, text=1)

        self.tree.append_column(col)
        
        idx = 2
        for name in (_('Description'), _('IP'), _('Packets')):
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
        # TODO: implement me
        pass
    
    def get_selected(self):
        if not self.tree.get_selection().get_selected():
            return None
        
        # The first column is the name
        model, iter = self.tree.get_selection().get_selected()
        return model.get_value(iter, 1)

class InterfaceDialog(gtk.Dialog):
    def __init__(self, parent):
        super(InterfaceDialog, self).__init__(
            _('Interfaces - PacketManipulator'), parent,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_REJECT,
             gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT)
        )
        
        self.if_list = InterfaceList()
        self.vbox.pack_start(self.if_list)
        
        self.if_list.show_all()
        self.set_size_request(500, 200)
    
    def get_selected(self):
        "@return the selected interface for sniffing or None"
        return self.if_list.get_selected()