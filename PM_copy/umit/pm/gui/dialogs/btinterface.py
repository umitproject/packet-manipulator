#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
#
# Author: Quek Shu Yang <quekshuy@gmail.com>
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
from sys import maxint

from umit.pm import backend

from umit.pm.core.i18n import _
from umit.pm.core.logger import log

from umit.pm.manager.preferencemanager import Prefs
from umit.pm.higwidgets.higdialogs import HIGAlertDialog
from umit.pm.gui.dialogs.interface import CaptureOptions, InterfaceList, InterfaceDialog

from umit.pm.backend.abstract.basecontext.btsniff import BT_OPTIONS_PINCRACK

class BtCaptureOptions(CaptureOptions):
    
    def __init__(self):
        
        super(BtCaptureOptions, self).__init__()
        
        # Start on a clean slate but keep the helper methods in
        # CaptureOptions
        self.__clear_children()
        self.set_label_widget(self.new_label(_('<b>Options</b>')))
        
        tbl = gtk.Table(6, 4, False)
        tbl.set_border_width(4)
        tbl.set_col_spacings(4)
        
        tbl.attach(self.new_label(_('Master Address:')),
                   0, 1, 0, 1, yoptions=gtk.SHRINK)
        
        tbl.attach(self.new_label(_('Slave Address:')),
                   0, 1, 1, 2, yoptions=gtk.SHRINK)

        tbl.attach(self.new_label(_('Capture file:')),
                   0, 1, 2, 3, yoptions=gtk.SHRINK)

        tbl.attach(self.new_label(_('Stop after:')),
                   0, 1, 3, 4, yoptions=gtk.SHRINK)

        tbl.attach(self.new_label(_('Stop after:')),
                   0, 1, 4, 5, yoptions=gtk.SHRINK)
        
        tbl.attach(self.new_label(_('Generate PIN:')), 
                   0, 1, 5, 6, yoptions=gtk.SHRINK)


        self.master_entries = self.__new_add_entry()
        self.slave_entries = self.__new_add_entry() 

        tbl.attach(self.master_entries, 1, 2, 0, 1, yoptions=gtk.SHRINK)
        tbl.attach(self.slave_entries, 1, 2, 1, 2, yoptions=gtk.SHRINK)

        self.file = gtk.Entry()

        btn = gtk.Button()
        btn.add(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
        btn.set_relief(gtk.RELIEF_NONE)
        btn.connect('clicked', self.__on_select_capfile)

        hbox = gtk.HBox(0, False)
        hbox.pack_start(btn, False, False)

        tbl.attach(self.file, 1, 2, 2, 3, yoptions=gtk.SHRINK)
        tbl.attach(hbox, 2, 3, 2, 3, yoptions=gtk.SHRINK)

        self.stop_packets, self.stop_packets_lbl = \
            self.new_combo(0, maxint, [_("packet(s)")])

        self.stop_time, self.stop_time_lbl = \
            self.new_combo(0, maxint,
                           [_("second(s)")])

        tbl.attach(self.stop_packets, 1, 2, 3, 4)
        tbl.attach(self.stop_packets_lbl, 2, 3, 3, 4, yoptions=gtk.SHRINK)

        tbl.attach(self.stop_time, 1, 2, 4, 5)
        tbl.attach(self.stop_time_lbl, 2, 3, 4, 5, yoptions=gtk.SHRINK)

        self.pinmethod = gtk.combo_box_new_text()
        
        # Set options for pincracking        
        for p_method in BT_OPTIONS_PINCRACK:
            self.pinmethod.append_text(_(p_method))
        
        self.pinmethod.set_active(0)
        
        btn = gtk.Button()
        btn.add(gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_BUTTON))
        btn.set_relief(gtk.RELIEF_NONE)
        btn.set_tooltip_markup(_('Pin-cracking may be time-intensive depending on '
                                 'the length of PIN.'))

        hbox = gtk.HBox(0, False)
        hbox.pack_start(btn, False, False)        
        
        tbl.attach(self.pinmethod, 1, 2, 5, 6, yoptions=gtk.SHRINK)
        tbl.attach(hbox, 2, 3, 5, 6, yoptions=gtk.SHRINK)

        self.res_mac = gtk.CheckButton(_('Enable MAC name resolution'))
        self.gui_real = gtk.CheckButton(_('Update view in real mode'))
        self.gui_scroll = gtk.CheckButton(_('Automatic view scrolling'))

        tbl.attach(self.gui_real, 3, 4, 0, 1)
        tbl.attach(self.gui_scroll, 3, 4, 1, 2)

        tbl.attach(self.res_mac, 3, 4, 2, 3)
        
        # Setting the default values
        self.res_mac.set_active(True)
        self.res_transport.set_active(True)
        self.gui_real.set_active(True)
        self.gui_scroll.set_active(True)
        self.net_promisc.set_active(True)

        self.add(tbl)
    
    def __new_add_entry(self):
        
        hbox = gtk.HBox(0, False)
   
        for i in range(6):
            entry = gtk.Entry()
            entry.set_max_length(2)
            entry.set_width_chars(2)
            hbox.pack_start(entry, False, False)
            if i < 5: 
                hbox.pack_start(self.new_label(_(':')), False, False)
        
        return hbox
    
    def __clear_children(self):
        """
            Clear all contained widgets
        """
        for child in self.get_children():
            self.remove(child)

    def __on_select_capfile(self, btn):
        d = gtk.FileChooserDialog(_('Select a capture file'),
                                  self.get_toplevel(),
                                  gtk.FILE_CHOOSER_ACTION_SAVE,
                                  (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
                                 )

        path = self.file.get_text()

        if path and os.path.exists(path):
            d.set_filename(path)

        response_id = d.run()
        d.hide()

        if response_id == gtk.RESPONSE_ACCEPT:
            self.file.set_text(d.get_filename())

        d.destroy()

    def get_options(self):
        
        capfile = self.file.get_text()

        if not capfile:
            capfile = None

        scount = self.stop_packets.get_value_as_int()
        stime = self.stop_time.get_value_as_int()
        factor = 0

        if factor == 0:
            factor = 1
        elif factor == 1:
            factor = 60
        elif factor == 2:
            factor = 60 ** 2

        stime = stime * factor

        real = self.gui_scroll.get_active()
        scroll = self.gui_scroll.get_active()
        resmac = self.res_mac.get_active()
        pinmethod = self.pinmethod.get_active()
        

        # Get master and slave addresses
        master_add = self.__get_addresses(self.master_entries) 
        slave_add = self.__get_addresses(self.slave_entries)
        
        log.debug('master_add: %s'% str(master_add))
        log.debug('slave_add: %s' % str(slave_add))

        dct = {
            'capfile'      : capfile,
            'scount'       : scount,
            'stime'        : stime,
#            'real'         : real,
#            'scroll'       : scroll,
#            'resmac'       : resmac,
            'master_add'   : master_add,
            'slave_add'    : slave_add,
            'pinmethod'    : pinmethod
        }

        return dct
    
    def __get_addresses(self, add_hbox):
        lst, children = [], add_hbox.get_children()
        for i in range(0, len(children) + 1, 2):
            spart = children[i].get_text()
            if spart=='': spart = '00'
            # TODO: We should validate input here
            part = int(spart, 16)
            lst.append(part)
        return lst
        

class BtInterfaceList(InterfaceList):
    def __init__(self):

        super(InterfaceList, self).__init__(False, 2)
        self.set_border_width(4)

        self.frame = gtk.Frame()
        self.frame.set_shadow_type(gtk.SHADOW_NONE)

        lbl = gtk.Label(_('<b>Available Interfaces:</b>'))
        lbl.set_use_markup(True)

        self.frame.set_label_widget(lbl)

        # Stock, Name, Desc, 
        self.store = gtk.ListStore(str, str, str)
        self.tree = gtk.TreeView(self.store)

        pix_renderer = gtk.CellRendererPixbuf()
        txt_renderer = gtk.CellRendererText()

        col = gtk.TreeViewColumn(_('Name'))
        col.pack_start(pix_renderer, False)
        col.pack_start(txt_renderer)

        col.set_attributes(pix_renderer, stock_id=0)
        col.set_attributes(txt_renderer, text=1)

        self.tree.append_column(col)

        col = gtk.TreeViewColumn(_('Description'), gtk.CellRendererText(), text=2)
        self.tree.append_column(col)

        self.tree.set_rules_hint(True)

        sw = gtk.ScrolledWindow()

        sw.set_border_width(4)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.tree)

        self.frame.add(sw)
        self.pack_start(self.frame)

class BtInterfaceDialog(InterfaceDialog):
    
    def __init__(self, parent):
        super(InterfaceDialog, self).__init__(
            _('Bluetooth HCI Interfaces - PacketManipulator'), parent,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_REJECT,
             gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT)
        )

        self.if_list = BtInterfaceList()
        self.options = BtCaptureOptions()

        self.vbox.pack_start(self.if_list)
        self.vbox.pack_start(self.options, False, False)

        for widget in self.action_area:
            if self.get_response_for_widget(widget) == gtk.RESPONSE_ACCEPT:
                widget.set_sensitive(False)

                self.if_list.tree.get_selection().connect(
                    'changed',
                    self.__on_selection_changed,
                    widget
                )

#                self.options.method.connect(
#                    'changed',
#                    self.__on_method_changed,
#                    widget
#                )

                break

        self.if_list.tree.connect('row-activated',
            lambda tree, path, view, diag:
                diag.response(gtk.RESPONSE_ACCEPT), self)

        # Method only one method right now
#        method = 0
#        self.options.method.set_active(method)

        self.connect('response', self.__on_response)
        self.__populate()

        self.show_all()
        self.if_list.set_size_request(600, 200)

    def get_selected(self):
        "@return the selected interface for sniffing or None"
        return self.if_list.get_selected()

    def get_options(self):
        "@return the actived options in a dict"
        return self.options.get_options()

    def __on_selection_changed(self, selection, btn):
        if selection.get_selected()[1]:
            btn.set_sensitive(True)
        else:
            btn.set_sensitive(False)

    def __populate(self):
    
        self.if_list.store.clear()
        
        #TODO: check if any of the interfaces are in RAW
        # mode. If not, display error
        
        for iface in backend.get_device_list():
            self.if_list.store.append(
                [gtk.STOCK_CONNECT, iface.name, iface.btadd]
            )

    def __on_method_changed(self, combo, btn):
        
        if combo.get_active() == 1:
            btn.set_sensitive(True)
        else:
            self.__on_selection_changed(self.if_list.tree.get_selection(), btn)

    def __on_response(self, dialog, response_id):
        # TODO: error checking of inputs
        log.debug("BtInterfaceDialog: __on_response")
        
