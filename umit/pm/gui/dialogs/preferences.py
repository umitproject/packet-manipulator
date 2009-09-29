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
Dialogs to edit and save preferences of PacketManipulator
"""

import gtk

from umit.pm.core.i18n import _
from umit.pm.manager.preferencemanager import Prefs
from umit.pm.manager.auditmanager import AuditManager

# Dummy class
class EnumeratorBox(gtk.ComboBox):
    pass

def new_combo_enumerator(lst):
    model = gtk.ListStore(str)
    for i in lst:
        model.append([i])
    combo = EnumeratorBox(model)
    rend = gtk.CellRendererText()

    combo.pack_start(rend)
    combo.add_attribute(rend, 'text', 0)

    return combo

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
    (EnumeratorBox        , EnumeratorBox.get_active),
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
    (EnumeratorBox        , EnumeratorBox.set_active),
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

    def save(self):
        pass

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

        lsizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        wsizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

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
                    lbl, widget = self.__create_option_widgets(name, lbl,
                                                               widget)

                    if lbl:
                        lsizegroup.add_widget(lbl)
                        wsizegroup.add_widget(widget)

                        table.attach(lbl, 0, 1, idx, idx + 1,
                                     yoptions=gtk.SHRINK)
                        table.attach(widget, 1, 2, idx, idx + 1,
                                     yoptions=gtk.SHRINK)
                    else:
                        table.attach(widget, 0, 2, idx, idx + 1,
                                     yoptions=gtk.SHRINK)

                    idx += 1

                self.attach(frame, 0, 2, gidx, gidx + 1, yoptions=gtk.SHRINK)
            else:
                lbl, widget = self.__create_option_widgets(options[0],
                                                           options[1],
                                                           options[2])

                if lbl:
                    lsizegroup.add_widget(lbl)
                    wsizegroup.add_widget(widget)

                    self.attach(lbl, 0, 1, gidx, gidx + 1,
                                yoptions=gtk.SHRINK)
                    self.attach(widget, 1, 2, gidx, gidx + 1,
                                yoptions=gtk.SHRINK)
                else:
                    self.attach(widget, 0, 2, gidx, gidx + 1,
                                yoptions=gtk.SHRINK)

            gidx += 1

class GUIPage(Page):
    title = _("GUI")
    icon = gtk.STOCK_PREFERENCES

    def create_widgets(self):
        self.widgets = [

        (_('General'),
          (
           ('gui.docking', _('Docking library:'),
                new_combo(('Standard', 'moo', 'GDL'))),
           ('gui.expander.standard', None,
                gtk.CheckButton(_('Use standard expanders'))),
          )
        ),

        (_('Sessions'),
          (
           ('gui.maintab.askforsave', None,
                gtk.CheckButton(_('Ask on unsaved changes'))),
           ('gui.maintab.autostop', None,
                gtk.CheckButton(_('Automatically stop sessions on close'))),
          )
        ),

        (_('Sniff perspective'),
          (
           ('gui.maintab.sniffview.font', _('Sniff view font:'),
                gtk.FontButton()),
           ('gui.maintab.sniffview.usecolors', None,
                gtk.CheckButton(_('Colorize rows'))),
          )
        ),

        (_('Sequence perspective'),
          (
           ('gui.maintab.sequenceview.font', _('Sequence view font:'),
                gtk.FontButton()),
           ('gui.maintab.sequenceview.usecolors', None,
                gtk.CheckButton(_('Colorize rows'))),
          )
        ),

        (_('Audit output perspective'),
          (
            ('gui.maintab.auditoutputview.font',
                _('Audit output font:'), gtk.FontButton()),
            ('gui.maintab.auditoutputview.timeformat',
                _('Audit output time column str format (strftime):'),
                gtk.Entry()),
            ('gui.maintab.auditoutputview.autoscroll', None,
                gtk.CheckButton(_('Autoscroll for Audit output'))),
          )
        ),

        (_('Hex view window'),
          (
           ('gui.maintab.hexview.font', _('HexView font:'),
                gtk.FontButton()),
           ('gui.maintab.hexview.bpl', _('Bytes per line or group type:'),
                gtk.SpinButton(gtk.Adjustment(8, 1, 16, 1, 1))),
          )
        ),

        (_('Status tab'),
          (
           ('gui.statustab.font', _('Status tab font:'), gtk.FontButton()),
          )
        ),

        (_('Operations tab'),
          (
           ('gui.operationstab.uniqueupdate', None,
                gtk.CheckButton(_('Use a unique function to update '
                                  'progress of operations (CPU saving - '
                                  'Restart required)'))),
           ('gui.operationstab.updatetimeout', _('Update timeout interval'),
                gtk.SpinButton(gtk.Adjustment(500, 100, 1000, 100, 100))),
          )
        )
        ]

class ViewsPage(Page):
    title = "Views"
    icon = gtk.STOCK_LEAVE_FULLSCREEN

    def create_widgets(self):
        self.widgets = [
        (_('Show views at startup'),
          (('gui.views.protocol_selector_tab', None,
                gtk.CheckButton(_('Protocol selector'))),

           ('gui.views.property_tab', None,
                gtk.CheckButton(_('Protocol properties'))),

           ('gui.views.status_tab', None,
                gtk.CheckButton(_('Status view'))),

           ('gui.views.operations_tab', None,
                gtk.CheckButton(_('Operations'))),

           ('gui.views.vte_tab', None,
                gtk.CheckButton(_('Terminal'))),

           ('gui.views.hack_tab', None,
                gtk.CheckButton(_('Payload Hack tab'))),

           ('gui.views.console_tab', None,
                gtk.CheckButton(_('Python shell')))
        ))
        ]

class BackendPage(Page):
    title = _("Backend")
    icon = gtk.STOCK_CONNECT

    def create_widgets(self):
        self.widgets = [
        ('backend.system', _('Backend system:'), new_combo(('UMPA', 'Scapy'))),

        ('Scapy',
          (('backend.scapy.interface', _('Default interface'), gtk.Entry()),)),

        ('Capture methods',
          (
           ('backend.system.sniff.capmethod', _('Capture method for sniffing:'),
            new_combo_enumerator(('Native', 'Virtual','TCPDump', 'Dumpcap'))),

           ('backend.system.sendreceive.capmethod',
            _('Capture method for SendReceive:'),
            new_combo_enumerator(('Native', 'TCPDump', 'Dumpcap'))),

           ('backend.system.sequence.capmethod',
            _('Capture method for Sequence:'),
            new_combo_enumerator(('Native', 'TCPDump', 'Dumpcap'))),

           ('backend.system.audit.capmethod',
            _('Capture method for Audit:'),
            new_combo_enumerator(('Native', 'TCPDump', 'Dumpcap'))),
          )
        ),

        (_('Audits'),
          (
           ('backend.system.sniff.audits', None,
            gtk.CheckButton(_('Enable passive audits on sniff'))),
           ('backend.system.static.audits', None,
            gtk.CheckButton(_('Enable passive audits on loaded files'))),
          )
        ),

        (_('Helpers'),
          (
           ('backend.tcpdump', _('tcpdump path:'), gtk.Entry()),
           ('backend.dumpcap', _('dumpcap path:'), gtk.Entry()),
          )
        ),

        ]

class SystemPage(Page):
    title = _("System")
    icon = gtk.STOCK_PROPERTIES

    def create_widgets(self):
        self.widgets = [
        (_('Checks'),
          (
           ('system.check_root', None,
                gtk.CheckButton(_('Check for root privileges at startup'))),
           ('system.check_pyver', None,
                gtk.CheckButton(_('Check for compatible Python version')))
          )
        ),

        ]

class SniffPage(gtk.VBox):
    title = _('Sniff perspective')
    icon = gtk.STOCK_INDEX

    def __init__(self):
        gtk.VBox.__init__(self, False, 2)

        self.set_border_width(4)

        self.store = gtk.ListStore(str, int, str)
        self.view = gtk.TreeView(self.store)
        self.view.set_rules_hint(True)
        self.view.set_reorderable(True)

        idx = 0
        lbls = (_('Column title'), _('Column size'), _('Function/cfield'))

        for lbl in lbls[:-1]:
            rend = gtk.CellRendererText()
            rend.set_property('editable', True)
            rend.connect('edited', self.__on_rend_edited, idx)

            col = gtk.TreeViewColumn(lbl, rend, text=idx)
            self.view.append_column(col)
            idx += 1

        # Last column
        model = gtk.ListStore(str)
        cfields = AuditManager().get_configuration('global.cfields').keys()
        cfields.sort()

        for field in cfields:
            model.append(['%' + field + '%'])

        rend = gtk.CellRendererCombo()
        rend.set_property('model', model)
        rend.set_property('text-column', 0)
        rend.set_property('editable', True)
        rend.connect('edited', self.__on_rend_edited, idx)

        self.view.props.has_tooltip = True
        self.view.connect('query-tooltip', self.__on_query_tooltip)

        col = gtk.TreeViewColumn(lbls[-1], rend, text=idx)
        self.view.append_column(col)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        sw.add(self.view)

        bb = gtk.HButtonBox()
        bb.set_layout(gtk.BUTTONBOX_END)

        btn = gtk.Button(stock=gtk.STOCK_ADD)
        btn.connect('clicked', self.__on_add_row)
        bb.pack_start(btn)

        btn = gtk.Button(stock=gtk.STOCK_REMOVE)
        btn.connect('clicked', self.__on_remove_row)
        bb.pack_start(btn)

        self.pack_start(sw)
        self.pack_end(bb, False, False)

        # Let's populate
        columns_str = Prefs()['gui.maintab.sniffview.columns'].value

        for column_str in columns_str.split(','):
            try:
                label, pixel_size, eval_str = column_str.split('|', 2)
                pixel_size = int(pixel_size)

                self.store.append([label, pixel_size, eval_str])
            except:
                pass

        self.widgets = []

    def __on_query_tooltip(self, widget, x, y, ktip, tooltip):
        if not widget.get_tooltip_context(x, y, ktip):
            return False

        model, path, iter = widget.get_tooltip_context(x, y, ktip)

        value = model.get_value(iter, 2)[1:-1]

        try:
            desc = AuditManager().get_configuration('global.cfields') \
                 .get_description(value)

            tooltip.set_markup('<b>%s:</b> %s' % (value, desc))
            widget.set_tooltip_row(tooltip, path)

            return True
        except:
            return False

    def __on_rend_edited(self, cell, path, new_text, idx):
        if idx == 1:
            # We have to check that new_text is a int()
            try:
                new_text = int(new_text)
            except ValueError:
                return

        iter = self.store.get_iter(path)
        self.store.set_value(iter, idx, new_text)


    def __on_add_row(self, widget):
        self.store.append(['Time', 150, '%time%'])

    def __on_remove_row(self, widget):
        model, iter = self.view.get_selection().get_selected()

        if iter:
            self.store.remove(iter)

    def save(self):
        s = ''

        for lbl, size, eval_str in self.store:
            s += "%s|%d|%s," % (lbl, size, eval_str)

        Prefs()['gui.maintab.sniffview.columns'].value = s[:-1]

class PreferenceDialog(gtk.Dialog):
    def __init__(self, parent):
        super(PreferenceDialog, self).__init__(
            _("Preferences - PacketManipulator"), parent,
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

        hbox = gtk.HBox(False, 2)
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

        #self.set_size_request(-1, -1)

        self.tree.get_selection().connect('changed', self.__on_switch_page)
        self.connect('response', self.__on_response)

    def __populate(self):
        for page in (GUIPage(), ViewsPage(), SniffPage(), BackendPage(), \
                     SystemPage()):
            self.store.append([page.icon, page.title])

            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
            sw.set_shadow_type(gtk.SHADOW_NONE)
            sw.add_with_viewport(page)

            sw.set_size_request(-1, 400)

            self.notebook.append_page(sw)

    def __on_switch_page(self, selection):
        model, iter = selection.get_selected()

        if iter:
            self.notebook.set_current_page(model.get_path(iter)[0])

    def close(self):
        self.hide()
        self.destroy()

    def apply_changes(self):
        for idx in xrange(self.notebook.get_n_pages()):
            # The page is inside a ViewPort, and ViewPort is inside ScrolledWindow
            page = self.notebook.get_nth_page(idx).get_child().get_child()

            for options in page.widgets:

                if isinstance(options[1], tuple):
                    for option, lbl, widget in options[1]:
                        self.__apply(widget, option)
                else:
                    self.__apply(options[2], options[0])
            else:
                page.save()

    def __apply(self, widget, option):
        for typo, func in TYPES:
            if isinstance(widget, typo):

                # We should call the functions
                new_value = func(widget)

                Prefs()[option].value = new_value

                break

    def save_changes(self):
        try:
            Prefs().write_options()
        except Exception, err:
            # It will be handled on MainWindow before quit
            pass

    def __on_response(self, dialog, id):
        if id == gtk.RESPONSE_CLOSE:
            self.close()
        elif id == gtk.RESPONSE_APPLY:
            self.apply_changes()
        elif id == gtk.RESPONSE_OK:
            self.apply_changes()
            self.save_changes()
            self.close()
