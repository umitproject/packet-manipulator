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

import sys

from PM.Core.I18N import _
from PM.Manager.AttackManager import AttackManager

COLUMN_BOOL, \
COLUMN_PIXBUF, \
COLUMN_STRING, \
COLUMN_OBJECT = range(4)

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

        self.notebook = gtk.Notebook()
        self.options_page = OptionsPage()

        self.notebook.append_page(self.options_page, None)
        self.notebook.append_page(self.create_find_page(), None)

        self.notebook.set_show_border(False)
        self.notebook.set_show_tabs(False)

        self.pack_end(self.notebook)

        self.populate()

        # Connect the signals

        self.tree.get_selection().connect('changed',
                                          self.__on_selection_changed)

        self.show_all()

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
