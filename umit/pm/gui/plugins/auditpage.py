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
import pango

import sys
import datetime

from umit.pm.core.i18n import _
from umit.pm.gui.core.app import PMApp
from umit.pm.gui.plugins.core import Core

from umit.pm.manager.auditmanager import AuditManager
from umit.pm.higwidgets.higdialogs import HIGAlertDialog

COLUMN_PIXBUF, \
COLUMN_STRING, \
COLUMN_OBJECT = range(3)

FILTER_NAME         = -1
FILTER_PROTO_NAME   = 0
FILTER_PORT_EQUAL   = 2
FILTER_PORT_NOT     = 3
FILTER_PORT_LESSER  = 4
FILTER_PORT_GREATER = 5
FILTER_VULN_NAME    = 7
FILTER_VULN_DESC    = 8
FILTER_VULN_CLASS   = 9
FILTER_SYS_AFF      = 11
FILTER_SYS_NOTAFF   = 12
FILTER_VER_AFF      = 14
FILTER_VER_NOTAFF   = 15
FILTER_PUBB_ON      = 17
FILTER_PUBB_AFTER   = 18
FILTER_PUBB_BEFORE  = 19
FILTER_DISCOVERED   = 21
FILTER_PLATFORM     = 22
FILTER_ARCHITECTURE = 23

EXTRA_FILTERS = (FILTER_VULN_CLASS, FILTER_PROTO_NAME,
                 FILTER_PORT_EQUAL, FILTER_PORT_NOT,
                 FILTER_PORT_LESSER, FILTER_PORT_GREATER,
                 FILTER_SYS_AFF, FILTER_SYS_NOTAFF,
                 FILTER_VER_AFF, FILTER_VER_NOTAFF,
                 FILTER_DISCOVERED, FILTER_PLATFORM,
                 FILTER_ARCHITECTURE)

class CalendarButton(gtk.Button):
    def __init__(self):
        now = datetime.datetime.now()

        self.year, self.month, self.day = now.year, now.month, now.day

        gtk.Button.__init__(self,
                            '%4d-%2d-%2d' % (self.year, self.month, self.day))

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

            self.set_label('%4d-%2d-%2d' % (self.year, self.month, self.day))

        d.hide()
        d.destroy()

    def get_date(self):
        return self.year, self.month, self.day

class FiltersPage(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self, False, 2)

        self.set_border_width(4)

        self.filters = [
            _('Protocol name contains'),
            None,
            _('Protocol port equal to'),
            _('Protocol port is not'),
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
        self.killer = {}
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

        bb = gtk.HButtonBox()
        bb.set_layout(gtk.BUTTONBOX_END)

        btn = gtk.Button(stock=gtk.STOCK_FIND)
        btn.set_relief(gtk.RELIEF_NONE)
        btn.connect('clicked', self.__on_find)
        bb.pack_start(btn)

        self.pack_end(bb, False, False)

        self.select_first_available()
        self.show_all()

    def __on_find(self, btn):
        if callable(self.find_cb):
            self.rehash()
            self.find_cb()

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

        if sel_id in (FILTER_PORT_EQUAL, FILTER_PORT_NOT, \
                      FILTER_PORT_GREATER, FILTER_PORT_LESSER):

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

        self.vbox.remove(hbox)

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

    def rehash(self):
        self.killer = {}

        txt = self.entry.get_text()

        if txt:
            self.killer[FILTER_NAME] = txt.lower()

        for id in self.active_filters:
            for hbox, lbl, widget, btn in self.active_filters[id]:
                if id not in self.killer:
                    self.killer[id] = []

                if isinstance(widget, gtk.SpinButton):
                    txt = widget.get_value_as_int()
                elif isinstance(widget, gtk.Entry):
                    txt = widget.get_text().lower()
                elif isinstance(widget, CalendarButton):
                    txt = widget.get_date()

                if txt is not None:
                    self.killer[id].append(txt)

    def filter_func(self, model, iter):
        plugin = model.get_value(iter, COLUMN_OBJECT)

        if not plugin:
            return True

        if not self.killer:
            return True

        for id in self.killer:
            if id == FILTER_NAME and self.killer[id] in plugin.name.lower():
                return True
            elif id in (FILTER_PROTO_NAME, FILTER_PORT_EQUAL, FILTER_PORT_NOT, \
                        FILTER_PORT_GREATER, FILTER_PORT_LESSER):

                for key in self.killer[id]:
                    for name, port in plugin.protocols:
                        if id == FILTER_PROTO_NAME and key == name.lower():
                            return True
                        elif id == FILTER_PORT_EQUAL and port and key == port:
                            return True
                        elif id == FILTER_PORT_NOT and port and key != port:
                            return True
                        elif id == FILTER_PORT_GREATER and port and key > port:
                            return True
                        elif id == FILTER_PORT_LESSER and port and key < port:
                            return True

            else:
                for vuln_name, vuln_dict in plugin.vulnerabilities:
                    if id == FILTER_VULN_NAME and \
                       self.killer[id][0] in vuln_name.lower():
                        return True

                    elif id == FILTER_VULN_DESC and \
                         'description' in vuln_dict and \
                         self.killer[id][0] in vuln_dict['description'].lower():
                        return True

                    elif id == FILTER_VULN_CLASS and 'classes' in vuln_dict:
                        for mclass in self.killer[id]:
                            for vclass in vuln_dict['classes']:
                                if mclass in vclass.lower():
                                    return True

                    elif id in (FILTER_SYS_AFF, FILTER_SYS_NOTAFF) and \
                         'systems' in vuln_dict:

                        for sys in self.killer[id]:
                            if id == FILTER_SYS_AFF:
                                for vsys in vuln_dict['systems'][0]:
                                    if sys in vsys.lower():
                                        return True
                            elif id == FILTER_SYS_NOTAFF:
                                for vsys in vuln_dict['systems'][1]:
                                    if sys in vsys.lower():
                                        return True

                    elif id in (FILTER_VER_AFF, FILTER_VER_NOTAFF) and \
                         'versions' in vuln_dict:

                        for sys in self.killer[id]:
                            if id == FILTER_VER_AFF:
                                for vsys in vuln_dict['versions'][0]:
                                    if sys in vsys.lower():
                                        return True
                            elif id == FILTER_VER_NOTAFF:
                                for vsys in vuln_dict['versions'][1]:
                                    if sys in vsys.lower():
                                        return True

                    elif id in (FILTER_PUBB_ON, FILTER_PUBB_AFTER, \
                                FILTER_PUBB_BEFORE, FILTER_DISCOVERED) and \
                         'credits' in vuln_dict:

                        time = datetime.datetime(*self.killer[id][0])

                        for date, authors in vuln_dict['credits']:
                            if id == FILTER_PUBB_ON and time == date:
                                return True
                            elif id == FILTER_PUBB_AFTER and time > date:
                                return True
                            elif id == FILTER_PUBB_BEFORE and time < date:
                                return True

                    elif id in (FILTER_PLATFORM, FILTER_ARCHITECTURE) and \
                         'platforms' in vuln_dict:

                        for skey in self.killer[id]:
                            for plat, arch in vuln_dict['platforms']:
                                if id == FILTER_PLATFORM and \
                                   skey in plat.lower():
                                    return True
                                elif id == FILTER_ARCHITECTURE and \
                                     skey in arch.lowe():
                                    return True

        return False

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

        AuditManager().get_configuration(conf_name)[opt_id] = \
                     widget.get_active()

    def __on_str_changed(self, widget, udata):
        conf_name, opt_id = udata

        AuditManager().get_configuration(conf_name)[opt_id] = \
                     widget.get_text()

    def __on_int_changed(self, widget, udata):
        conf_name, opt_id = udata

        AuditManager().get_configuration(conf_name)[opt_id] = \
                     widget.get_value_as_int()

    def __on_float_changed(self, widget, udata):
        conf_name, opt_id = udata

        AuditManager().get_configuration(conf_name)[opt_id] = \
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
            if conf_name == 'global.cfields':
                continue

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
                opt_lbl.set_ellipsize(pango.ELLIPSIZE_END)
                opt_lbl.set_width_chars(20)
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

class InfoPage(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self, False, 2)
        self.set_border_width(4)

        self.not_selected_lbl = gtk.Label('')
        self.not_selected_lbl.set_markup(_('<span size=\'large\'><b>'
                                           'No plugin selected.</b></span>'))

        self.tagtable = gtk.TextTagTable()

        self.bold = gtk.TextTag('bold')
        self.bold.set_property('right-margin', 15)
        self.bold.set_property('weight', pango.WEIGHT_BOLD)
        self.tagtable.add(self.bold)

        self.par = gtk.TextTag('par')
        self.par.set_property('left-margin', 15)
        self.par.set_property('right-margin', 15)
        self.par.set_property('justification', gtk.JUSTIFY_FILL)
        self.tagtable.add(self.par)

        self.link = gtk.TextTag('link')
        self.link.set_property('foreground', '#0000FF')
        self.link.set_property('right-margin', 15)
        self.link.set_property('underline', pango.UNDERLINE_SINGLE)
        self.link.connect('event', self.__on_link)
        self.tagtable.add(self.link)

        self.buff = gtk.TextBuffer(self.tagtable)
        self.text = gtk.TextView(self.buff)
        self.text.modify_font(pango.FontDescription('Monospace 9'))
        self.text.set_editable(False)
        self.text.set_wrap_mode(gtk.WRAP_WORD_CHAR)

        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.sw.add(self.text)

        self.pack_start(self.not_selected_lbl)
        self.pack_end(self.sw)

        self.current_plugin = None

        self.show()
        self.not_selected_lbl.show()

        self.connect('realize', self.__on_realize)

    def __on_realize(self, widget):
        self.sw.hide()

    def __on_link(self, tag, widget, event, start):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:

            end = start.copy()
            start.backward_to_tag_toggle(self.link)
            end.forward_to_tag_toggle(self.link)

            link = self.buff.get_text(start, end)

            Core().open_url(link)

    def reload(self, plugin):
        if self.current_plugin is plugin:
            return

        if self.current_plugin:
            self.buff.set_text('')

        self.current_plugin = plugin

        if not self.current_plugin or \
           (not plugin.protocols and not plugin.vulnerabilities):

            if not self.not_selected_lbl.flags() & gtk.VISIBLE:
                self.not_selected_lbl.show()

            return

        if self.not_selected_lbl.flags() & gtk.VISIBLE:
            self.not_selected_lbl.hide()
            self.sw.show()

        self.append(_('Protocols:\n'), self.bold)

        for pname, pport in plugin.protocols:
            self.append('- %s\n' % ('%s/%s' %
                                  (pport and str(pport) or '*', pname)),
                        self.par)

        for vulnname, vulndict in plugin.vulnerabilities:
            self.append('\n' + vulnname + ':\n\n', self.bold)

            if 'description' in vulndict:
                self.append(vulndict['description'] + '\n', self.par)


            if 'classes' in vulndict:
                self.append(_('\nClasses:\n'), self.bold)

                for kls in vulndict['classes']:
                    self.append('- %s\n' % kls, self.par)

            if 'systems' in vulndict:
                aff, notaff = vulndict['systems']

                if aff:
                    self.append(_('\nAffected systems:\n'), self.bold)

                    for sys in aff:
                        self.append('- ' + sys + '\n', self.par)

                if notaff:
                    self.append(_('\nNot-affected systems:\n'), self.bold)

                    for sys in aff:
                        self.append('- ' + sys + '\n', self.par)

            if 'versions' in vulndict:
                aff, notaff = vulndict['versions']

                if aff:
                    self.append(_('\nAffected versions:\n'), self.bold)

                    for sys in aff:
                        self.append('- ' + sys + '\n', self.par)

                if notaff:
                    self.append(_('\nNot-affected versions:\n'), self.bold)

                    for sys in aff:
                        self.append('- ' + sys + '\n', self.par)

            if 'platforms' in vulndict:
                platforms = vulndict['platforms']

                if platforms:
                    self.append(_('\nPlatforms:\n'), self.bold)

                    for name, arch in platforms:
                        self.append('- ' + name + ' (' + arch + ')\n', self.par)

            if 'credits' in vulndict:
                date, authors = vulndict['credits']

                self.append(_('Pubblished on: '), self.bold)
                self.append(date + '\n')

                if authors:
                    self.append('\nAuthors:\n', self.bold)

                    for auth in authors:
                        self.append('- ' + auth + '\n', self.par)

            if 'references' in vulndict:
                refs = vulndict['references']

                if refs:
                    self.append(_('\nReferences:\n'), self.bold)

                    for typ, href in refs:
                        self.append('- ', self.par)
                        self.append(href, self.link)

                        if typ:
                            self.append(' (' + typ + ')\n')
                        else:
                            self.append('\n')

    def append(self, txt, *args):
        self.buff.insert_with_tags(self.buff.get_end_iter(), txt, *args)

class AuditPage(gtk.VBox):
    def __init__(self, parent):
        gtk.VBox.__init__(self, False, 4)

        self.p_window = parent

        self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, object)
        self.tree = gtk.TreeView(self.store)

        rend = gtk.CellRendererToggle()
        rend.connect('toggled', self.__on_activate_plugin)

        col = gtk.TreeViewColumn('', rend)
        col.set_expand(False)
        col.set_cell_data_func(rend, self.__act_cell_data_func)

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

        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.sw.add(self.tree)
        self.sw.set_size_request(230, -1)

        self.notebook = gtk.Notebook()
        self.info_page = InfoPage()
        self.options_page = OptionsPage()
        self.filters_page = FiltersPage()
        self.filters_page.find_cb = self.__on_find

        self.filter_model = self.store.filter_new()
        self.filter_model.set_visible_func(self.filters_page.filter_func)

        self.notebook.append_page(self.info_page, None)
        self.notebook.append_page(self.filters_page, None)
        self.notebook.append_page(self.options_page, None)

        self.notebook.set_show_border(False)
        self.notebook.set_show_tabs(False)

        store = gtk.ListStore(str, str)
        self.combo = gtk.ComboBox(store)

        pix_rend = gtk.CellRendererPixbuf()
        self.combo.pack_start(pix_rend, False)

        txt_rend = gtk.CellRendererText()
        self.combo.pack_end(txt_rend)

        self.combo.add_attribute(pix_rend, 'stock-id', 0)
        self.combo.add_attribute(txt_rend, 'text', 1)

        store.append([gtk.STOCK_INDEX, _('Show plugins')])
        store.append([gtk.STOCK_ABOUT, _('Information')])
        store.append([gtk.STOCK_FIND, _('Find plugins')])
        store.append([gtk.STOCK_PREFERENCES, _('Configure plugins')])

        self.combo.set_active(0)
        self.combo.connect('changed', self.__on_change_view)

        self.hbox = gtk.HBox(False, 4)

        self.hbox.pack_start(self.sw, False, False)
        self.hbox.pack_end(self.notebook)

        self.pack_start(self.hbox)

        hbox = gtk.HBox(False, 4)
        hbox.pack_end(self.combo, False, False)
        self.pack_end(hbox, False, False)

        self.populate()
        self.tree.expand_all()

        self.connect('realize', self.__on_realize)
        self.tree.get_selection().connect('changed',
                                          self.__on_selection_changed)

        self.show_all()

    def __on_realize(self, widget):
        self.__on_change_view(self.combo)

    def __on_change_view(self, combo):
        id = self.combo.get_active()

        if id != 1:
            self.tree.set_model(self.store)
            self.tree.expand_all()

        if id == 0: # Show plugins
            self.hbox.set_child_packing(self.sw, True, True, 0, gtk.PACK_START)
            self.notebook.hide()

        elif id == 1: # Information
            self.hbox.set_child_packing(self.sw, False, False, 0,
                                        gtk.PACK_START)

            self.tree.set_model(self.filter_model)
            self.tree.expand_all()

            self.notebook.set_current_page(0)
            self.notebook.show()

        elif id == 2: # Find
            self.hbox.set_child_packing(self.sw, False, False, 0,
                                        gtk.PACK_START)

            self.tree.set_model(self.filter_model)
            self.tree.expand_all()

            self.notebook.set_current_page(1)
            self.notebook.show()

        elif id == 3: # Configure
            self.hbox.set_child_packing(self.sw, False, False, 0,
                                        gtk.PACK_START)

            self.tree.set_model(self.store)
            self.tree.expand_all()

            self.notebook.set_current_page(2)
            self.notebook.show()

        self.__on_selection_changed(self.tree.get_selection())

    def __on_find(self):
        self.filter_model.refilter()
        self.tree.expand_all()

    def __on_activate_plugin(self, cell, path):
        model = self.tree.get_model()
        iter = model.get_iter(path)

        plugin = model.get_value(iter, COLUMN_OBJECT)

        if not plugin:
            return

        if not plugin.enabled:
            func = self.p_window.engine.load_plugin
        else:
            func = self.p_window.engine.unload_plugin

        ret, errmsg = func(plugin)

        if not ret:
            dialog = HIGAlertDialog(
                PMApp().main_window,
                gtk.DIALOG_MODAL,
                gtk.MESSAGE_ERROR,
                message_format=errmsg,
                secondary_text=errmsg.summary
            )
            dialog.run()
            dialog.hide()
            dialog.destroy()

    def __on_selection_changed(self, selection):
        act = self.combo.get_active()

        if act == 1:
            page = self.info_page
        elif act == 3:
            page = self.options_page
        else:
            return

        model, iter = selection.get_selected()

        if not iter:
            return

        obj = model.get_value(iter, COLUMN_OBJECT)

        if not obj:
            return False

        page.reload(obj)

    def __act_cell_data_func(self, col, cell, model, iter):
        plugin = model.get_value(iter, COLUMN_OBJECT)

        if plugin:
            cell.set_property('active', plugin.enabled)
        else:
            cell.set_property('active', False)

    def __txt_cell_data_func(self, col, cell, model, iter):
        plugin = model.get_value(iter, COLUMN_OBJECT)

        if plugin is None:
            cell.set_property('markup', '<b>%s</b>' % \
                              model.get_value(iter, COLUMN_STRING))
        else:
            cell.set_property('markup', '<b>%s</b>\n%s' % (plugin.name,
                                                           plugin.description))

    def populate(self):
        self.store.clear()

        passive_it = self.store.append(None,
            [None, _('Passive audits'), None])

        active_it = self.store.append(None,
            [None, _('Active audits'), None])

        for plugin in self.p_window.engine.available_plugins:
            if plugin.audit_type == 0:
                self.store.append(passive_it,
                    [plugin.get_logo(24, 24), plugin.name, plugin])
            elif plugin.audit_type == 1:
                self.store.append(active_it,
                    [plugin.get_logo(24, 24), plugin.name, plugin])
