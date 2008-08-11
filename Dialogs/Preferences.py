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

import gtk

from Manager.PreferenceManager import Prefs

def new_combo(lst):
    combo = gtk.combo_box_new_text()

    for iter in lst:
        combo.append_text(iter)

    return combo

def set_active_text(combo, text):
    model = combo.get_model()

    for idx in xrange(len(model)):
        value = model.get_value(model.get_iter((idx, )), 0)

        if value.lower() == text.lower():
            combo.set_active(idx)
            return

TYPES = (
    (gtk.FontButton       , gtk.FontButton.get_font_name),
    (gtk.ToggleButton     , gtk.ToggleButton.get_active),
    (gtk.ComboBox         , gtk.ComboBox.get_active_text),
    (gtk.SpinButton       , gtk.SpinButton.get_value),
    (gtk.Entry            , gtk.Entry.get_text),
    (gtk.ColorButton      , gtk.ColorButton.get_color),
    (gtk.FileChooserButton, gtk.FileChooserButton.get_filename),
)

CONSTRUCTORS = (
    # The most inheritance class goes upper
    (gtk.FontButton       , gtk.FontButton.set_font_name),
    (gtk.ToggleButton     , gtk.ToggleButton.set_active),
    (gtk.ComboBox         , set_active_text),
    (gtk.SpinButton       , gtk.SpinButton.set_value),
    (gtk.Entry            , gtk.Entry.set_text),
    (gtk.ColorButton      , gtk.ColorButton.set_color),
    (gtk.FileChooserButton, gtk.FileChooserButton.set_filename),
)

class Page(gtk.Table):
    widgets = []

    def __init__(self):
        self.create_widgets()

        super(Page, self).__init__(max(len(self.widgets), 1), 2)

        self.set_border_width(4)
        self.set_row_spacings(4)

        self.create_ui()
        self.show_all()
    
    def create_widgets(self):
        pass

    def __create_option_widgets(self, name, lbl, widget):
        label = None

        if lbl:
            label = gtk.Label(lbl)
            label.set_use_markup(True)
            label.set_alignment(0, 0.5)

        for typo, func in CONSTRUCTORS:
            if isinstance(widget, typo):

                value = Prefs()[name].value
                func(widget, value)

                break

        return label, widget

    def create_ui(self):
        gidx = 0

        for options in self.widgets:

            if isinstance(options[1], tuple):
                frame = gtk.Frame()
                table = gtk.Table(len(options[1]), 2)

                label = gtk.Label("<b>%s</b>" % options[0])
                label.set_use_markup(True)

                frame.set_label_widget(label)
                frame.add(table)

                table.set_border_width(4)
                table.set_row_spacings(4)

                idx = 0
                for name, lbl, widget in options[1]:
                    lbl, widget = self.__create_option_widgets(name, lbl, widget)

                    if lbl:
                        table.attach(lbl, 0, 1, idx, idx + 1, yoptions=gtk.SHRINK)
                        table.attach(widget, 1, 2, idx, idx + 1, yoptions=gtk.SHRINK)
                    else:
                        table.attach(widget, 0, 2, idx, idx + 1, yoptions=gtk.SHRINK)

                    idx += 1

                self.attach(frame, 0, 2, gidx, gidx + 1, yoptions=gtk.SHRINK)
            else:
                lbl, widget = self.__create_option_widgets(options[0], options[1], options[2])

                if lbl:
                    self.attach(lbl, 0, 1, gidx, gidx + 1, yoptions=gtk.SHRINK)
                    self.attach(widget, 1, 2, gidx, gidx + 1, yoptions=gtk.SHRINK)
                else:
                    self.attach(widget, 0, 2, gidx, gidx + 1, yoptions=gtk.SHRINK)

            gidx += 1

class GUIPage(Page):
    title = "GUI"
    icon = gtk.STOCK_PREFERENCES

    def create_widgets(self):
        self.widgets = [
        ('gui.docking', None, gtk.CheckButton('Use docking windows')),
        
        ('Sniff perspective',
          (('gui.maintab.sniffview.font', 'Sniff view font:', gtk.FontButton()),
           ('gui.maintab.sniffview.usecolors', None, gtk.CheckButton('Colorize rows')))),

        ('Hex view window',
          (('gui.maintab.hexview.font', 'HexView font:', gtk.FontButton()),
           ('gui.maintab.hexview.bpl', 'Bytes per line:', gtk.SpinButton(gtk.Adjustment(8, 1, 16, 1, 1)))))
        ]

class ViewsPage(Page):
    title = "Views"
    icon = gtk.STOCK_LEAVE_FULLSCREEN

    def create_widgets(self):
        self.widgets = [
        ('Show views at startup',
          (('gui.views.protocol_selector_tab', None, gtk.CheckButton('Protocol selector')),
           ('gui.views.property_tab', None, gtk.CheckButton('Protocol properties')),
           ('gui.views.status_tab', None, gtk.CheckButton('Status view')),
           ('gui.views.vte_tab', None, gtk.CheckButton('Terminal')),
           ('gui.views.hack_tab', None, gtk.CheckButton('Payload Hack tab')),
           ('gui.views.console_tab', None, gtk.CheckButton('Python shell'))))
        ]

class BackendPage(Page):
    title = "Backend"
    icon = gtk.STOCK_CONNECT

    def create_widgets(self):
        self.widgets = [
        ('backend.system', 'Backend system:', new_combo(('UMPA', 'Scapy')))
        ]

class PreferenceDialog(gtk.Dialog):
    def __init__(self, parent):
        super(PreferenceDialog, self).__init__(
            "Preferences - PacketManipulator", parent,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE,
             gtk.STOCK_APPLY, gtk.RESPONSE_APPLY,
             gtk.STOCK_OK, gtk.RESPONSE_OK)
        )

        self.store = gtk.ListStore(str, str)
        self.tree = gtk.TreeView(self.store)

        self.tree.append_column(
            gtk.TreeViewColumn('', gtk.CellRendererPixbuf(), stock_id=0))

        self.tree.append_column(
            gtk.TreeViewColumn('', gtk.CellRendererText(), text=1))

        self.tree.set_headers_visible(False)
        self.tree.set_rules_hint(True)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.tree)

        hbox = gtk.HBox()
        hbox.pack_start(sw, False, False)

        self.notebook = gtk.Notebook()
        self.notebook.set_show_border(False)
        self.notebook.set_show_tabs(False)
        hbox.pack_end(self.notebook)

        self.__populate()

        hbox.show_all()

        self.vbox.pack_start(hbox)
        self.vbox.set_border_width(4)
        self.vbox.set_spacing(6)

        self.set_size_request(600, 400)

        self.tree.get_selection().connect('changed', self.__on_switch_page)
        self.connect('response', self.__on_response)

    def __populate(self):
        for page in (GUIPage(), ViewsPage(), BackendPage()):
            self.store.append([page.icon, page.title])
            self.notebook.append_page(page)

    def __on_switch_page(self, selection):
        model, iter = selection.get_selected()

        if iter:
            self.notebook.set_current_page(model.get_path(iter)[0])

    def close(self):
        self.hide()
        self.destroy()

    def apply_changes(self):
        for idx in xrange(self.notebook.get_n_pages()):
            page = self.notebook.get_nth_page(idx)

            for options in page.widgets:

                if isinstance(options[1], tuple):
                    for option, lbl, widget in options[1]:
                        self.__apply(widget, option)
                else:
                    self.__apply(options[2], options[0])

    def __apply(self, widget, option):
        for typo, func in TYPES:
            if isinstance(widget, typo):

                # We should call the functions
                new_value = func(widget)

                Prefs()[option].value = new_value

                break

    def save_changes(self):
        Prefs().write_options()

    def __on_response(self, dialog, id):
        if id == gtk.RESPONSE_CLOSE:
            self.close()
        elif id == gtk.RESPONSE_APPLY:
            self.apply_changes()
        elif id == gtk.RESPONSE_OK:
            self.apply_changes()
            self.save_changes()
            self.close()

if __name__ == "__main__":
    d = PreferenceDialog(None)
    d.show()
    gtk.main()
