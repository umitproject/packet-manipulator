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

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.bus import ServiceBus
from umit.pm.core.auditutils import Netmask
from umit.pm.core.providers import HostEntry
from umit.pm.gui.pages.base import Perspective
from umit.pm.core.auditutils import is_ip, is_mac

class TargetTree(gtk.VBox):
    def __init__(self):
        super(TargetTree, self).__init__(False, 2)

        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        self.store = gtk.ListStore(str)
        self.view = gtk.TreeView(self.store)
        self.view.set_rules_hint(True)
        self.view.enable_model_drag_dest([('text/plain', 0, 0)],
                                         gtk.gdk.ACTION_DEFAULT | \
                                         gtk.gdk.ACTION_COPY)

        self.view.connect("drag_data_received",self.__on_drag_data_recv)
        self.view.connect('button-press-event', self.__on_popup_menu)

        self.view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        pixrenderer = gtk.CellRendererPixbuf()
        txtrenderer = gtk.CellRendererText()
        txtrenderer.set_property('editable', True)
        txtrenderer.connect('edited', self.__on_ip_edited)

        column = gtk.TreeViewColumn('Target')
        column.pack_start(pixrenderer, False)
        column.pack_end(txtrenderer)

        column.set_attributes(txtrenderer, text=0)
        column.set_cell_data_func(pixrenderer, self.__set_ip_icon)

        self.view.append_column(column)

        bbox = gtk.HButtonBox()
        bbox.set_layout(gtk.BUTTONBOX_END)

        btn = gtk.Button(stock=gtk.STOCK_ADD)
        btn.connect('clicked', self.__on_add_target)
        bbox.pack_start(btn)

        btn = gtk.Button(stock=gtk.STOCK_REMOVE)
        btn.connect('clicked', self.__on_remove_selection)
        bbox.pack_start(btn)

        sw.add(self.view)
        self.pack_start(sw)
        self.pack_start(bbox, False, False)

    def __set_ip_icon(self, column, cell, model, iter):
        cell.set_property('stock-id', gtk.STOCK_CONNECT)

    def __on_drag_data_recv(self, treeview, context, x, y, selection,
                            info, etime):
        data = selection.data
        self.append(data)
        context.finish(True, True, etime)

    def __on_ip_edited(self, cell, path, new_text):
        iter = self.store.get_iter(path)

        if iter:
            self.store.set_value(iter, 0, new_text)

    def __on_popup_menu(self, tree, event):
        if event.button != 3:
            return False

        self.ctxmenu.popup(None, None, None, event.button, event.time)
        return True

    def __on_add_target(self, btn):
        self.append("0.0.0.0")

    def __on_remove_selection(self, btn):
        model, rows = self.view.get_selection().get_selected_rows()

        if not rows:
            return

        for row in map(lambda path: gtk.TreeRowReference(model, path), rows):
            self.store.remove(model.get_iter(row.get_path()))

        iter = self.store.get_iter_first()

        if iter:
            self.view.get_selection().select_iter(iter)

    def append(self, ip):
        if isinstance(ip, (tuple, list)):
            for i in ip:
                self.store.append([i.strip()])
        else:
            for i in ip.splitlines():
                self.store.append([i.strip()])

    def get_targets(self):
        for row in self.store:
            yield row[0]

class AuditTargetPage(Perspective):
    icon = gtk.STOCK_INDEX
    title = _('Targets')

    def create_ui(self):
        self.target1_tree = TargetTree()
        self.target2_tree = TargetTree()

        # This is to hold information about the targets (a list of HostEntry)
        self.targets = ([], [])

        hbox = gtk.HBox(True, 2)
        hbox.pack_start(self.target1_tree)
        hbox.pack_end(self.target2_tree)

        self.pack_start(hbox)
        self.show_all()

    def get_targets1(self):
        return self.targets[0]

    def get_targets2(self):
        return self.targets[1]

    def create_targets(self):
        """
        Update targets structure appropriately by looking at target{1,2}_tree.
        @return True if the list is filled right or False
        """
        func = ServiceBus().get_function('pm.hostlist', 'get_target')

        if not func:
            dialog = gtk.MessageDialog(self.get_toplevel(), gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                       "No class implements `get_target method'"
                                       " of pm.hostlist interface. Please load "
                                       "an appropriate plugin.")
            dialog.run()
            dialog.hide()
            dialog.destroy()
        else:
            netmask = Netmask(self.session.context.get_netmask1(),
                              self.session.context.get_ip1())

        def add_host_entry(target, targets_idx):
            entry = None

            if is_mac(target):
                entry = HostEntry(l2_addr=target)

            elif func:
                if is_ip(target) and netmask.match_strict(target):
                    profs = filter(lambda p: p.l2_addr is not None,
                                   func(l3_addr=target, netmask=netmask) or \
                                   [])

                    if profs:
                        entry = HostEntry(l2_addr=profs[0].l2_addr,
                                          l3_addr=target,
                                          hostname=profs[0].hostname)
                else:
                    profs = filter(lambda p: p.l2_addr is not None,
                                   func(hostname=target, netmask=netmask) or \
                                   [])

                    if profs:
                        entry = HostEntry(l2_addr=profs[0].l2_addr,
                                          l3_addr=profs[0].l3_addr,
                                          hostname=target)

            if entry:
                log.info('Group %d -> %s' % (targets_idx + 1, entry))
                self.targets[targets_idx].append(entry)

        # Ok. Now let's create the target list
        if not self.targets[0] and not self.targets[1]:
            log.info('Creating targets list for the MITM attack')

            for target in self.target1_tree.get_targets():
                add_host_entry(target, 0)

            for target in self.target2_tree.get_targets():
                add_host_entry(target, 1)

            errs = []

            if func:
                netmask = None

                if not self.targets[0]:
                    netmask = Netmask(self.session.context.get_netmask1(),
                                      self.session.context.get_ip1())

                    for prof in filter(lambda p: p.l2_addr is not None,
                                       func(netmask=netmask) or []):

                        entry = HostEntry(l2_addr=prof.l2_addr,
                                          l3_addr=prof.l3_addr,
                                          hostname=prof.hostname)

                        self.targets[0].append(entry)
                        log.info('[AUTOADD] Group 1 -> %s' % entry)

                if not self.targets[1]:
                    if not netmask:
                        netmask = Netmask(self.session.context.get_netmask1(),
                                          self.session.context.get_ip1())

                    for prof in filter(lambda p: p.l2_addr is not None,
                                       func(netmask=netmask) or []):

                        entry = HostEntry(l2_addr=prof.l2_addr,
                                          l3_addr=prof.l3_addr,
                                          hostname=prof.hostname)

                        self.targets[1].append(entry)
                        log.info('[AUTOADD] Group 2 -> %s' % entry)

            if not self.targets[0]:
                errs.append(
                    _('Could not set any targets for the first group.'))

            if not self.targets[1]:
                errs.append(
                    _('Could not set any targets for the second group.'))

            if errs and not func:
                errs.append(
                    _('Neither get_target can be used to autopopulate the targ'
                      'ets. Please load at least an appropriate plugin (like '
                      'Profiler) and make an ARP scan, or add targets MAC by '
                      'hand.'))

            if errs:
                dialog = gtk.MessageDialog(self.get_toplevel(),
                                           gtk.DIALOG_MODAL,
                                           gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                           "Some errors found:\n\n" + \
                                           '\n'.join(errs))
                dialog.run()
                dialog.hide()
                dialog.destroy()

                return False

            return True
