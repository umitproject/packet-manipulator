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
import cairo
import pango
import gobject

# App
import App

# Protocol stuff
import Backend

# I18N
from umitCore.I18N import _

# For the icons
from Icons import get_pixbuf

# Higwidgets
from higwidgets.higbuttons import MiniButton
from higwidgets.hignetwidgets import HIGIpEntry
from widgets.Expander import ToolBox

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
            return Backend.get_keyflag_value(self.protocol, self.field, self.flag_name)
        else:
            return Backend.get_field_value(self.protocol, self.field)

    def set_value(self, value):
        if self.flag_name != None:
            Backend.set_keyflag_value(self.protocol, self.field, self.flag_name, value)
        else:
            Backend.set_field_value(self.protocol, self.field, value)
    
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
        if Backend.get_field_size(self.protocol, self.field) != None:
            self.min = 0
            self.max = (2 ** Backend.get_field_size(self.protocol, self.field)) - 1 # (2 ^ n) - 1
            self.digits = 0
        else:
            import sys
            print "Hei man we are falling back to sys.maxint for", self.field
            self.min = -sys.maxint - 1
            self.max = sys.maxint
            self.digits = 0
    
    def __on_changed(self, spin):
        if isinstance(self.value, int):
            self.value = self.spin.get_value_as_int()
        else:
            self.value = self.spin.get_value()

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

            if Backend.get_keyflag_value(proto, field, name):
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

        self.combo.pack_start(pix, False)
        self.combo.pack_start(txt)

        self.combo.set_attributes(pix, pixbuf=0)
        self.combo.set_attributes(txt, text=1)

        self.odict = Backend.get_field_enumeration_i2s(self.field)
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
        self.entry.set_text(self.value)
        self.btn = gtk.Button("...")

    def pack_widgets(self):
        self.entry.set_has_frame(False)
        self.pack_start(self.entry)
        self.pack_start(self.btn, False, False, 0)

    def connect_signals(self):
        self.btn.connect('clicked', self.__on_edit)
        self.entry.connect('changed', self.__on_changed)
    
    def __on_changed(self, entry):
        self.value = self.entry.get_text()

    def __on_edit(self, widget):
        print "Yeah launch a dialog to edit the field"

class IPv4Editor(Editor):
    def create_widgets(self):
        self.entry = HIGIpEntry()
        #self.entry.set_has_frame(False)

    def pack_widgets(self):
        self.pack_start(self.entry)

    def connect_signals(self):
        self.entry.connect('changed', self.__on_changed)

    def __on_changed(self, entry):
        self.value = self.entry.get_text()

def get_editor(field):
    "@return the corresponding editor class for field or None"

    assert Backend.is_field(field)

    # MACField
    # IPField

    # We use a list because order is important here
    table = [#(Backend.PMMACField, MACEditor),
             (Backend.PMStrField, StrEditor),
             (Backend.PMIPField, IPv4Editor),
             (Backend.PMEnumField, EnumEditor),
             (Backend.PMByteField, IntEditor),
             (Backend.PMShortField, IntEditor),
             (Backend.PMLEShortField, IntEditor),
             (Backend.PMIntField, IntEditor),
             (Backend.PMSignedIntField, IntEditor),
             (Backend.PMLEIntField, IntEditor),
             (Backend.PMLESignedIntField, IntEditor),
             (Backend.PMLongField, IntEditor),
             (Backend.PMLELongField, IntEditor),
             (Backend.PMLenField, IntEditor),
             (Backend.PMRDLenField, IntEditor),
             (Backend.PMFieldLenField, IntEditor),
             (Backend.PMBCDFloatField, IntEditor),
             (Backend.PMBitField, IntEditor),
    ]

    for it in table:
        if it[0] != None and Backend.implements(field, it[0]):
            return it[1]

class HackEntry(gtk.Entry):
    __gtype_name__ = "HackEntry"
    __gsignals__ = {
        'finish-edit' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT, ))
    }

    def __init__(self):
        gtk.Entry.__init__(self)

        self.box = gtk.EventBox()
        self.box.modify_bg(gtk.STATE_NORMAL, self.style.white)
        self.connect('parent-set', self.__on_parent_set)

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
            alloc.width, alloc.height = self.allocation.width, self.allocation.height

        gtk.Entry.do_size_allocate(self, alloc)

        # Reserving space for borders
        alloc.height -= 1
        alloc.width -= 1
        alloc.x -= 1
        alloc.y -= 1

        self.box.size_request()
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

            entry.box.add(self.editor(self.field))
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

class PropertyGridTree(gtk.ScrolledWindow):
    __gsignals__ = {
        'finish-edit'    : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT, )),
        'field-selected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        'desc-changed'   : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING, )),
    }

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
       
        self.packet = None
        self.store = gtk.TreeStore(object, object)
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
        col.set_expand(True)
        #col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(180)
        
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
        self.tree.set_enable_tree_lines(True) # This don't work with cell back

        self.add(self.tree)

        self.icon_locked = get_pixbuf("locked_small")
        self.finish_callback = self.__on_finish_edit

        self.tree.get_selection().connect('changed', self.__on_selection_changed)
        self.tree.connect('button-release-event', self.__on_button_release)
    
    def get_selected_field(self):
        """
        Get the selected field

        @return a tuple (proto, field) containing the parent
                protocol for field and the field or None, None
        """

        model, iter = self.tree.get_selection().get_selected()

        if not iter:
            return (None, None, None)

        if isinstance(model.get_value(iter, 1), str):
            iter = model.iter_parent(iter)

        if not iter:
            return (None, None, None)

        proto, field = self.__get_parent_field(model, iter)

        if not proto or not field or \
           not Backend.is_field(field) or \
           not Backend.is_proto(proto):

            return (None, None, None)

        return (self.packet, proto, field)

    def __on_selection_changed(self, selection):
        model, iter = selection.get_selected()

        if not iter:
            return

        proto = model.get_value(iter, 0)

        if proto != None:
            # We have selected the protocol
            self.emit('desc-changed', "%s protocol." % Backend.get_proto_name(proto))
        else:
            packet, proto, field = self.get_selected_field()

            self.emit('field-selected', packet, proto, field)
            self.emit('desc-changed', Backend.get_field_desc(field))

    def __on_button_release(self, widget, event):
        # We should get the selection and show the popup

        if event.button != 3:
            return

        if not self.tree.get_selection().get_selected():
            return

        model, iter = self.tree.get_selection().get_selected()
        field = model.get_value(iter, 1)

        if not Backend.is_field(field):
            return

        menu = gtk.Menu()
        item = gtk.MenuItem("Toggle editability of %s" % field.name)
        menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

    def __on_finish_edit(self, entry, editor):
        self.emit('finish-edit', entry)

    def __get_parent_protocol(self, model, iter, idx=0):
        root = model.iter_parent(iter)

        if root:
            return model.get_value(root, idx)

        return None

    def __get_parent_field(self, model, iter):
        proto = self.__get_parent_protocol(model, iter)

        if proto:
            field = model.get_value(iter, 1)

            return proto, field

        return None, None

    def __get_parent_flags_field(self, model, iter):
        root = model.iter_parent(iter)

        if root:
            field = self.__get_parent_protocol(model, iter, 1)
            protocol = self.__get_parent_protocol(model, root)

            if protocol and field:
                return protocol, field

        return None, None

    def __property_cell_func(self, col, cell, model, iter):
        cell.editor, cell.field = None, None
        cell.set_property('editable', False)
        cell.set_property('text', '')
        
        obj = model.get_value(iter, 1)

        if Backend.is_flags(obj):
            cell.set_property('cell-background-gdk',
                              self.style.mid[gtk.STATE_NORMAL])

            protocol = self.__get_parent_protocol(model, iter)

            if protocol:
                value = Backend.get_field_value_repr(protocol, obj)

                if value:
                    cell.set_property('markup', '<tt>%s</tt>' % value)

        # If we are a field or a string (a sub field of flags)
        elif Backend.is_field(obj) or isinstance(obj, str):

            cell.field = None
            cell.set_property('editable', True)
            cell.set_property('cell-background-gdk', None)

            # We have a standard field

            protocol = self.__get_parent_protocol(model, iter)

            if protocol:
                value = Backend.get_field_value(protocol, obj)

                if value is None:
                    value = "N/A"

                cell.set_property('markup', '<tt>%s</tt>' % value)
                cell.editor = get_editor(obj)

                if cell.editor:
                    cell.field = (protocol, obj)
                
                return

            # We have a subkey of Flags
            
            proto, flags = self.__get_parent_flags_field(model, iter)

            if flags:
                cell.editor = BitEditor
                cell.field = (proto, flags, model.get_value(iter, 1))
                
                return
            
        else:
            cell.set_property('cell-background-gdk',
                              self.style.mid[gtk.STATE_NORMAL])

    def __group_cell_func(self, col, cell, model, iter):
        obj = model.get_value(iter, 0)
        color = self.style.mid[gtk.STATE_NORMAL]
        markup = None
        
        if not obj:
            # This is not a group but a property
            obj = model.get_value(iter, 1)
            proto = model.get_value(model.iter_parent(iter), 0)

            if Backend.is_field(obj):

                if Backend.is_flags(obj):
                    color = self.style.mid[gtk.STATE_NORMAL]
                else:
                    color = None
                
                if Backend.is_field_autofilled(obj):
                    markup = '<i>%s</i>' % Backend.get_field_name(obj)
                else:
                    markup = '<b>%s</b>' % Backend.get_field_name(obj)

            elif isinstance(obj, str):
                color = None
                markup = '<b>%s</b>' % obj
        else:
            markup = '<b>%s</b>' % Backend.get_proto_name(obj)
        
        # Setting the values
        cell.set_property('cell-background-gdk', color)
        cell.set_property('markup', markup)
    
    def __pixbuf_cell_func(self, col, cell, model, iter):
        obj = model.get_value(iter, 1)
        
        icon, color = None, self.style.mid[gtk.STATE_NORMAL]
        
        if Backend.is_field(obj):

            if Backend.is_flags(obj):
                color = self.style.mid[gtk.STATE_NORMAL]
            else:
                color = None

            if Backend.is_field_autofilled(obj):
                icon = self.icon_locked

        elif isinstance(obj, str):
            color = None
        
        cell.set_property('cell-background-gdk', color)
        cell.set_property('pixbuf', icon)

    def clear(self):
        "Clear the store"
        self.packet = None
        self.store.clear()

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
        root_iter = self.store.append(None, [proto_inst, None])

        # We have to use the get_fields method
        for field in Backend.get_proto_fields(proto_inst):
            flag_iter = self.store.append(root_iter, [None, field])

            if Backend.is_flags(field):
                for flag in Backend.get_flag_keys(field):
                    self.store.append(flag_iter, [None, flag])

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

        if True:
            toolbox = ToolBox()
            toolbox.append_page(self.tree, '<b>Protocol</b>', gtk.STOCK_CONNECT)
            toolbox.append_page(sw, '<b>Description</b>', gtk.STOCK_JUSTIFY_FILL, expand=False)
            self.pack_start(toolbox)
        else:

            expander = AnimatedExpander('Protocol')
            expander.add(self.tree)

            self.pack_start(expander)

            expander = AnimatedExpander('Description')
            expander.add(sw)

            self.pack_start(expander, False, False)

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
