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
Interface capturing related dialogs and widgets
"""

import os.path
from sys import maxint

import gtk

from umit.pm import backend

from umit.pm.core.i18n import _
from umit.pm.core.logger import log

from umit.pm.manager.preferencemanager import Prefs
from umit.pm.higwidgets.higdialogs import HIGAlertDialog

class CaptureOptions(gtk.Expander):
    def __init__(self):
        super(CaptureOptions, self).__init__()

        self.set_border_width(4)
        self.set_label_widget(self.new_label(_('<b>Options</b>')))

        tbl = gtk.Table(8, 4, False)
        tbl.set_border_width(4)
        tbl.set_col_spacings(4)

        tbl.attach(self.new_label(_('Filter:')),
                   0, 1, 0, 1, yoptions=gtk.SHRINK)

        tbl.attach(self.new_label(_('Capture file:')),
                   0, 1, 1, 2, yoptions=gtk.SHRINK)

        tbl.attach(self.new_label(_('Capture method:')),
                   0, 1, 2, 3, yoptions=gtk.SHRINK)

        tbl.attach(self.new_label(_('Min packet size:')),
                   0, 1, 3, 4, yoptions=gtk.SHRINK)

        tbl.attach(self.new_label(_('Max packet size:')),
                   0, 1, 4, 5, yoptions=gtk.SHRINK)

        tbl.attach(self.new_label(_('Stop after:')),
                   0, 1, 5, 6, yoptions=gtk.SHRINK)

        tbl.attach(self.new_label(_('Stop after:')),
                   0, 1, 6, 7, yoptions=gtk.SHRINK)

        tbl.attach(self.new_label(_('Stop after:')),
                   0, 1, 7, 8, yoptions=gtk.SHRINK)

        self.filter = gtk.Entry()

        btn = gtk.Button()
        btn.add(gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_BUTTON))
        btn.set_relief(gtk.RELIEF_NONE)
        btn.set_tooltip_markup(_('Enter a pcap filter expression here.\nSee '
            'also <span foreground="blue">'
            'http://www.cs.ucr.edu/~marios/ethereal-tcpdump.pdf</span>'))

        hbox = gtk.HBox(0, False)
        hbox.pack_start(btn, False, False)

        tbl.attach(self.filter, 1, 2, 0, 1, yoptions=gtk.SHRINK)
        tbl.attach(hbox, 2, 3, 0, 1, yoptions=gtk.SHRINK)

        self.file = gtk.Entry()

        btn = gtk.Button()
        btn.add(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
        btn.set_relief(gtk.RELIEF_NONE)
        btn.connect('clicked', self.__on_select_capfile)

        hbox = gtk.HBox(0, False)
        hbox.pack_start(btn, False, False)

        tbl.attach(self.file, 1, 2, 1, 2, yoptions=gtk.SHRINK)
        tbl.attach(hbox, 2, 3, 1, 2, yoptions=gtk.SHRINK)

        self.method = gtk.combo_box_new_text()
        self.method.append_text(_('Native'))
        self.method.append_text(_('Virtual interface'))
        self.method.append_text(_('tcpdump helper'))
        self.method.append_text(_('dumpcap helper'))

        self.method.set_active(0)

        tbl.attach(self.method, 1, 2, 2, 3, yoptions=gtk.SHRINK)

        self.min_size, self.min_combo = \
                self.new_combo(68, maxint, [_("byte(s)")], True)

        self.max_size, self.max_combo = \
                self.new_combo(68, maxint, [_("byte(s)")], True)

        self.stop_packets, stop_packets_lbl = \
            self.new_combo(0, maxint, [_("packet(s)")])

        self.stop_size, self.stop_size_combo = \
            self.new_combo(0, 1024, [_("KB"), _("MB"), _("GB")])

        self.stop_time, self.stop_time_combo = \
            self.new_combo(0, maxint,
                           [_("second(s)"), _("minute(s)"), _("hour(s)")])

        tbl.attach(self.min_size, 1, 2, 3, 4)
        tbl.attach(self.min_combo, 2, 3, 3, 4, yoptions=gtk.SHRINK)

        tbl.attach(self.max_size, 1, 2, 4, 5)
        tbl.attach(self.max_combo, 2, 3, 4, 5, yoptions=gtk.SHRINK)

        tbl.attach(self.stop_packets, 1, 2, 5, 6)
        tbl.attach(stop_packets_lbl, 2, 3, 5, 6, yoptions=gtk.SHRINK)

        tbl.attach(self.stop_size, 1, 2, 6, 7)
        tbl.attach(self.stop_size_combo, 2, 3, 6, 7, yoptions=gtk.SHRINK)

        tbl.attach(self.stop_time, 1, 2, 7, 8)
        tbl.attach(self.stop_time_combo, 2, 3, 7, 8, yoptions=gtk.SHRINK)

        self.res_mac = gtk.CheckButton(_('Enable MAC name resolution'))
        self.res_name = gtk.CheckButton(_('Enable network name resolution'))
        self.res_transport = gtk.CheckButton(_('Enable transport name ' \
                                                'resolution'))

        self.gui_real = gtk.CheckButton(_('Update view in real mode'))
        self.gui_scroll = gtk.CheckButton(_('Automatic view scrolling'))

        self.net_promisc = gtk.CheckButton(_('Capture in promiscuous mode'))

        self.background = gtk.CheckButton(_('Start in background mode'))

        self.audits = gtk.CheckButton(_('Enable audits'))

        tbl.attach(self.gui_real, 3, 4, 0, 1)
        tbl.attach(self.gui_scroll, 3, 4, 1, 2)

        tbl.attach(self.net_promisc, 3, 4, 2, 3)

        tbl.attach(self.res_mac, 3, 4, 3, 4)
        tbl.attach(self.res_name, 3, 4, 4, 5)
        tbl.attach(self.res_transport, 3, 4, 5, 6)

        tbl.attach(self.background, 3, 4, 6, 7)
        tbl.attach(self.audits, 3, 4, 7, 8)

        # Setting the default values
        self.res_mac.set_active(True)
        self.res_transport.set_active(True)
        self.gui_real.set_active(True)
        self.gui_scroll.set_active(True)
        self.net_promisc.set_active(True)

        if Prefs()['backend.system.sniff.audits'].value == True:
            self.audits.set_active(True)

        self.add(tbl)

    def new_label(self, txt):
        lbl = gtk.Label(txt)
        lbl.set_use_markup(True)
        lbl.set_alignment(0, 0.5)

        return lbl

    def new_combo(self, min, max, lbls, check=False):
        spin = gtk.SpinButton(gtk.Adjustment(min, min, max, 1, 10))

        if len(lbls) == 1:
            if check:
                combo = gtk.CheckButton(lbls[0])

                combo.connect('toggled',
                              lambda w, b: b.set_sensitive(w.get_active()),
                              spin)

                spin.set_sensitive(False)
            else:
                combo = gtk.Label(lbls[0])
                combo.set_alignment(0, 0.5)
        else:
            combo = gtk.combo_box_new_text()

            for lbl in lbls:
                combo.append_text(lbl)

            combo.set_active(0)

        return spin, combo

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
        filter = self.filter.get_text()
        capfile = self.file.get_text()

        if not filter:
            filter = None

        if not capfile:
            capfile = None

        method = self.method.get_active()

        if self.min_combo.get_active():
            minsize = self.min_size.get_value_as_int()
        else:
            minsize = 0

        if self.max_combo.get_active():
            maxsize = self.max_size.get_value_as_int()
        else:
            maxsize = 0

        scount = self.stop_packets.get_value_as_int()

        stime = self.stop_time.get_value_as_int()
        factor = self.stop_time_combo.get_active()

        if factor == 0:
            factor = 1
        elif factor == 1:
            factor = 60
        elif factor == 2:
            factor = 60 ** 2

        stime = stime * factor

        ssize = self.stop_size.get_value_as_int()
        factor = self.stop_size_combo.get_active()

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
        audits = self.audits.get_active()

        dct = {
            'filter'       : filter,
            'minsize'      : minsize,
            'maxsize'      : maxsize,
            'capmethod'    : method,
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
            'background'   : background,
            'audits'      : audits,
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

        for widget in self.action_area:
            if self.get_response_for_widget(widget) == gtk.RESPONSE_ACCEPT:
                widget.set_sensitive(False)

                self.if_list.tree.get_selection().connect(
                    'changed',
                    self.__on_selection_changed,
                    widget
                )

                self.options.method.connect(
                    'changed',
                    self.__on_method_changed,
                    widget
                )

                break

        self.if_list.tree.connect('row-activated',
            lambda tree, path, view, diag:
                diag.response(gtk.RESPONSE_ACCEPT), self)

        method = Prefs()['backend.system.sniff.capmethod'].value

        if method < 0 and method > 3:
            Prefs()['backend.system.sniff.capmethod'] = 0
            method = 0

        self.options.method.set_active(method)

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
        # Let's repopulate the store if the capmethod changes.
        # This is usefull for WINDOWS in case of using windump/dumpcap
        # that have a different nomenclature for the interface respect
        # libdnet python binding.

        # This is useless for Linux and other OS

        self.if_list.store.clear()
        active_m = self.options.method.get_active()

        for iface in backend.find_all_devs(active_m):
            self.if_list.store.append(
                [gtk.STOCK_CONNECT, iface.name, iface.description, iface.ip]
            )

    def __on_method_changed(self, combo, btn):
        self.__populate()

        if combo.get_active() == 1:
            btn.set_sensitive(True)
        else:
            self.__on_selection_changed(self.if_list.tree.get_selection(), btn)

    def __on_response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_ACCEPT:
            opts = self.get_options()

            if opts['capmethod'] == 1 and not opts['capfile']:
                log.debug('Capture method selected is virtual interface but '
                          'the file entry is empty. Stopping response emission')

                self.stop_emission('response')

                d = HIGAlertDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT | \
                                         gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
                                   message_format=_("Some options are missing"),
                                   secondary_text=_("You've selected Virtual "
                                                    "interface as capture "
                                                    "method. You need to "
                                                    "specify a file source to "
                                                    "read from"))
                d.run()
                d.hide()
                d.destroy()
