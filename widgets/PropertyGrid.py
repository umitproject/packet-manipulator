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
import pango
import gobject

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
        return self.field.value

    def set_value(self, value):
        self.field.value = value
    
    def render(self, window, widget, bounds, state):
        return False

    value = property(get_value, set_value)

class IntEditor(Editor):
    # Check the tipe in __init__

    def create_widgets(self):
        self.calc_bounds()
        self.adj = gtk.Adjustment(self.value, self.min, self.max, 1, 2)
        self.spin = gtk.SpinButton(self.adj, digits=self.digits)

    def pack_widgets(self):
        self.pack_start(self.spin)
        self.spin.set_has_frame(False)
        self.spin.show()
    
    def connect_signals(self):
        self.spin.connect('value-changed', self.__on_changed)
    
    def calc_bounds(self):
        import sys
        
        if isinstance(self.value, int):
            self.min = -sys.maxint - 1
            self.max = sys.maxint
            self.digits = 0
        elif isinstance(self.value, float):
            # FIXME: i dunno here
            self.min = -sys.maxint - 1
            self.max = sys.maxint
            self.digits = 2
        else:
            self.min = 0
            self.max = 10
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
    
    def render(self, window, widget, bounds, state):
        if self.value:
            sh = gtk.SHADOW_IN
        else:
            sh = gtk.SHADOW_OUT

        size = 15
        
        if size > bounds.height:
            size = bounds.height
        if size > bounds.width:
            size = bounds.width
            
        # Paint a center check button
        widget.style.paint_check(window, state, sh, bounds, widget, \
            "checkbutton",                                          \
            #bounds.x + (bounds.width - size) / 2,                   \
            bounds.x                                                \
            bounds.y + (bounds.height - size) / 2,                  \
            size, size)
        
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

class HackEntry(gtk.Entry):
    __gtype_name__ = "HackEntry"

    def __init__(self):
        gtk.Entry.__init__(self)

        self.box = gtk.EventBox()
        self.box.modify_bg(gtk.STATE_NORMAL, self.style.white)
        self.box.connect('button-press-event', lambda *w: True)

        self.connect('parent-set', self.__on_parent_set)

    def do_show(self):
        return

    def __on_parent_set(self, widget, parent):
        if self.get_parent():
            if self.get_parent_window():
                self.box.set_parent_window(self.get_parent_window())
            self.box.set_parent(self.get_parent())
            self.box.show()
        else:
            self.box.unparent()

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

class CellRendererGroup(gtk.CellRendererText):
    __gtype_name__ = "CellRendererGroup"
    
    def __init__(self, tree):
        super(CellRendererGroup, self).__init__()

        self.tree = tree
        self.set_property('xalign', 0)
        self.set_property('xpad', 3)

        self.editor = None

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
        widget.style.paint_hline(
            window, gtk.STATE_NORMAL,
            background_area, widget, "cell-line",
            background_area.x, background_area.x + background_area.width,
            background_area.y + background_area.height - 1)

        widget.style.paint_vline( \
            window, gtk.STATE_NORMAL,
            background_area, widget, "cell-line",
            background_area.y,
            background_area.y + background_area.height - 1,
            background_area.x + background_area.width - 1
        )

        if self.editor:
            if self.flags() & gtk.CELL_RENDERER_SELECTED:
                state = gtk.STATE_SELECTED
            else:
                state = gtk.STATE_NORMAL

            if self.editor.render(window, widget, cell_area, state):
                return
                
        return gtk.CellRendererText.do_render( \
            self, window, widget, background_area, cell_area, expose_area, flags
        )

gobject.type_register(CellRendererGroup)
   
class CellRendererProperty(CellRendererGroup):
    __gtype_name__ = "CellRendererProperty"
    
    def __init__(self, tree):
        super(CellRendererProperty, self).__init__(tree)
        self.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)

    def do_start_editing(self, event, widget, path, \
                         background_area, cell_area, flags):

        entry = HackEntry()

        entry.box.add(self.editor)
        entry.box.show_all()

        entry.size_allocate(background_area)

        # Yes type error - PyGTK bug #542583
        return entry

gobject.type_register(CellRendererProperty)

class PropertyGridTree(gtk.ScrolledWindow):
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        
        self.store = gtk.TreeStore(object, object)
        self.tree = gtk.TreeView(self.store)

        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        col = gtk.TreeViewColumn('Property')
        crt = CellRendererGroup(self.tree)

        crt.set_property('xpad', 0)
        crt.set_property('cell-background-gdk',
                         self.style.base[gtk.STATE_INSENSITIVE])

        col.pack_start(crt, True)
        col.set_resizable(True)
        col.set_expand(True)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(180)
        col.set_attributes(crt)
        
        col.set_cell_data_func(crt, self.__group_cell_func)
        self.tree.append_column(col)

        col = gtk.TreeViewColumn('Value')
        crt = CellRendererProperty(self.tree)

        col.pack_start(crt, True)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_resizable(False)
        col.set_expand(True)
        col.set_attributes(crt)

        col.set_cell_data_func(crt, self.__property_cell_func)
        self.tree.append_column(col)
        #self.tree.set_headers_visible(False)
        self.tree.set_enable_tree_lines(True) # This don't work with cell back

        self.add(self.tree)
        
        class G(object):
            def __init__(self, name):
                self.name = name
        
        class P(object):
            def __init__(self, name, value):
                self.name = name
                self.value = value

        it = self.store.append(None, [G("Generals fields"), None])
        self.store.append(it, [None, P("string", "miao")])
        self.store.append(it, [None, P("boolean", True)])
        self.store.append(it, [None, P("integer", 1)])

    def __property_cell_func(self, col, cell, model, iter):
        cell.editor = None
        cell.set_property('editable', False)
        cell.set_property('text', '')
        
        obj = model.get_value(iter, 1)
        
        if obj != None:
            cell.set_property('editable', True)
            cell.set_property('markup', '<tt>%s</tt>' % obj.value)
            
            if isinstance(obj.value, bool):
                cell.editor = BitEditor(obj)
            elif isinstance(obj.value, str):
                cell.editor = StrEditor(obj)
            elif isinstance(obj.value, int) or \
                 isinstance(obj.value, float):
                cell.editor = IntEditor(obj)

    def __group_cell_func(self, col, cell, model, iter):
        obj = model.get_value(iter, 0)
        
        if not obj:
            obj = model.get_value(iter, 1)
        
        if obj:
            cell.set_property('markup', '<b>%s</b>' % obj.name)

class PropertyGrid(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)

        self.__create_toolbar()
        self.__create_widgets()

    def __create_widgets(self):
        self.tree = PropertyGridTree()
        self.pack_end(self.tree)

    def __create_toolbar(self):
        pass

if __name__ == "__main__":
    w = gtk.Window()
    w.add(PropertyGrid())
    w.show_all()
    w.connect('delete-event', lambda *w: gtk.main_quit())
    gtk.main()
