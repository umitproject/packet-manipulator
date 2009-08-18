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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 US

import gtk
import pango

from PM.Core.I18N import _
from PM.Gui.Core.Views import UmitView
from PM.Gui.Widgets.Interfaces import InterfacesCombo
from PM.Core.Providers import HOST_LOCAL_TYPE, HOST_NONLOCAL_TYPE, \
     UNKNOWN_TYPE, ROUTER_TYPE, GATEWAY_TYPE

def new_button(stock, tooltip):
    btn = gtk.Button()
    btn.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU))
    #btn.set_relief(gtk.RELIEF_NONE)
    btn.props.has_tooltip = True
    btn.set_tooltip_markup(tooltip)
    btn.set_border_width(0)
    return btn

class HostListDetails(gtk.TreeView):
    def __init__(self):
        self.store = gtk.TreeStore(str, str)
        self.model_filter = self.store.filter_new()
        self.model_filter.set_visible_func(self.__visible_func)

        gtk.TreeView.__init__(self, self.model_filter)

        rend = gtk.CellRendererText()

        self.append_column(gtk.TreeViewColumn('', rend, text=0))
        self.append_column(gtk.TreeViewColumn('', rend, text=1))

        self.get_column(0).set_cell_data_func(rend, self.__data_func)

        self.set_headers_visible(False)
        self.set_rules_hint(True)
        self.set_enable_search(True)
        self.set_search_column(1)

        self.set_rubber_banding(True)
        self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

    def __data_func(self, col, cell, model, iter):
        cell.set_property('markup', '<b>%s</b>' % model.get_value(iter, 0))

    def __visible_func(self, model, iter):
        if model.get_value(iter, 1):
            return True
        return False

    def copy_selected(self):
        selection = self.get_selection()

        if not selection:
            return

        model, rows = selection.get_selected_rows()

        if not model or not rows:
            return

        out = ''

        for path in rows:
            iter = model.get_iter(path)
            out += ('\t' * (len(path) - 1)) + \
                model.get_value(iter, 0) + '\t' + \
                model.get_value(iter, 1) + '\n'

        return out

    def populate(self, prof):
        self.store.clear()

        if not prof:
            return

        iter = self.store.append(None, [_('IP address:'), prof.l3_addr])
        self.store.append(iter, [_('Hostname:'), prof.hostname or ''])
        self.store.append(iter, [_('Remote OS:'), prof.fingerprint])

        iter = self.store.append(None, [_('MAC address:'), prof.l2_addr])
        self.store.append(iter, [_('MAC Vendor:'), prof.vendor or ''])

        if prof.type == UNKNOWN_TYPE:
            host_type = _('Unknown')
        elif prof.type == HOST_LOCAL_TYPE:
            host_type = _('Local (LAN)')
        elif prof.type == HOST_NONLOCAL_TYPE:
            host_type = _('Remote')
        elif prof.type == GATEWAY_TYPE:
            host_type = _('Gateway')
        elif prof.type == ROUTER_TYPE:
            host_type = _('Router')

        iter = self.store.append(None, [_('Type:'), host_type])
        self.store.append(iter, [_('Distance:'), str(prof.distance) + ' hops'])

        iter = self.store.append(None, [_('Services:'), str(len(prof.ports))])

        for port in prof.ports:
            child = self.store.append(iter, [_('Port:'), str(port.port)])

            if port.proto == 6:
                proto = 'TCP'
            elif port.proto == 17:
                proto = 'UDP'
            else:
                proto = port.proto and str(port.proto) or ''

            self.store.append(child, [_('Protocol:'), proto])
            self.store.append(child, [_('Banner:'), port.banner or ''])

            acc_child = self.store.append(child, [_('Accounts:'), \
                                                  str(len(port.accounts))])

            for account in port.accounts:
                self.store.append(acc_child, [_('Username:'), account.username])
                self.store.append(acc_child, [_('Password:'), account.password])
                self.store.append(acc_child, [_('Information:'), account.info \
                                              or ''])
                self.store.append(acc_child, [_('Failed:'), account.failed])
                self.store.append(acc_child, [_('IP address:'),
                                              account.ip_addr])

        self.expand_all()

class HostListTab(UmitView):
    """
    HostListTab is a tab that lists active hosts.

    We have 3 callbacks that could be set:
     - populate_cb is called when the user change the combobox selection
     - info_cb is fired when the user select an ip and then click on info button
     - scan_cb is fired when the user click on scan button to obtain a new shiny
               host list
    """

    name = 'HostListTab'
    label_text = _('HostList')
    tab_position = gtk.POS_RIGHT
    icon_name = gtk.STOCK_INDEX

    def create_ui(self):
        self._populate_cb = None
        self._info_cb = None
        self._scan_cb = None

        self._main_widget.set_border_width(4)
        self._main_widget.set_spacing(2)

        self.intf_combo = InterfacesCombo()
        self._main_widget.pack_start(self.intf_combo, False, False)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.store = gtk.ListStore(str, str, str)
        self.tree = gtk.TreeView(self.store)

        rend = gtk.CellRendererText()

        self.tree.append_column(gtk.TreeViewColumn(_('IP'), rend, text=0))
        self.tree.append_column(gtk.TreeViewColumn(_('MAC'), rend, text=1))
        self.tree.append_column(gtk.TreeViewColumn(_('Description'), rend,
                                                   text=2))

        self.tree.get_column(2).set_resizable(True)

        self.tree.set_rules_hint(True)
        self.tree.set_search_column(0)
        self.tree.set_enable_search(True)

        sw.add(self.tree)
        self._main_widget.pack_start(sw)

        bb = gtk.HButtonBox()
        bb.set_layout(gtk.BUTTONBOX_END)

        self.btn_refresh = new_button(gtk.STOCK_REFRESH, _('Refresh the list'))
        self.btn_refresh.connect('clicked', self.__on_refresh)

        self.btn_scan = new_button(gtk.STOCK_CONNECT, _('Scan for new hosts'))
        self.btn_scan.connect('clicked', self.__on_scan)

        self.btn_info = new_button(gtk.STOCK_INFO,
                                   _('Information for selected host'))
        self.btn_info.connect('clicked', self.__on_info)

        bb.pack_start(self.btn_scan, False, False)
        bb.pack_start(self.btn_refresh, False, False)
        bb.pack_end(self.btn_info, False, False)

        self._main_widget.pack_end(bb, False, False)
        self._main_widget.show_all()

        self.btn_scan.set_sensitive(False)
        self.btn_info.set_sensitive(False)
        self.btn_refresh.set_sensitive(False)

        self.populate()

    def __on_refresh(self, button):
        self.populate()

    def __on_scan(self, button):
        self._scan_cb()

    def __on_info(self, button):
        model, iter = self.tree.get_selection().get_selected()

        if iter:
            intf = self.intf_combo.get_interface()
            ip, mac = model.get_value(iter, 0), model.get_value(iter, 1)

            ret = self._info_cb(intf, ip, mac)

            if not ret:
                return

            import PM.Gui.Core.App

            d = gtk.Dialog(_('Informations for %s - PacketManipulator') % \
                           ret.l3_addr,
                           PM.Gui.Core.App.PMApp().main_window,
                           gtk.DIALOG_DESTROY_WITH_PARENT,
                           (gtk.STOCK_COPY, gtk.RESPONSE_ACCEPT,
                            gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
            d.set_size_request(460, 300)

            sw = gtk.ScrolledWindow()
            sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

            details = HostListDetails()
            details.populate(ret)

            sw.add(details)
            sw.show_all()

            d.vbox.pack_start(sw)
            d.connect('response', self.__on_dialog_response)

            d.show()

    def __on_dialog_response(self, dialog, rid):
        if rid == gtk.RESPONSE_ACCEPT:
            dialog.stop_emission('response')
            details = dialog.vbox.get_children()[0].get_child()

            assert isinstance(details, HostListDetails)

            text = details.copy_selected()

            if text:
                gtk.clipboard_get().set_text(text)
        else:
            dialog.hide()
            dialog.destroy()

    def populate(self):
        """
        Could be called to refresh the store.
        """
        intf = self.intf_combo.get_interface()

        self.store.clear()

        if not callable(self._populate_cb):
            return

        for ip, mac, desc in self._populate_cb(intf):
            self.store.append([ip, mac, desc])

    def get_populate_cb(self):
        return self._populate_cb

    def get_scan_cb(self):
        return self._scan_cb

    def get_info_cb(self):
        return self._info_cb

    def set_populate_cb(self, call):
        if callable(call):
            self._populate_cb = call
            self.btn_refresh.set_sensitive(True)
            self.populate()
        else:
            self.store.clear()
            self.btn_refresh.set_sensitive(False)

    def set_scan_cb(self, call):
        if callable(call):
            self._scan_cb = call
            self.btn_scan.set_sensitive(True)
        else:
            self.btn_scan.set_sensitive(False)

    def set_info_cb(self, call):
        if callable(call):
            self._info_cb = call
            self.btn_info.set_sensitive(True)
        else:
            self.btn_info.set_sensitive(False)

    populate_cb = property(get_populate_cb, set_populate_cb)
    scan_cb = property(get_scan_cb, set_scan_cb)
    info_cb = property(get_info_cb, set_info_cb)
