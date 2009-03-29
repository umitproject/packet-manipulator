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
Interface capturing related dialogs and widgets
"""

import gtk
from sys import maxint

from PM import Backend
from PM.Core.I18N import _

class CaptureOptions(gtk.Expander):
    def __init__(self):
        super(CaptureOptions, self).__init__()

        self.set_border_width(4)
        self.set_label_widget(self.new_label(_('<b>Options</b>')))

        tbl = gtk.Table(8, 3, False)
        tbl.set_border_width(4)
        tbl.set_col_spacings(4)

        tbl.attach(self.new_label(_('Filter:')), 0, 1, 0, 1, yoptions=gtk.SHRINK)
        tbl.attach(self.new_label(_('Capture file:')), 0, 1, 1, 2, yoptions=gtk.SHRINK)
        tbl.attach(self.new_label(_('Min packet size:')), 0, 1, 2, 3, yoptions=gtk.SHRINK)
        tbl.attach(self.new_label(_('Max packet size:')), 0, 1, 3, 4, yoptions=gtk.SHRINK)
        tbl.attach(self.new_label(_('Stop after:')), 0, 1, 4, 5, yoptions=gtk.SHRINK)
        tbl.attach(self.new_label(_('Stop after:')), 0, 1, 5, 6, yoptions=gtk.SHRINK)
        tbl.attach(self.new_label(_('Stop after:')), 0, 1, 6, 7, yoptions=gtk.SHRINK)

        self.filter = gtk.Entry()

        btn = gtk.Button()
        btn.add(gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_BUTTON))
        btn.set_relief(gtk.RELIEF_NONE)

        hbox = gtk.HBox(False, 2)
        hbox.pack_start(self.filter)
        hbox.pack_start(btn, False, False)

        tbl.attach(hbox, 1, 2, 0, 1, yoptions=gtk.SHRINK)

        self.file = gtk.Entry()

        btn = gtk.Button()
        btn.add(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
        btn.set_relief(gtk.RELIEF_NONE)
        btn.connect('clicked', self.__on_select_capfile)

        hbox = gtk.HBox(False, 2)
        hbox.pack_start(self.file)
        hbox.pack_start(btn, False, False)

        tbl.attach(hbox, 1, 2, 1, 2, yoptions=gtk.SHRINK)

        min_size, self.min_size, self.min_check = \
                self.new_combo(68, maxint, [_("byte(s)")], True)
        max_size, self.max_size, self.max_check = \
                self.new_combo(68, maxint, [_("byte(s)")], True)

        stop_packets, self.stop_packets = self.new_combo(0, maxint, [_("packet(s)")])
        self.stop_size_box, self.stop_size = self.new_combo(0, 1024, [_("KB"), _("MB"), _("GB")])
        self.stop_time_box, self.stop_time = self.new_combo(0, maxint, [_("second(s)"), _("minute(s)"), _("hour(s)")])

        group = gtk.SizeGroup(gtk.SIZE_GROUP_BOTH)

        for widget in min_size, max_size, stop_packets, self.stop_size_box, self.stop_time_box:
            group.add_widget(widget)

        tbl.attach(min_size, 1, 2, 2, 3, yoptions=gtk.SHRINK)
        tbl.attach(max_size, 1, 2, 3, 4, yoptions=gtk.SHRINK)
        tbl.attach(stop_packets, 1, 2, 4, 5, yoptions=gtk.SHRINK)
        tbl.attach(self.stop_size_box, 1, 2, 5, 6, yoptions=gtk.SHRINK)
        tbl.attach(self.stop_time_box, 1, 2, 6, 7, yoptions=gtk.SHRINK)

        self.res_mac = gtk.CheckButton(_('Enable MAC name resolution'))
        self.res_name = gtk.CheckButton(_('Enable network name resolution'))
        self.res_transport = gtk.CheckButton(_('Enable transport name resolution'))

        self.gui_real = gtk.CheckButton(_('Update view in real mode'))
        self.gui_scroll = gtk.CheckButton(_('Automatic view scrolling'))

        self.net_promisc = gtk.CheckButton(_('Capture in promiscuous mode'))
        
        self.background = gtk.CheckButton(_('Start in background mode'))

        tbl.attach(self.gui_real, 2, 3, 0, 1, yoptions=gtk.SHRINK)
        tbl.attach(self.gui_scroll, 2, 3, 1, 2, yoptions=gtk.SHRINK)

        tbl.attach(self.net_promisc, 2, 3, 2, 3, yoptions=gtk.SHRINK)

        tbl.attach(self.res_mac, 2, 3, 3, 4, yoptions=gtk.SHRINK)
        tbl.attach(self.res_name, 2, 3, 4, 5, yoptions=gtk.SHRINK)
        tbl.attach(self.res_transport, 2, 3, 5, 6, yoptions=gtk.SHRINK)

        tbl.attach(self.background, 2, 3, 6, 7, yoptions=gtk.SHRINK)

        # Setting the default values
        self.res_mac.set_active(True)
        self.res_transport.set_active(True)
        self.gui_real.set_active(True)
        self.gui_scroll.set_active(True)
        self.net_promisc.set_active(True)

        self.add(tbl)

    def new_label(self, txt):
        lbl = gtk.Label(txt)
        lbl.set_use_markup(True)
        lbl.set_alignment(0, 0.5)

        return lbl

    def new_combo(self, min, max, lbls, check=False):
        if len(lbls) == 1:
            combo = gtk.Label(lbls[0])
            combo.set_alignment(0, 0.5)
        else:
            combo = gtk.combo_box_new_text()

            for lbl in lbls:
                combo.append_text(lbl)

            combo.set_active(0)

        spin = gtk.SpinButton(gtk.Adjustment(min, min, max, 1, 10))

        hbox = gtk.HBox(False, 2)
        hbox.pack_start(spin)
        hbox.pack_start(combo)

        if check:
            chk = gtk.CheckButton()
            hbox.pack_start(chk, False, False)

            chk.connect('toggled',
                lambda w, b: b.set_sensitive(w.get_active()), spin)

            spin.set_sensitive(False)

            return hbox, spin, chk

        return hbox, spin

    def __on_select_capfile(self, btn):
        pass

    def get_options(self):
        filter = self.filter.get_text()
        capfile = self.file.get_text()

        if not filter:
            filter = None

        if not capfile:
            capfile = None

        if self.min_check.get_active():
            minsize = self.min_size.get_value_as_int()
        else:
            minsize = 0

        if self.max_check.get_active():
            maxsize = self.max_size.get_value_as_int()
        else:
            maxsize = 0

        scount = self.stop_packets.get_value_as_int()

        stime = self.stop_time.get_value_as_int()
        factor = self.stop_time_box.get_children()[1].get_active()

        if factor == 0:
            factor = 1
        elif factor == 1:
            factor = 60
        elif factor == 2:
            factor = 60 ** 2

        stime = stime * factor
        
        ssize = self.stop_size.get_value_as_int()
        factor = self.stop_size_box.get_children()[1].get_active()

        if factor == 0:
            factor = 1024
        elif factor == 1:
            factor = 1024 ** 2
        elif factor == 2:
            factor = 1024 ** 3

        ssize = ssize * factor

        real = self.gui_scroll.get_active()
        scroll = self.gui_scroll.get_active()
        resmac = self.res_mac.get_active()
        resname = self.res_name.get_active()
        restransport = self.res_transport.get_active()
        promisc = self.net_promisc.get_active()
        background = self.background.get_active()

        dct = {
            'filter'       : filter,
            'minsize'      : minsize,
            'maxsize'      : maxsize,
            'capfile'      : capfile,
            'scount'       : scount,
            'stime'        : stime,
            'ssize'        : ssize,
            'real'         : real,
            'scroll'       : scroll,
            'resmac'       : resmac,
            'resname'      : resname,
            'restransport' : restransport,
            'promisc'      : promisc,
            'background'   : background
        }

        return dct

class InterfaceList(gtk.VBox):
    def __init__(self):
        super(InterfaceList, self).__init__(False, 2)
        self.set_border_width(4)

        self.frame = gtk.Frame()
        self.frame.set_shadow_type(gtk.SHADOW_NONE)

        lbl = gtk.Label(_('<b>Avaiable Interfaces:</b>'))
        lbl.set_use_markup(True)

        self.frame.set_label_widget(lbl)

        # Stock, Name, Desc, IP
        self.store = gtk.ListStore(str, str, str, str)
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
        for name in (_('Description'), _('IP')):
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
        for iface in Backend.find_all_devs():
            self.store.append(
                [gtk.STOCK_CONNECT, iface.name, iface.description, iface.ip]
            )
    
    def get_selected(self):
        model, iter = self.tree.get_selection().get_selected()

        if not iter:
            return
        
        # The first column is the name
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
        self.options = CaptureOptions()

        self.vbox.pack_start(self.if_list)
        self.vbox.pack_start(self.options, False, False)

        self.if_list.tree.connect('row-activated',
            lambda tree, path, view, diag:
                diag.response(gtk.RESPONSE_ACCEPT), self)

        self.show_all()
        self.set_size_request(620, 400)

    def get_selected(self):
        "@return the selected interface for sniffing or None"
        return self.if_list.get_selected()

    def get_options(self):
        "@return the actived options in a dict"
        return self.options.get_options()
