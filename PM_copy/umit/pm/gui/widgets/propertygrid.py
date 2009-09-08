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

import gtk
import cairo
import pango
import gobject

from umit.pm import backend
from umit.pm.core.i18n import _
from umit.pm.core.logger import log

from umit.pm.higwidgets.higbuttons import MiniButton
from umit.pm.higwidgets.hignetwidgets import HIGIpEntry, HIGIpv6Entry, HIGMacEntry

from umit.pm.gui.core.icons import get_pixbuf
from umit.pm.gui.widgets.expander import ToolBox
from umit.pm.manager.preferencemanager import Prefs

try:
    from umit.pm.gui.widgets.pygtkhexview import HexView
except ImportError:
    HexView = None

class Editor(gtk.HBox):

    def __init__(self, field):
        assert isinstance(field, tuple)
        gtk.HBox.__init__(self, 0, False)

        if len(field) == 2:
            self.protocol, self.field = field
            self.flag_name = None
        else:
            self.protocol, self.field, self.flag_name = field

        self.create_widgets()
        self.pack_widgets()
        self.connect_signals()

        self.show()

    def create_widgets(self):  pass
    def pack_widgets(self):    pass
    def connect_signals(self): pass

    def get_value(self):
        if self.flag_name != None:
            return backend.get_keyflag_value(self.protocol, self.field,
                                             self.flag_name)
        else:
            return backend.get_field_value(self.protocol, self.field)

    def set_value(self, value):
        if self.flag_name != None:
            backend.set_keyflag_value(self.protocol, self.field, self.flag_name,
                                      value)
        else:
            backend.set_field_value(self.protocol, self.field, value)

    @staticmethod
    def render(field, window, widget, bounds, state):
        return False

    value = property(get_value, set_value)

class IntEditor(Editor):
    # Check the tipe in __init__

    def create_widgets(self):
        # Manage the None type

        value = self.value

        if value is None:
            value = 0

        self.calc_bounds()
        self.adj = gtk.Adjustment(value, self.min, self.max, 1, 2)
        self.spin = gtk.SpinButton(self.adj, digits=self.digits)

    def pack_widgets(self):
        self.pack_start(self.spin)
        #self.spin.set_has_frame(False)
        self.spin.show()

    def connect_signals(self):
        self.spin.connect('value-changed', self.__on_changed)

    def calc_bounds(self):
        # Unsigned int / Int? :(
        if backend.get_field_size(self.protocol, self.field) != None:
            self.min = 0
            # (2 ^ n) - 1
            self.max = (2 ** backend.get_field_size(self.protocol,
                                                    self.field)) - 1
            self.digits = 0
        else:
            import sys
            log.debug("Hei man we are falling back to sys.maxint for %s" % \
                      self.field)
            self.min = -sys.maxint - 1
            self.max = sys.maxint
            self.digits = 0

    def __on_changed(self, spin):
        if self.spin.get_digits() != 0:
            self.value = self.spin.get_value()
        else:
            self.value = self.spin.get_value_as_int()

class BitEditor(Editor):
    def create_widgets(self):
        self.btn = gtk.CheckButton()
        self.btn.set_active(self.value)

    def pack_widgets(self):
        self.pack_start(self.btn)
        self.btn.show()

    def connect_signals(self):
        self.btn.connect('toggled', self.__on_changed)

    def __on_changed(self, btn):
        self.value = self.btn.get_active()

    @staticmethod
    def render(field, window, widget, bounds, state):
        if len(field) == 3:
            proto, field, name = field

            if backend.get_keyflag_value(proto, field, name):
                sh = gtk.SHADOW_IN
            else:
                sh = gtk.SHADOW_OUT
        else:
            raise Exception

        size = 15

        if size > bounds.height:
            size = bounds.height
        if size > bounds.width:
            size = bounds.width

        # Paint a right aligned checkbox
        widget.style.paint_check(window, state, sh, bounds, widget,
                                 "checkbutton", bounds.x,
                                 bounds.y + (bounds.height - size) / 2,
                                 size, size)

        # Yes we handle the drawing
        return True

class EnumEditor(Editor):
    def create_widgets(self):
        self.store = gtk.ListStore(gtk.gdk.Pixbuf, str, int)
        self.combo = gtk.ComboBox(self.store)

        self.icon = None

        pix = gtk.CellRendererPixbuf()
        txt = gtk.CellRendererText()

        txt.set_property('font',
                         Prefs()['gui.views.property_tab.font'].value \
                         or 'Monospace 8')

        self.combo.pack_start(pix, False)
        self.combo.pack_start(txt)

        self.combo.set_attributes(pix, pixbuf=0)
        self.combo.set_attributes(txt, text=1)

        self.odict = backend.get_field_enumeration_i2s(self.field)
        self.odict.sort()

        idx = 0
        set = False

        for value, key in self.odict:
            self.store.append([self.icon, key, value])

            if not set:
                if self.value == value:
                    set = True
                    continue

                idx += 1

        if set:
            self.combo.set_active(idx)

        self.store.append([self.icon, _("Set manually"), -1])

        self.int_editor = IntEditor((self.protocol, self.field))

        self.undo_btn = MiniButton(stock=gtk.STOCK_UNDO)
        self.undo_btn.set_size_request(24, 24)

        self.int_editor.pack_start(self.undo_btn, False, False)
        self.int_editor.show()

    def pack_widgets(self):
        self.pack_start(self.combo)

    def connect_signals(self):
        self.last = len(self.store) - 1
        self.combo.connect('changed', self.__on_changed)
        self.undo_btn.connect('clicked', self.__on_switch_back)

    def __on_changed(self, combo):
        if self.combo.get_active() == self.last:
            self.remove(self.combo)
            self.pack_start(self.int_editor)
            self.int_editor.show_all()
        else:
            iter = self.combo.get_active_iter()

            if iter:
                model = self.combo.get_model()
                self.value = model.get_value(iter, 2)

    def __on_switch_back(self, btn):
        self.remove(self.int_editor)
        self.pack_start(self.combo)
        self.combo.show_all()

class StrEditor(Editor):
    def create_widgets(self):
        self.entry = gtk.Entry()
        self._ignore_changed = False

        try:
            self.entry.set_text(unicode(self.value))
            self.entry.set_sensitive(True)
        except UnicodeDecodeError:
            self.entry.set_text('')
            self.entry.set_sensitive(False)

        self.btn = gtk.Button("...")

    def pack_widgets(self):
        self.entry.set_has_frame(False)
        self.pack_start(self.entry)
        self.pack_start(self.btn, False, False, 0)

    def connect_signals(self):
        self.btn.connect('clicked', self.__on_edit)
        self.entry.connect('changed', self.__on_changed)

    def __on_changed(self, entry):
        if self._ignore_changed:
            self._ignore_changed = False
            return

        self.value = self.entry.get_text()

    def __on_edit(self, widget):
        if not HexView:
            try:
                text = unicode(self.value)
            except UnicodeDecodeError:
                dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                           gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                _("Cannot edit this field because I can't convert it to utf8.\n"
                  "Try to edit the field with python shell or simply install "
                  "pygtkhex that provides a nice HexView to edit raw fields"))
                dialog.run()
                dialog.hide()
                dialog.destroy()

                return


        dialog = gtk.Dialog(_('Editing string field'),
                            None, gtk.DIALOG_MODAL,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        if not HexView:
            buffer = gtk.TextBuffer()
            buffer.set_text(text)

            view = gtk.TextView(buffer)
            view.modify_font(pango.FontDescription(
                Prefs()['gui.maintab.hexview.font'].value))

            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            sw.add(view)
            sw.show_all()

            dialog.vbox.pack_start(sw)
        else:
            hex = HexView()
            hex.set_insert_mode(True)
            hex.set_read_only_mode(False)

            hex.font = Prefs()['gui.maintab.hexview.font'].value
            hex.payload = self.value

            hex.show()
            dialog.vbox.pack_start(hex)

        dialog.set_size_request(400, 300)

        if dialog.run() == gtk.RESPONSE_ACCEPT:
            if not HexView:
                self.entry.set_text(buffer.get_text(buffer.get_start_iter(),
                                                buffer.get_end_iter(), True))
            else:
                self.value = hex.payload
                self._ignore_changed = True

                try:
                    self.entry.set_text(unicode(self.value))
                except UnicodeDecodeError:
                    self.entry.set_text('')

        dialog.hide()
        dialog.destroy()

class IPv4Editor(Editor):
    def create_widgets(self):
        self.entry = HIGIpEntry()

        if self.value:
            self.entry.set_text(self.value)
        #self.entry.set_has_frame(False)

    def pack_widgets(self):
        self.pack_start(self.entry)

    def connect_signals(self):
        self.entry.connect('changed', self.__on_changed)

    def __on_changed(self, entry):
        self.value = self.entry.get_text()

class IPv6Editor(IPv4Editor):
    def create_widgets(self):
        self.entry = HIGIpv6Entry()

        if self.value:
            self.entry.set_text(self.value)

class MACEditor(IPv4Editor):
    def create_widgets(self):
        self.entry = HIGMacEntry()

        if self.value:
            self.entry.set_text(self.value)

def get_editor(field):
    "@return the corresponding editor class for field or None"

    if not backend.is_field(field):
        log.error('%s is not a valid field' % field)
        return None

    # MACField
    # IPField

    # We use a list because order is important here
    table = [(backend.PMMACField, MACEditor),
             (backend.PMStrField, StrEditor),
             (backend.PMIP6Field, IPv6Editor),
             (backend.PMIPField, IPv4Editor),
             (backend.PMEnumField, EnumEditor),
             (backend.PMByteField, IntEditor),
             (backend.PMShortField, IntEditor),
             (backend.PMLEShortField, IntEditor),
             (backend.PMIntField, IntEditor),
             (backend.PMSignedIntField, IntEditor),
             (backend.PMLEIntField, IntEditor),
             (backend.PMLESignedIntField, IntEditor),
             (backend.PMLongField, IntEditor),
             (backend.PMLELongField, IntEditor),
             (backend.PMLenField, IntEditor),
             (backend.PMRDLenField, IntEditor),
             (backend.PMFieldLenField, IntEditor),
             (backend.PMBCDFloatField, IntEditor),
             (backend.PMBitField, IntEditor),
    ]

    for it in table:
        if it[0] != None and backend.implements(field, it[0]):
            return it[1]

class HackEntry(gtk.Entry):
    __gtype_name__ = "HackEntry"
    __gsignals__ = {
        'finish-edit' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                         (gobject.TYPE_OBJECT, ))
    }

    def __init__(self):
        gtk.Entry.__init__(self)

        self.box = gtk.EventBox()
        self.box.set_border_width(0)
        self.connect('parent-set', self.__on_parent_set)

    def do_realize(self):
        self.box.modify_bg(gtk.STATE_NORMAL, self.style.base[gtk.STATE_SELECTED])

    def do_button_press_event(self, event):
        return True

    def do_show(self):
        return

    def __on_parent_set(self, widget, parent):
        if self.get_parent():
            if self.get_parent_window():
                self.box.set_parent_window(self.get_parent_window())
            self.box.set_parent(self.get_parent())
            self.box.show()
        else:
            self.emit('finish-edit', self.box.get_child())
            self.box.unparent()
            self.box.hide()
            self.box.destroy()

    def do_size_allocate(self, alloc):
        # I wanna be extra large! mc donalds rules
        if self.allocation.width > alloc.width and \
           self.allocation.height > alloc.height:
            alloc.width, alloc.height = self.allocation.width, \
                                        self.allocation.height

        gtk.Entry.do_size_allocate(self, alloc)

        # Reserving space for borders
        #alloc.height -= 1
        #alloc.width -= 1
        #alloc.x -= 1
        #alloc.y -= 1

        alloc.x -= 2
        alloc.y -= 2

        self.box.size_request()
        self.box.set_size_request(alloc.width, alloc.height)
        self.box.size_allocate(alloc)

gobject.type_register(HackEntry)

class CellRendererGroup(gtk.CellRendererText):
    __gtype_name__ = "CellRendererGroup"

    def __init__(self, tree):
        super(CellRendererGroup, self).__init__()

        self.tree = tree
        self.set_property('xalign', 0)
        self.set_property('xpad', 3)

        # We use two fields (to avoid creating instances)
        # - editor : containing the class for editor
        # - field  : is the object to edit
        self.editor = None
        self.field = None

        dummy_entry = gtk.Entry()
        dummy_entry.set_has_frame(False)

        font_desc = Prefs()['gui.views.property_tab.font'].value \
                    or 'Monospace 8'
        dummy_entry.modify_font(pango.FontDescription(font_desc))

        self.row_height = dummy_entry.size_request()[1] + 2

    def do_get_size(self, widget, area):
        w, h = 0, 0

        if h < self.row_height:
            h = self.row_height

        w += self.get_property('xpad') * 2
        h += self.get_property('ypad') * 2

        return (0, 0, w, h)

    def do_render(self, window, widget, background_area, \
                  cell_area, expose_area, flags):

        # We draw two lines for emulating a box _|
        cr = window.cairo_create()
        cr.save()

        area = background_area
        cr.set_operator(cairo.OPERATOR_DEST_OVER)

        if self.get_property('cell-background-set'):
            cr.set_source_color(self.get_property('cell-background-gdk'))
            cr.rectangle(area.x, area.y, area.width, area.height)
            cr.fill()

            self.set_property('cell-background-gdk', None)
        else:
            cr.set_operator(cairo.OPERATOR_OVER)

            cr.set_source_color(widget.style.mid[gtk.STATE_NORMAL])
            cr.set_line_width(0.5)

            # Horiz
            cr.move_to(area.x, area.y + area.height - 1)
            cr.rel_line_to(area.width, 0)
            cr.stroke()

            # Vert
            cr.move_to(area.x + area.width - 1, area.y)
            cr.rel_line_to(0, area.height - 1)
            cr.stroke()

        cr.restore()

        if self.editor != None and self.field != None:
            if self.flags() & gtk.CELL_RENDERER_SELECTED:
                state = gtk.STATE_SELECTED
            else:
                state = gtk.STATE_NORMAL

            # Don't create any instance. Use the static method instead
            if self.editor.render(self.field, window, widget, cell_area, state):
                return

        return gtk.CellRendererText.do_render(self, window, widget,
                                              background_area, cell_area,
                                              expose_area, flags)

gobject.type_register(CellRendererGroup)

class CellRendererProperty(CellRendererGroup):
    __gtype_name__ = "CellRendererProperty"

    def __init__(self, tree):
        super(CellRendererProperty, self).__init__(tree)
        self.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
        self.set_property('ellipsize', pango.ELLIPSIZE_END)

    def do_start_editing(self, event, widget, path, \
                         background_area, cell_area, flags):

        if self.editor != None and self.field != None:
            entry = HackEntry()

            font_desc = Prefs()['gui.views.property_tab.font'].value \
                        or 'Monospace 8'

            editor = self.editor(self.field)

            for wid in editor:
                wid.modify_font(pango.FontDescription(font_desc))

            entry.box.add(editor)
            entry.box.show_all()

            entry.connect('finish-edit', self.tree.finish_callback)
            entry.size_allocate(background_area)

            self.editor = None
            self.field = None

            return entry

        # Yes type error - PyGTK bug #542583
        return None

gobject.type_register(CellRendererProperty)

class CellRendererIcon(gtk.CellRendererPixbuf):
    __gtype_name__ = "CellRendererIcon"

    def __init__(self):
        super(CellRendererIcon, self).__init__()

    def do_render(self, window, widget, background_area, \
                  cell_area, expose_area, flags):

        ret = gtk.CellRendererPixbuf.do_render(self, window, widget,
                                               background_area, cell_area,
                                               expose_area, flags)

        cr = window.cairo_create()
        cr.save()

        area = background_area
        cr.set_operator(cairo.OPERATOR_DEST_OVER)

        if self.get_property('cell-background-set'):
            cr.set_source_color(self.get_property('cell-background-gdk'))
            cr.rectangle(area.x, area.y, area.width, area.height)
            cr.fill()

            self.set_property('cell-background-gdk', None)
        else:
            cr.set_operator(cairo.OPERATOR_OVER)
            cr.set_source_color(widget.style.mid[gtk.STATE_NORMAL])
            cr.set_line_width(0.5)

            cr.move_to(area.x, area.y + area.height - 1)
            cr.rel_line_to(area.width, 0)
            cr.stroke()

        cr.restore()

gobject.type_register(CellRendererIcon)

# Simple classes for easy managing of object into the tree store

class TField:
    def __init__(self, field, proto):
        self.ref = field
        self.proto = proto

class TFlag:
    def __init__(self, flag, field):
        self.ref = flag
        self.field = field
        self.proto = field.proto

class PropertyGridTree(gtk.ScrolledWindow):
    __gsignals__ = {
        'finish-edit'    : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            (gobject.TYPE_OBJECT, )),
        'field-selected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,
                             gobject.TYPE_PYOBJECT)),
        'desc-changed'   : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            (gobject.TYPE_STRING, )),
    }

    printable = \
        '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' \
        '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)

        self.packet = None
        self.store = gtk.TreeStore(object)
        self.tree = gtk.TreeView(self.store)

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        col = gtk.TreeViewColumn('Property')
        crt = CellRendererGroup(self)

        crt.set_property('xpad', 0)
        crt.set_property('cell-background-gdk',
                         self.style.mid[gtk.STATE_NORMAL])

        pix = CellRendererIcon()
        pix.set_property('xpad', 0)
        pix.set_property('ypad', 0)

        col.pack_start(pix, False)
        col.pack_start(crt, True)
        col.set_resizable(True)
        col.set_expand(False)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(120)

        col.set_cell_data_func(crt, self.__group_cell_func)
        col.set_cell_data_func(pix, self.__pixbuf_cell_func)
        self.tree.append_column(col)

        col = gtk.TreeViewColumn('Value')
        crt = CellRendererProperty(self)

        col.pack_start(crt, True)
        #col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_resizable(False)
        col.set_expand(True)
        col.set_attributes(crt)

        col.set_cell_data_func(crt, self.__property_cell_func)
        self.tree.append_column(col)

        #self.tree.set_headers_visible(False)
        self.tree.set_search_column(0)
        self.tree.set_search_equal_func(self.__search_func)
        self.tree.set_enable_tree_lines(True) # This don't work with cell back

        self.add(self.tree)

        self.icon_locked = get_pixbuf("locked_small")
        self.finish_callback = self.__on_finish_edit

        self.tree.get_selection().connect('changed',
                                          self.__on_selection_changed)
        self.tree.connect('button-release-event', self.__on_button_release)

    def __search_func(self, model, col, key, iter):
        field = model.get_value(iter, 0)

        if not field or backend.is_proto(field):
            return True

        if isinstance(field, TFlag):
            return not key in field.ref

        name = backend.get_field_name(field.ref)

        return not key in name

    def get_selected_field(self):
        """
        Get the selected field

        @return a tuple (packet, proto, field) containing the parent
                protocol for field and the field or None, None, None
        """

        model, iter = self.tree.get_selection().get_selected()

        if not iter:
            return (None, None, None)

        obj = model.get_value(iter, 0)

        proto = obj.proto

        if isinstance(obj, TField):
            field = obj.ref
        elif isinstance(obj, TFlag):
            field = obj.field
        else:
            field = None

        if not proto or not field or \
           not backend.is_field(field) or \
           not backend.is_proto(proto):

            return (None, None, None)

        return (self.packet, proto, field)

    def __on_selection_changed(self, selection):
        model, iter = selection.get_selected()

        if not iter:
            return

        proto = model.get_value(iter, 0)

        if isinstance(proto, (TField, TFlag)):
            packet, proto, field = self.get_selected_field()

            self.emit('field-selected', packet, proto, field)
            self.emit('desc-changed', backend.get_field_desc(field))
        else:
            # We have selected the protocol
            self.emit('desc-changed', "%s protocol." % \
                      backend.get_proto_name(proto))

    def __on_button_release(self, widget, event):
        # We should get the selection and show the popup

        if event.button != 3:
            return

        if not self.tree.get_selection().get_selected():
            return

        model, iter = self.tree.get_selection().get_selected()
        field = model.get_value(iter, 0)

        if not isinstance(field, TField):
            return

        # We could reset the selected field, all the field in the current
        # protocol, the field in the current protocol and the protocols
        # above, and for all the packet.

        menu = gtk.Menu()

        stocks = (
            gtk.STOCK_GO_FORWARD,
            gtk.STOCK_GO_DOWN,
            gtk.STOCK_GOTO_BOTTOM,
            gtk.STOCK_GOTO_TOP
        )

        labels = (
            _('Reset selected field'),
            _('Reset fields in this protocol'),
            _('Reset fields in above protocols'),
            _('Reset all the packet fields')
        )

        callbacks = (
            self.__on_reset_field,
            self.__on_reset_proto_fields,
            self.__on_reset_above_protos_fields,
            self.__on_reset_packet_fields
        )

        for stock, label, cback, in zip(stocks, labels, callbacks):
            action = gtk.Action(None, label, None, stock)
            action.connect('activate', cback)

            item = action.create_menu_item()
            menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

    def __on_reset_field(self, action):
        packet, proto, field = self.get_selected_field()
        packet.reset(proto, proto, field=field)

    def __on_reset_proto_fields(self, action):
        packet, proto, field = self.get_selected_field()
        packet.reset(proto)

    def __on_reset_above_protos_fields(self, action):
        packet, proto, field = self.get_selected_field()
        packet.reset(startproto=proto)

    def __on_reset_packet_fields(self, action):
        packet, proto, field = self.get_selected_field()
        packet.reset()

    def __on_finish_edit(self, entry, editor):
        self.emit('finish-edit', entry)

    def __property_cell_func(self, col, cell, model, iter):
        cell.editor, cell.field = None, None
        cell.set_property('editable', False)
        cell.set_property('text', '')

        obj = model.get_value(iter, 0)

        if isinstance(obj, TField) and backend.is_flags(obj.ref):
            # Flag container

            cell.set_property('cell-background-gdk',
                              self.style.mid[gtk.STATE_NORMAL])

            value = backend.get_field_value_repr(obj.proto, obj.ref)

            try:
                if value:
                    cell.set_property('markup', '<tt>%s</tt>' % \
                                  gobject.markup_escape_text(unicode(value)))
            except UnicodeDecodeError:
                cell.set_property('markup', _('<tt>N/A</tt>'))


        # If we are a field or a string (a sub field of flags)
        elif isinstance(obj, (TField, TFlag)):

            cell.field = None
            cell.set_property('editable', True)
            cell.set_property('cell-background-gdk', None)

            # We have a standard field

            if isinstance(obj, TField):
                value = backend.get_field_value(obj.proto, obj.ref)

                if value is not None:
                    try:
                        value = gobject.markup_escape_text(unicode(value))
                    except UnicodeDecodeError:
                        value = None

                if not value:
                    value = _("N/A")

                cell.set_property('markup', '<tt>%s</tt>' % value)
                cell.editor = get_editor(obj.ref)

                if cell.editor:
                    cell.field = (obj.proto, obj.ref)

            elif isinstance(obj, TFlag):
                # We have a subkey of Flags

                cell.editor = BitEditor
                cell.field = (obj.proto, obj.field.ref, obj.ref)
        else:
            cell.set_property('cell-background-gdk',
                              self.style.mid[gtk.STATE_NORMAL])

    def __group_cell_func(self, col, cell, model, iter):
        obj = model.get_value(iter, 0)
        color, markup = self.style.mid[gtk.STATE_NORMAL], None

        if isinstance(obj, TFlag):
            color = None
            markup = '<b>%s</b>' % gobject.markup_escape_text(obj.ref)

        elif isinstance(obj, TField):
            # This is a property

            name = gobject.markup_escape_text(backend.get_field_name(obj.ref))
            proto = obj.proto

            if not backend.is_flags(obj.ref):
                color = None

            if backend.is_field_autofilled(obj.ref):
                markup = '<i>%s</i>' % name
            else:
                markup = '<b>%s</b>' % name
        else:
            # Ok. This is the protocol
            name = gobject.markup_escape_text(backend.get_proto_name(obj))
            markup = '<b>%s</b>' % name

        # Setting the values
        cell.set_property('cell-background-gdk', color)
        cell.set_property('markup', markup)

    def __pixbuf_cell_func(self, col, cell, model, iter):
        obj = model.get_value(iter, 0)

        icon, color = None, self.style.mid[gtk.STATE_NORMAL]

        if isinstance(obj, TFlag):
            color = None

        elif isinstance(obj, TField):
            if not backend.is_flags(obj.ref): # Not a flag container
                color = None

            if backend.is_field_autofilled(obj.ref):
                icon = self.icon_locked

        cell.set_property('cell-background-gdk', color)
        cell.set_property('pixbuf', icon)

    def clear(self):
        "Clear the store"
        self.packet = None
        self.store.clear()
        self.emit('desc-changed', '')

    def populate(self, packet, proto_inst):
        """
        Populate the store with the fields of Protocol
        @param packet a Packet that cointains the proto_inst
               or None if not parent is setted
        @param proto_inst a Protocol object instance
        """

        if not proto_inst:
            return

        self.packet = packet
        root_iter = self.store.append(None, [proto_inst])

        # We have to use the get_fields method
        for field in backend.get_proto_fields(proto_inst):

            if not backend.is_showable_field(field, packet):
                continue

            tfield = TField(field, proto_inst)
            flag_iter = self.store.append(root_iter, [tfield])

            if backend.is_flags(field):
                for flag in backend.get_flag_keys(field):
                    self.store.append(flag_iter, [TFlag(flag, tfield)])

        self.tree.expand_row((0, ), False)

gobject.type_register(PropertyGridTree)

class PropertyGrid(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self, False, 2)

        self.set_border_width(2)

        self.__create_toolbar()
        self.__create_widgets()

        self.tree.connect('desc-changed', self.__on_update_desc)

    def __create_widgets(self):
        self.tree = PropertyGridTree()

        self.desc_text = gtk.TextView()
        self.desc_text.set_wrap_mode(gtk.WRAP_WORD)
        self.desc_text.set_editable(False)
        self.desc_text.set_left_margin(5)
        self.desc_text.set_right_margin(5)

        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.add(self.desc_text)

        sw.set_size_request(30, 100)

        toolbox = ToolBox()
        toolbox.append_page(self.tree, '<b>Protocol</b>', gtk.STOCK_CONNECT)
        toolbox.append_page(sw, '<b>Description</b>', gtk.STOCK_JUSTIFY_FILL,
                            expand=False)

        self.pack_start(toolbox)

        self.clear = self.tree.clear
        self.populate = self.tree.populate

    def __create_toolbar(self):
        pass

    def __on_update_desc(self, tree, desc):
        if not desc:
            desc = ""

        desc = desc.replace("  ", "").replace("\n", "").replace("\t", "")
        self.desc_text.get_buffer().set_text(desc)

if __name__ == "__main__":
    w = gtk.Window()
    w.add(PropertyGrid())
    w.show_all()
    w.connect('delete-event', lambda *w: gtk.main_quit())
    gtk.main()
