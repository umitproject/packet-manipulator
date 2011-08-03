#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Adriano Monteiro Marques
#
# Author: Guilherme Rezende <guilhermebr@gmail.com>
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
SIP GUI UTILS
"""
import gtk
import gobject
import random

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.atoms import generate_traceback
from umit.pm.core.auditutils import is_ip, random_ip, AuditOperation
from umit.pm.core.const import STATUS_ERR, STATUS_WARNING, STATUS_INFO

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.plugins.core import Core
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.gui.core.views import UmitView


from umit.pm.manager.auditmanager import *

from umit.pm.backend import MetaPacket

class SipGuiUtils(Plugin):
    def start(self, reader):
        self.__inputs__ = (
        ('type of message', (['REGISTER','OPTIONS', 'INVITE', 'PHRACK', 'INFO'], _('Which headers that the message will include'))),
        ('user agent', (['Cisco', 'Linksys', 'Grandstream', 'Yate', 'Xlite', 'Asterisk'], _('A list of user-agents to scan spoofed'))),
        ('contact', ('', _('A list of user-agents to scan spoofed'))),
        ('to', ('', _('A list of user-agents to scan spoofed'))),
        ('via', ('', _('A list of user-agents to scan spoofed'))),
        ('from', ('', _('A list of user-agents to scan spoofed'))),
        ('callid', ('', _('A list of user-agents to scan spoofed'))),
        ('cseq', ('', _('A list of user-agents to scan spoofed'))),
        ('max-forwards', ('', _('A list of user-agents to scan spoofed'))),
        ('content-length', (0, _('A list of user-agents to scan spoofed'))),
    )

    def stop(self):
        pass

    def create_sip_window(self, btn, *data):

        inputs = data[0]
        self.response_back = data[1]

        dialog = gtk.Dialog(_('SIP PACKET CREATE'),
                            None,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        tbl = gtk.Table(2, 1, False)

        tbl.set_border_width(4)
        tbl.set_col_spacings(4)
        tbl.set_row_spacings(4)

        dialog.vbox.pack_start(tbl)

        idx = 0

        for field in inputs:
            for txt, (opt_val, desc) in self.__inputs__:
                if field == txt:
                    break

            if field != txt:
                pass

            lbl = gtk.Label('')
            lbl.set_alignment(.0, .5)
            lbl.set_markup('<b>%s:</b>' % txt.capitalize())

            if isinstance(opt_val, bool):
                widget = gtk.ToggleButton('')
                widget.set_active(opt_val)

                widget.get_child().set_text(widget.get_active() \
                                            and _('Enabled') \
                                            or _('Disabled'))

                widget.connect('toggled', lambda w: w.get_child().set_text( \
                    w.get_active() and _('Enabled') or _('Disabled')))

            elif isinstance(opt_val, str):
                widget = gtk.Entry()
                widget.set_text(opt_val)

            elif isinstance(opt_val, int):
                widget = gtk.SpinButton(gtk.Adjustment(opt_val, -sys.maxint,
                                                       sys.maxint, 1, 10),
                                        digits=0)

            elif isinstance(opt_val, float):
                widget = gtk.SpinButton(gtk.Adjustment(opt_val),
                                        digits=4)

            elif isinstance(opt_val, (list, tuple)):
                widget = gtk.ComboBox()
                store = gtk.ListStore(str)
                for i in opt_val:
                    store.append([i])
                widget.set_model(store)
                cell = gtk.CellRendererText()
                widget.pack_start(cell, True)
                widget.add_attribute(cell, 'text', 0)
                widget.set_active(0)

            lbl.props.has_tooltip = True
            widget.props.has_tooltip = True

            lbl.set_tooltip_markup(desc)
            widget.set_tooltip_markup(desc)
            widget.set_name(txt)

            tbl.attach(lbl, 0, 1, idx, idx + 1, gtk.FILL, gtk.FILL)
            tbl.attach(widget, 1, 2, idx, idx + 1, yoptions=gtk.FILL)
            idx += 1

        tbl.show_all()
        dialog.connect('response', self.on_dialog_response)
        dialog.show()

    def on_dialog_response(self, dialog, rid):
        import gtk
        import umit.pm.gui.core.app

        if rid != gtk.RESPONSE_ACCEPT:
            dialog.hide()
            dialog.destroy()
            return

        table = dialog.vbox.get_children()[0]

        assert isinstance(table, gtk.Table)

        inp_dict = {}

        for widget in table:
            if isinstance(widget, gtk.Label):
                continue

            if isinstance(widget, gtk.SpinButton):
                if widget.get_digits() == 0:
                    value = widget.get_value_as_int()
                else:
                    value = widget.get_value()

            elif isinstance(widget, gtk.ToggleButton):
                value = widget.get_active()

            elif isinstance(widget, gtk.ComboBox):
                model = widget.get_model()
                active = widget.get_active()
                if active < 0:
                    value = None
                value = model[active][0]

            else:
                value = widget.get_text()

            inp_dict[widget.get_name()] = value
            print value

        self.response_back(inp_dict)

        dialog.hide()
        dialog.destroy()

__plugins__ = [SipGuiUtils]
__plugins_deps__ = [('SipGuiUtils', [], ['SipGuiUtils-0.1'], [])]
