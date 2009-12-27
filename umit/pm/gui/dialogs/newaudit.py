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
from umit.pm.gui.widgets.interfaces import InterfacesCombo

class NewAuditDialog(gtk.Dialog):
    def __init__(self, parent):
        super(NewAuditDialog, self).__init__(
            _('New audit - PacketManipulator'), parent,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_REJECT,
             gtk.STOCK_NEW, gtk.RESPONSE_ACCEPT)
        )

        lbl1 = gtk.Label(_('Interface:'))
        lbl1.set_alignment(.0, .5)

        lbl2 = gtk.Label(_('Interface:'))
        lbl2.set_alignment(.0, .5)

        lbl3 = gtk.Label(_('Pcap filter:'))
        lbl3.set_alignment(.0, .5)

        self.intf1_combo = InterfacesCombo(False)

        bridge_check = gtk.CheckButton(_('Use bridged sniffing'))
        bridge_check.connect('toggled', self.__on_check_toggled)

        self.unoffensive_check = gtk.CheckButton(_('Unoffensie mode'))
        self.skipforwarded_check = gtk.CheckButton(_('Skip forwarded packets'))

        self.intf2_combo = InterfacesCombo(False)

        self.filter = gtk.Entry()

        table = gtk.Table(5, 2, False)

        table.set_border_width(4)
        table.set_row_spacings(4)
        table.set_col_spacings(10)

        table.attach(lbl1, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        table.attach(self.intf1_combo, 1, 2, 0, 1, yoptions=gtk.FILL)

        table.attach(bridge_check, 0, 2, 1, 2, gtk.FILL, gtk.FILL)
        table.attach(lbl2, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
        table.attach(self.intf2_combo, 1, 2, 2, 3, yoptions=gtk.FILL)

        table.attach(lbl3, 0, 1, 3, 4, gtk.FILL, gtk.FILL)
        table.attach(self.filter, 1, 2, 3, 4, yoptions=gtk.FILL)

        table.attach(self.unoffensive_check, 0, 1, 4, 5, gtk.FILL, gtk.FILL)
        table.attach(self.skipforwarded_check, 0, 1, 5, 6, gtk.FILL, gtk.FILL)

        self.vbox.pack_start(table)

        self.intf2_combo.set_sensitive(False)

        table.show_all()

        for btn in self.action_area:
            if btn.get_label() == gtk.STOCK_NEW:
                self.intf1_combo.connect('changed', self.__on_changed, btn)
                self.intf2_combo.connect('changed', self.__on_changed, btn)

                self.__on_changed(self.intf1_combo, btn)

        self.set_size_request(400, 250)

    def __on_changed(self, widget, btn):
        # This is to avoid launching an audit without having a proper selection
        if self.intf1_combo.get_active() >= 0 and \
           (not self.intf2_combo.flags() & gtk.SENSITIVE or \
            self.intf2_combo.get_active() >= 0):
            btn.set_sensitive(True)
        else:
            btn.set_sensitive(False)

    def __on_check_toggled(self, widget):
        self.intf2_combo.set_sensitive(widget.get_active())

        if widget.get_active():
            self.unoffensive_check.set_active(False)
            self.unoffensive_check.set_sensitive(False)
        else:
            self.unoffensive_check.set_sensitive(True)

    def get_inputs(self):
        return (self.intf1_combo.get_interface(), \
                self.intf2_combo.get_active() and \
                    self.intf2_combo.get_interface() or None,
                self.filter.get_text(),
                self.skipforwarded_check.get_active(),
                self.unoffensive_check.get_active())
