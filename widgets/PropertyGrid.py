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
from umpa.protocols import _ as base

# For the icons
from Icons import get_pixbuf

# Higwidgets
from higwidgets.hignetwidgets import HIGIpEntry

class Editor(gtk.HBox):

    def __init__(self, field):
        gtk.HBox.__init__(self, 0, False)

        self.field = field
        self.create_widgets()
        self.pack_widgets()
        self.connect_signals()

        self.show()

    def create_widgets(self):  pass
    def pack_widgets(self):    pass
    def connect_signals(self): pass

    def get_value(self):
        return self.field.get()

    def set_value(self, value):
        self.field.set(value)
    
    @staticmethod
    def render(field, window, widget, bounds, state):
        return False

    value = property(get_value, set_value)

class IntEditor(Editor):
    # Check the tipe in __init__

    def create_widgets(self):
        # Manage the None type
        if not self.value:
            self.value = 0

        self.calc_bounds()
        self.adj = gtk.Adjustment(self.value, self.min, self.max, 1, 2)
        self.spin = gtk.SpinButton(self.adj, digits=self.digits)

    def pack_widgets(self):
        self.pack_start(self.spin)
        #self.spin.set_has_frame(False)
        self.spin.show()
    
    def connect_signals(self):
        self.spin.connect('value-changed', self.__on_changed)
    
    def calc_bounds(self):
        # Unsigned int / Int? :(
        if self.field.bits:
            self.min = 0
            self.max = (2 ** self.field.bits) - 1 # (2 ^ n) - 1
            self.digits = 0
        elif isinstance(self.value, int):
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

class BitField(base.Field):
    bits = 1
    auto = False

    def __init__(self, flag, name, value):
        self.name = name
        self.parent = flag
        super(BitField, self).__init__(name, value, 1)

    def set(self, val):
        if val:
            self.parent.set(self.name)
        else:
            self.parent.unset(self.name)
        super(BitField, self).set(val)

    def _is_valid(self, val):
        return True

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
        if field.get():
            sh = gtk.SHADOW_IN
        else:
            sh = gtk.SHADOW_OUT

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
        if self.allocation.width >= alloc.width and \
           self.allocation.height >= alloc.height:
            return

        gtk.Entry.do_size_allocate(self, alloc)

        # Reserving space for borders
        alloc.height -= 1
        alloc.width -= 1

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
        self.row_height = dummy_entry.size_request()[1]
    
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
        
        cr.set_source_color(widget.style.mid[gtk.STATE_NORMAL])
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_line_width(0.25)
        
        area = background_area
        
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
        
        area = background_area
        cr = window.cairo_create()
        cr.save()
        
        cr.set_source_color(widget.style.mid[gtk.STATE_NORMAL])
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_line_width(0.25)
        
        cr.move_to(area.x, area.y + area.height - 1)
        cr.rel_line_to(area.width, 0)
        cr.stroke()
        
        cr.restore()

gobject.type_register(CellRendererIcon)

class PropertyGridTree(gtk.ScrolledWindow):
    __gsignals__ = {
        'finish-edit' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT, )),
        'desc-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING, )),
    }

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        
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
        col.set_attributes(crt)
        
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

    def __on_selection_changed(self, selection):
        model, iter = selection.get_selected()

        if not iter:
            return

        proto = model.get_value(iter, 0)

        if proto != None:
            # We have selected the protocol
            self.emit('desc-changed', "%s protocol." % Backend.get_proto_name(proto))
        else:
            proto = model.get_value(model.iter_parent(iter), 0)
            field = model.get_value(iter, 1)

            if not isinstance(field, base.Field) or \
               not isinstance(proto, base.Protocol):
                return
            
            self.emit('desc-changed', Backend.get_field_desc(field))

            # We should select also the bounds in HexView
            nb = App.PMApp().main_window.main_tab.session_notebook
            page = nb.get_nth_page(nb.get_current_page())

            # The page *MUST* be a SessionPage otherwise the signal
            # we cannot be here becouse this widget is insentive
            # so no worry about it.

            print Backend.get_field_key(proto, field)

            print page.hexview, proto.get_offset(field)
            

    def __on_finish_edit(self, entry, editor):
        self.emit('finish-edit', entry)

    def __property_cell_func(self, col, cell, model, iter):
        cell.editor, cell.field = None, None
        cell.set_property('editable', False)
        cell.set_property('text', '')
        
        obj = model.get_value(iter, 1)
        
        if isinstance(obj, base.Flags):
            cell.set_property('cell-background-gdk',
                              self.style.mid[gtk.STATE_NORMAL])
        elif isinstance(obj, base.Field):
            cell.field = obj
            cell.set_property('editable', True)

            if not obj.get() is None:
                cell.set_property('markup', '<tt>%s</tt>' % obj.get())
            else:
                cell.set_property('markup', '<tt>N/A</tt>')

            if obj.bits == 1:
                cell.editor = BitEditor
            elif isinstance(obj, base.IntField):
                cell.editor = IntEditor
            elif isinstance(obj, base.IPv4Field):
                cell.editor = IPv4Editor
            else:
                cell.field = None
            
            cell.set_property('cell-background-gdk', None)
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
            
            if isinstance(obj, base.Field):

                if isinstance(obj, base.Flags):
                    color = self.style.mid[gtk.STATE_NORMAL]
                else:
                    color = None
                
                if obj.auto:
                    markup = '<i>%s</i>' % Backend.get_field_name(obj)
                else:
                    markup = '<b>%s</b>' % Backend.get_field_name(obj)
        else:
            markup = '<b>%s</b>' % Backend.get_proto_name(obj)
        
        # Setting the values
        cell.set_property('cell-background-gdk', color)
        cell.set_property('markup', markup)
    
    def __pixbuf_cell_func(self, col, cell, model, iter):
        obj = model.get_value(iter, 1)
        
        icon, color = None, self.style.mid[gtk.STATE_NORMAL]
        
        if isinstance(obj, base.Field):

            if isinstance(obj, base.Flags):
                color = self.style.mid[gtk.STATE_NORMAL]
            else:
                color = None

            if obj.auto:
                icon = self.icon_locked
        
        cell.set_property('cell-background-gdk', color)
        cell.set_property('pixbuf', icon)

    def clear(self):
        "Clear the store"
        self.store.clear()

    def populate(self, proto_inst):
        """
        Populate the store with the fields of Protocol
        @param proto_inst a Protocol object instance
        """
        root_iter = self.store.append(None, [proto_inst, None])

        # We have to use the get_fields method
        for field in proto_inst.get_fields():
            flag_iter = self.store.append(root_iter, [None, field])

            if isinstance(field, base.Flags):
                for flag in Backend.get_flag_keys(field):
                    self.store.append(flag_iter,
                        [None, BitField(field, flag, field.get(flag)[0])]
                    )

gobject.type_register(PropertyGridTree)

class PropertyGrid(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)

        self.__create_toolbar()
        self.__create_widgets()

        self.tree.connect('desc-changed', self.__on_update_desc)

    def __create_widgets(self):
        self.tree = PropertyGridTree()

        self.expander = gtk.Expander("Description")

        self.desc_text = gtk.TextView()
        self.desc_text.set_wrap_mode(gtk.WRAP_WORD)
        self.desc_text.set_size_request(1, 70)
        self.desc_text.set_editable(False)
        self.desc_text.set_left_margin(5)
        self.desc_text.set_right_margin(5)

        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.add(self.desc_text)

        self.expander.add(sw)
        
        self.pack_start(self.tree)
        self.pack_start(self.expander, False, False)

        self.clear = self.tree.clear
        self.populate = self.tree.populate

    def __create_toolbar(self):
        pass

    def __on_update_desc(self, tree, desc):
        if not desc:
            desc = ""

        self.desc_text.get_buffer().set_text(desc)

if __name__ == "__main__":
    w = gtk.Window()
    w.add(PropertyGrid())
    w.show_all()
    w.connect('delete-event', lambda *w: gtk.main_quit())
    gtk.main()
