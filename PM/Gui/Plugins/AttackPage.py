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
import pango

import sys
import datetime

from PM.Core.I18N import _
from PM.Manager.AttackManager import AttackManager

COLUMN_BOOL, \
COLUMN_PIXBUF, \
COLUMN_STRING, \
COLUMN_OBJECT = range(4)

FILTER_PROTO_NAME   = 0
FILTER_PORT_EQUAL   = 2
FILTER_PORT_LESSER  = 3
FILTER_PORT_GREATER = 4
FILTER_VULN_NAME    = 6
FILTER_VULN_DESC    = 7
FILTER_VULN_CLASS   = 8
FILTER_SYS_AFF      = 10
FILTER_SYS_NOTAFF   = 11
FILTER_VER_AFF      = 13
FILTER_VER_NOTAFF   = 14
FILTER_PUBB_ON      = 16
FILTER_PUBB_AFTER   = 17
FILTER_PUBB_BEFORE  = 18
FILTER_DISCOVERED   = 20
FILTER_PLATFORM     = 21
FILTER_ARCHITECTURE = 22

EXTRA_FILTERS = (FILTER_VULN_CLASS,
                 FILTER_SYS_AFF, FILTER_SYS_NOTAFF,
                 FILTER_VER_AFF, FILTER_VER_NOTAFF,
                 FILTER_DISCOVERED, FILTER_PLATFORM,
                 FILTER_ARCHITECTURE)

class CalendarButton(gtk.Button):
    def __init__(self):
        now = datetime.datetime.now()

        self.year, self.month, self.day = now.year, now.month, now.day

        gtk.Button.__init__(self,
                            '%d/%d/%d' % (self.year, self.month, self.day))

        self.connect('clicked', self.__on_clicked)

    def __on_clicked(self, btn):
        d = gtk.Dialog(_('Select a date'), self.get_toplevel(),
                       gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL,
                       (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        calendar = gtk.Calendar()
        calendar.show()

        d.vbox.pack_start(calendar)

        if d.run() == gtk.RESPONSE_ACCEPT:
            self.year, self.month, self.day = calendar.get_date()

            self.set_label('%d/%d/%d' % (self.year, self.month, self.day))

        d.hide()
        d.destroy()

    def get_date(self):
        return self.year, self.month, self.date

class FiltersPage(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self, False, 2)

        self.set_border_width(4)

        self.filters = [
            _('Protocol name contains'),
            None,
            _('Protocol port equal to'),
            _('Protocol port lesser than'),
            _('Protocol port greater than'),
            None,
            _('Vulnerability name contains'),
            _('Vulnerability description contains'),
            _('Vulnerability class contains'),
            None,
            _('Systems affected includes'),
            _('Systems not-affected includes'),
            None,
            _('Versions affected includes'),
            _('Versions not-affected includes'),
            None,
            _('Pubblished on'),
            _('Pubblished after'),
            _('Pubblished before'),
            _('Discovered by'),
            None,
            _('Vulnerability classification (CVE/OSVDB/etc)'),
            _('URI\'s references contains'),
            None,
            _('Platform is'),
            _('Architecture is'),
        ]

        self.n_rows = 1
        self.active_filters = {}

        self.group_labels = gtk.SizeGroup(gtk.SIZE_GROUP_BOTH)
        self.group_widgets = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self.group_buttons = gtk.SizeGroup(gtk.SIZE_GROUP_BOTH)

        lbl = gtk.Label(_('Name contains:'))
        lbl.set_alignment(.0, .5)

        self.entry = gtk.Entry()

        self.store = gtk.ListStore(str, bool)
        self.combo = gtk.ComboBox(self.store)

        cell = gtk.CellRendererText()
        cell.set_property('ellipsize', pango.ELLIPSIZE_END)

        self.combo.pack_end(cell)
        self.combo.add_attribute(cell, 'text', 0)
        self.combo.add_attribute(cell, 'sensitive', 1)
        self.combo.set_size_request(150, -1)

        for filter in self.filters:
            self.store.append([filter or '', filter and True or False])

        self.combo.set_row_separator_func(self.__separator_func)

        hbox = gtk.HBox(False, 10)

        hbox.pack_start(lbl, False, False)
        hbox.pack_start(self.entry)

        self.pack_start(hbox, False, False)

        self.vbox = gtk.VBox(False, 2)
        self.vbox.set_border_width(4)

        self.expander = gtk.Expander(_('More options'))
        self.expander.add(self.vbox)

        lbl = gtk.Label(_('Available options:'))
        lbl.set_alignment(.0, .5)

        btn = gtk.Button(stock=gtk.STOCK_ADD)
        btn.connect('clicked', self.__on_add_filter)

        hbox = gtk.HBox(False, 4)

        hbox.pack_start(lbl, False, False, 10)
        hbox.pack_start(self.combo)
        hbox.pack_end(btn, False, False)

        self.group_labels.add_widget(lbl)
        self.group_widgets.add_widget(self.combo)
        self.group_buttons.add_widget(btn)

        self.vbox.pack_start(hbox)

        self.pack_start(self.expander, False, False)

        self.show_all()

    def __separator_func(self, model, iter):
        if not model.get_value(iter, 0):
            return True

    def __on_add_filter(self, btn):
        sel_id = self.combo.get_active()
        ret = self.create_widget(sel_id)

        if not ret:
            return

        lbl, widget, btn = ret

        hbox = gtk.HBox(False, 4)

        hbox.pack_start(lbl, False, False, 10)
        hbox.pack_start(widget)
        hbox.pack_end(btn, False, False)

        self.group_labels.add_widget(lbl)
        self.group_widgets.add_widget(widget)
        self.group_buttons.add_widget(btn)

        if not sel_id in self.active_filters:
            self.active_filters[sel_id] = [(hbox, lbl, widget, btn)]
        else:
            self.active_filters[sel_id].append((hbox, lbl, widget, btn))

        self.vbox.pack_start(hbox, False, False)
        hbox.show()

        self.n_rows += 1
        self.select_first_available()

    def select_first_available(self):
        # Now select the first sensitive iter
        idx = 0
        for i in self.store:
            if i[1]:
                break
            idx += 1

        self.combo.set_active(idx)

    def create_widget(self, sel_id):
        if sel_id not in EXTRA_FILTERS:
            if sel_id in self.active_filters:
                return

            self.store.set_value(self.store.get_iter(sel_id), 1, False)

        lbl = gtk.Label(self.filters[sel_id] + ':')
        lbl.set_alignment(.0, .5)
        lbl.show()

        if sel_id in (FILTER_PORT_EQUAL, FILTER_PORT_GREATER, \
                      FILTER_PORT_LESSER):

            widget = gtk.SpinButton(gtk.Adjustment(1, 1, 65535, 1, 10))

        elif sel_id in (FILTER_PUBB_ON, FILTER_PUBB_AFTER, FILTER_PUBB_BEFORE):
            widget = CalendarButton()

        else:
            widget = gtk.Entry()

        widget.show()

        btn = gtk.Button(stock=gtk.STOCK_REMOVE)
        btn.set_relief(gtk.RELIEF_NONE)
        btn.connect('clicked', self.__on_remove, sel_id)
        btn.show()

        return lbl, widget, btn

    def __on_remove(self, btn, sel_id):
        idx = 0
        self.store.set_value(self.store.get_iter(sel_id), 1, True)

        for hbox, lbl, widget, cbtn in self.active_filters[sel_id]:
            if btn is cbtn:
                break
            idx += 1

        hbox, lbl, widget, cbtn = self.active_filters[sel_id][idx]

        hbox.hide()

        lbl.hide()
        widget.hide()
        cbtn.hide()

        lbl.destroy()
        widget.destroy()
        cbtn.destroy()

        hbox.destroy()

        del self.active_filters[sel_id][idx]

        if not self.active_filters[sel_id]:
            del self.active_filters[sel_id]

        self.n_rows -= 1
        self.select_first_available()

class OptionsPage(gtk.Table):
    def __init__(self):
        gtk.Table.__init__(self, 1, 1)

        self.set_col_spacings(4)
        self.set_row_spacings(2)

        self.not_selected_lbl = gtk.Label('')
        self.not_selected_lbl.set_markup(_('<span size=\'large\'><b>'
                                           'No options defined.</b></span>'))

        self.size_group = gtk.SizeGroup(gtk.SIZE_GROUP_BOTH)

        self.attach(self.not_selected_lbl, 0, 1, 0, 1)

        self.current_plugin = None
        self.widgets = []

        self.show_all()

    def cleanup(self):
        if not self.widgets:
            return

        for conf_lbl, conf_widgets in self.widgets:
            conf_lbl.hide()

            for lbl, widget in conf_widgets:
                lbl.hide()
                widget.hide()

                lbl.destroy()
                widget.destroy()

            conf_lbl.destroy()

        self.widgets = []

    def create_widget(self, conf_name, opt_id, opt_val, opt_desc):
        if isinstance(opt_val, bool):
            widget = gtk.ToggleButton('')
            widget.set_active(opt_val)

            if widget.get_active():
                widget.get_child().set_text(_('Enabled'))
            else:
                widget.get_child().set_text(_('Disabled'))

            widget.connect('toggled', self.__on_bool_toggled, \
                           (conf_name, opt_id))

        elif isinstance(opt_val, str):
            widget = gtk.Entry()
            widget.set_text(opt_val)

            widget.connect('changed', self.__on_str_changed, \
                           (conf_name, opt_id))

        elif isinstance(opt_val, int):
            widget = gtk.SpinButton(gtk.Adjustment(opt_val, -sys.maxint,
                                                   sys.maxint, 1, 10), digits=0)

            widget.connect('value-changed', self.__on_int_changed, \
                           (conf_name, opt_id))

        elif isinstance(opt_val, float):
            widget = gtk.SpinButton(gtk.Adjustment(opt_val, -sys.maxint,
                                                   sys.maxint, 1, 10), digits=4)

            widget.connect('value-changed', self.__on_float_changed, \
                           (conf_name, opt_id))

        if opt_desc:
            widget.props.has_tooltip = True
            widget.set_data('opt_tuple', (opt_id, opt_desc))
            widget.connect('query-tooltip', self.__on_query_tooltip)

        return widget

    def __on_bool_toggled(self, widget, udata):
        conf_name, opt_id = udata

        if widget.get_active():
            widget.get_child().set_text(_('Enabled'))
        else:
            widget.get_child().set_text(_('Disabled'))

        AttackManager().get_configuration(conf_name)[opt_id] = \
                     widget.get_active()

    def __on_str_changed(self, widget, udata):
        conf_name, opt_id = udata

        AttackManager().get_configuration(conf_name)[opt_id] = \
                     widget.get_text()

    def __on_int_changed(self, widget, udata):
        conf_name, opt_id = udata

        AttackManager().get_configuration(conf_name)[opt_id] = \
                     widget.get_value_as_int()

    def __on_float_changed(self, widget, udata):
        conf_name, opt_id = udata

        AttackManager().get_configuration(conf_name)[opt_id] = \
                     widget.get_value()

    def __on_query_tooltip(self, widget, x, y, keyboard_tip, tooltip):
        data = widget.get_data('opt_tuple')

        if not data:
            return False

        tooltip.set_markup('<span size=\'large\'><b>%s</b></span>\n%s' \
                           % (data[0], data[1]))
        tooltip.set_icon_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON)

        return True

    def reload(self, plugin):
        if self.current_plugin is plugin:
            return

        if self.current_plugin:
            self.cleanup()

        self.current_plugin = plugin

        if not self.current_plugin or not plugin.configurations:

            if not self.not_selected_lbl.flags() & gtk.VISIBLE:
                self.not_selected_lbl.show()
                self.attach(self.not_selected_lbl, 0, 1, 0, 1)

            return

        if self.not_selected_lbl.flags() & gtk.VISIBLE:
            self.not_selected_lbl.hide()
            self.remove(self.not_selected_lbl)

        row = 0

        for conf_name, conf_dict in plugin.configurations:
            opt_list = conf_dict.items()
            opt_list.sort()

            conf_lbl = gtk.Label()
            conf_lbl.set_markup('<span size=\'large\'><b>%s</b></span>' % \
                                conf_name)
            conf_lbl.set_alignment(.0, .5)
            conf_lbl.show()

            eb = gtk.EventBox()
            eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#FFFFDC"))
            eb.add(conf_lbl)
            eb.show()

            conf_frame = gtk.Frame()
            conf_frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            conf_frame.set_border_width(2)
            conf_frame.add(eb)
            conf_frame.show()

            self.attach(conf_frame, 0, 2, row, row + 1, xoptions=gtk.FILL,
                        yoptions=gtk.FILL)

            conf_widgets = []

            for opt_id, (opt_val, opt_desc) in opt_list:
                opt_lbl = gtk.Label()
                opt_lbl.set_markup('<tt>%s</tt>' % opt_id)
                opt_lbl.set_alignment(.0, .5)
                opt_wid = self.create_widget(conf_name, opt_id,
                                             opt_val, opt_desc)

                opt_lbl.show()
                opt_wid.show()

                self.size_group.add_widget(opt_wid)

                row += 1
                self.attach(opt_lbl, 0, 1, row, row + 1, xoptions=gtk.FILL,
                            yoptions=gtk.FILL, xpadding=10)
                self.attach(opt_wid, 1, 2, row, row + 1, yoptions=gtk.FILL)

                conf_widgets.append((opt_lbl, opt_wid))

            self.widgets.append((conf_frame, conf_widgets))
            row += 1

class AttackPage(gtk.HBox):
    def __init__(self, parent):
        gtk.HBox.__init__(self, False, 4)

        self.p_window = parent

        self.store = gtk.TreeStore(bool, gtk.gdk.Pixbuf, str, object)
        self.tree = gtk.TreeView(self.store)

        rend = gtk.CellRendererToggle()
        col = gtk.TreeViewColumn('', rend, active=COLUMN_BOOL)
        col.set_expand(False)

        self.tree.append_column(col)

        rend = gtk.CellRendererPixbuf()
        col = gtk.TreeViewColumn('', rend, pixbuf=COLUMN_PIXBUF)
        col.set_expand(False)

        self.tree.append_column(col)

        rend = gtk.CellRendererText()
        col = gtk.TreeViewColumn('', rend, text=COLUMN_STRING)
        col.set_expand(True)
        col.set_cell_data_func(rend, self.__txt_cell_data_func)

        self.tree.append_column(col)

        self.tree.set_headers_visible(False)
        self.tree.set_search_column(COLUMN_STRING)
        self.tree.set_rules_hint(True)
        self.tree.set_enable_search(True)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        sw.add(self.tree)
        sw.set_size_request(200, -1)

        self.pack_start(sw, False, False)

        vbox = gtk.VBox(False, 2)

        self.notebook = gtk.Notebook()
        self.options_page = OptionsPage()
        self.filters_page = FiltersPage()

        self.notebook.append_page(self.options_page, None)
        self.notebook.append_page(self.filters_page, None)

        self.notebook.set_show_border(False)
        self.notebook.set_show_tabs(False)

        bb = gtk.HButtonBox()
        bb.set_layout(gtk.BUTTONBOX_END)

        self.find_btn = gtk.Button(stock=gtk.STOCK_FIND)
        self.find_btn.set_relief(gtk.RELIEF_NONE)
        self.find_btn.connect('clicked', self.__on_find_clicked)

        self.pref_btn = gtk.Button(stock=gtk.STOCK_PREFERENCES)
        self.pref_btn.set_relief(gtk.RELIEF_NONE)
        self.pref_btn.connect('clicked', self.__on_pref_clicked)

        bb.pack_start(self.pref_btn)
        bb.pack_end(self.find_btn)

        vbox.pack_start(self.notebook)
        vbox.pack_end(bb, False, False)

        self.pack_end(vbox)

        self.populate()

        self.tree.get_selection().connect('changed',
                                          self.__on_selection_changed)

        self.connect('realize', self.__on_realize)
        self.show_all()

    def __on_find_clicked(self, widget):
        if self.notebook.get_current_page():
            #self.filters_page.apply_filters()
            pass
        else:
            self.pref_btn.show()
            self.notebook.set_current_page(1)

    def __on_pref_clicked(self, widget):
        self.pref_btn.hide()
        self.notebook.set_current_page(0)

    def __on_realize(self, widget):
        self.pref_btn.hide()

    def __on_selection_changed(self, selection):
        model, iter = selection.get_selected()
        obj = model.get_value(iter, COLUMN_OBJECT)

        if not obj:
            return False

        self.options_page.reload(obj)

    def __txt_cell_data_func(self, col, cell, model, iter):
        plugin = model.get_value(iter, COLUMN_OBJECT)

        if plugin is None:
            cell.set_property('markup', '<b>%s</b>' % \
                              model.get_value(iter, COLUMN_STRING))
        else:
            cell.set_property('markup', '<b>%s</b>\n%s' % (plugin.name,
                                                           plugin.description))

    def populate(self):
        offline_it = self.store.append(None,
            [False, None, _('Offline attacks'), None])

        online_it = self.store.append(None,
            [False, None, _('Online attacks'), None])

        for plugin in self.p_window.engine.available_plugins:
            if plugin.attack_type == 0:
                self.store.append(offline_it,
                    [False, plugin.get_logo(24, 24), plugin.name, plugin])
            elif plugin.attack_type == 1:
                self.store.append(online_it,
                    [False, plugin.get_logo(24, 24), plugin.name, plugin])

    def create_find_page(self):
        return gtk.Label('Implement me')
