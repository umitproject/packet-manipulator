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
import gobject

from gtk import gdk
from umit.pm.higwidgets.higbuttons import HIGArrowButton

#
# Reimplementation of gtk.Layout in python
# Example on how to implement a scrollable container in python
#
# Johan Dahlin <johan@gnome.org>, 2006
#
# Readaption for implementing show/hide animation and only one child by
# Francesco Piccinno <stack.box@gmail.com>, 2008
#
# Requires PyGTK 2.8.0 or later

__all__ = ['AnimatedExpander', 'ToolBox']

class Child:
    widget = None
    x = 0
    y = 0

def set_adjustment_upper(adj, upper, always_emit):
    changed = False
    value_changed = False

    min = max(0.0, upper - adj.page_size)

    if upper != adj.upper:
        adj.upper = upper
        changed = True

    if adj.value > min:
        adj.value = min
        value_changed = True

    if changed or always_emit:
        adj.changed()
    if value_changed:
        adj.value_changed()

def new_adj():
    return gtk.Adjustment(0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0)

class Layout(gtk.Container):
    __gsignals__ = {
        'animation-end' : (gobject.SIGNAL_RUN_LAST, None,
                           (gobject.TYPE_BOOLEAN, )),
        'set_scroll_adjustments' : (gobject.SIGNAL_RUN_LAST, None,
                                   (gtk.Adjustment, gtk.Adjustment))
    }

    def __init__(self, orientation=gtk.ORIENTATION_VERTICAL):
        self._child = None
        self._width = 100
        self._height = 100
        self._hadj = None
        self._vadj = None
        self._bin_window = None
        self._hadj_changed_id = -1
        self._vadj_changed_id = -1

        self._orientation = orientation

        self._animating = False
        self._stupid = False
        self._to_show = True

        self._current = 0
        self._dest = 0
        self._speed = 5

        self._time_int = 20
        self._time_tot = 300

        gtk.Container.__init__(self)

        if not self._hadj or not self._vadj:
            self._set_adjustments(self._vadj or new_adj(),
                                  self._hadj or new_adj())

    def _move(self, x=0, y=0):
        if not self._child:
            return

        if x != self._child.x or \
           y != self._child.y:

            self._child.x = x
            self._child.y = y

            self.queue_resize()

    def set_size(self, width, height):
        if self._width != width:
            self._width = width
        if self._height != height:
            self._height = height
        if self._hadj:
            set_adjustment_upper(self._hadj, self._width, False)
        if self._vadj:
            set_adjustment_upper(self._vadj, self._height, False)

        if self.flags() & gtk.REALIZED:
            self._bin_window.resize(max(width, self.allocation.width),
                                    max(height, self.allocation.height))

    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)

        self.window = gdk.Window(
            self.get_parent_window(),
            window_type=gdk.WINDOW_CHILD,
            x=self.allocation.x,
            y=self.allocation.y,
            width=self.allocation.width,
            height=self.allocation.height,
            wclass=gdk.INPUT_OUTPUT,
            colormap=self.get_colormap(),
            event_mask=gdk.VISIBILITY_NOTIFY_MASK)
        self.window.set_user_data(self)

        self._bin_window = gdk.Window(
            self.window,
            window_type=gdk.WINDOW_CHILD,
            x=int(-self._hadj.value),
            y=int(-self._vadj.value),
            width=max(self._width, self.allocation.width),
            height=max(self._height, self.allocation.height),
            colormap=self.get_colormap(),
            wclass=gdk.INPUT_OUTPUT,
            event_mask=(self.get_events() | gdk.EXPOSURE_MASK |
                        gdk.SCROLL_MASK))
        self._bin_window.set_user_data(self)

        self.set_style(self.style.attach(self.window))
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.style.set_background(self._bin_window, gtk.STATE_NORMAL)

        if self._child:
            self._child.widget.set_parent_window(self._bin_window)

        if not self._to_show:
            self.hide()

        self.queue_resize()

    def do_unrealize(self):
        self._bin_window.set_user_data(None)
        self._bin_window.destroy()
        self._bin_window = None
        gtk.Container.do_unrealize(self)

    def _do_style_set(self, style):
        gtk.Widget.do_style_set(self, style)

        if self.flags() & gtk.REALIZED:
            self.style.set_background(self._bin_window, gtk.STATE_NORMAL)

    def do_expose_event(self, event):
        if self._animating:
            if not self.flags() & gtk.VISIBLE:
                self.show()
        else:
            if self._to_show:
                if not self.flags() & gtk.VISIBLE:
                    self.show()
            else:
                if self.flags() & gtk.VISIBLE:
                    self.hide()

        if event.window != self._bin_window:
            return False

        gtk.Container.do_expose_event(self, event)

        return False

    def do_map(self):
        self.set_flags(self.flags() | gtk.MAPPED)

        if self._child:
            flags = self._child.widget.flags()

            if flags & gtk.VISIBLE and not (flags & gtk.MAPPED):
                self._child.widget.map()

        self._bin_window.show()
        self.window.show()

    def do_size_request(self, req):
        req.width = 0
        req.height = 0

        #if self._child and (self._animating or self._to_show):
        if self._child:
            req.width, req.height = self._child.widget.size_request()

    def do_size_allocate(self, allocation):
        self.allocation = allocation

        if self._child:
            rect = gdk.Rectangle(self._child.x, self._child.y,
                                 allocation.width, allocation.height)
            self._child.widget.size_allocate(rect)

        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)
            self._bin_window.resize(max(self._width, allocation.width),
                                    max(self._height, allocation.height))

        self._hadj.page_size = allocation.width
        self._hadj.page_increment = allocation.width * 0.9
        self._hadj.lower = 0
        set_adjustment_upper(self._hadj,
                             max(allocation.width, self._width), True)

        self._vadj.page_size = allocation.height
        self._vadj.page_increment = allocation.height * 0.9
        self._vadj.lower = 0
        self._vadj.upper = max(allocation.height, self._height)
        set_adjustment_upper(self._vadj,
                             max(allocation.height, self._height), True)

        # We should move also the child
        if self._child and self._stupid:
            if self._to_show:
                self._current = 0
            else:
                if self._orientation is gtk.ORIENTATION_VERTICAL:
                    self._current = -max(self._height, allocation.height)
                else:
                    self._current = -max(self._width, allocation.width)

            if self._orientation is gtk.ORIENTATION_VERTICAL:
                self._move(0, self._current)
            else:
                self._move(self._current, 0)

        if self._stupid:
            self._stupid = False

            self._to_show = not self._to_show

            if self._orientation is gtk.ORIENTATION_VERTICAL:
                self._speed = max(self._height, allocation.height)
            else:
                self._speed = max(self._width, allocation.width)

            self._speed /= self._time_tot / self._time_int
            self._speed = int(max(self._speed, 5))

            self._child.widget.set_sensitive(False)

            if self._to_show:
                self._dest = 0
            else:
                if self._orientation is gtk.ORIENTATION_VERTICAL:
                    self._dest = -max(self._height, allocation.height)
                else:
                    self._dest = -max(self._width, allocation.width)

            gobject.timeout_add(self._time_int, self._do_animation)

    def do_set_scroll_adjustments(self, hadj, vadj):
        self._set_adjustments(hadj, vadj)

    def do_forall(self, include_internals, callback, data):
        if self._child:
            callback(self._child.widget, data)

    def do_add(self, widget):
        if self._child:
            raise AttributeError

        child = Child()
        child.widget = widget
        child.x, child.y = 0, 0

        self._child = child

        if self.flags() & gtk.REALIZED:
            widget.set_parent_window(self._bin_window)

        widget.set_parent(self)

    def do_remove(self, widget):
        if self._animating:
            raise Exception("Try later please :)")

        if self._child and self._child.widget == widget:
            self._child = None
            widget.unparent()
        else:
            raise AttributeError

    # Private

    def _set_adjustments(self, hadj, vadj):
        if not hadj and self._hadj:
            hadj = new_adj()

        if not vadj and self._vadj:
            vadj = new_adj()

        if self._hadj and self._hadj != hadj:
            self._hadj.disconnect(self._hadj_changed_id)

        if self._vadj and self._vadj != vadj:
            self._vadj.disconnect(self._vadj_changed_id)

        need_adjust = False

        if self._hadj != hadj:
            self._hadj = hadj
            set_adjustment_upper(hadj, self._width, False)
            self._hadj_changed_id = hadj.connect(
                "value-changed",
                self._adjustment_changed)
            need_adjust = True

        if self._vadj != vadj:
            self._vadj = vadj
            set_adjustment_upper(vadj, self._height, False)
            self._vadj_changed_id = vadj.connect(
                "value-changed",
                self._adjustment_changed)
            need_adjust = True

        if need_adjust and vadj and hadj:
            self._adjustment_changed()

    def _adjustment_changed(self, adj=None):
        if self.flags() & gtk.REALIZED:
            self._bin_window.move(int(-self._hadj.value),
                                  int(-self._vadj.value))
            self._bin_window.process_updates(True)

    def _do_animation(self):
        if not self._child:
            return False

        if not self._child.widget.flags() & gtk.VISIBLE:
            self._child.widget.show()

        if self._to_show:
            if self._current < 0:
                self._current += self._speed

                if self._orientation is gtk.ORIENTATION_VERTICAL:
                    self._move(0, self._current)
                else:
                    self._move(self._current, 0)

                return True
        else:
            if self._current > self._dest:
                self._current -= self._speed

                if self._orientation is gtk.ORIENTATION_VERTICAL:
                    self._move(0, self._current)
                else:
                    self._move(self._current, 0)

                return True

        self._animating = False
        self._set_expanded()
        self.emit('animation-end', self._to_show)
        self._child.widget.set_sensitive(True)

        return False

    def set_expanded(self, val):
        if self._animating:
            return False

        self._to_show = val
        self._set_expanded()

        return True

    def _set_expanded(self):
        if self._to_show:
            self._current = 0

            if self._orientation is gtk.ORIENTATION_VERTICAL:
                self._move(0, self._current)
            else:
                self._move(self._current, 0)

            self.show()
        else:
            if self._orientation is gtk.ORIENTATION_VERTICAL:
                self._current = -self.allocation.height
                self._move(0, self._current)
            else:
                self._current = -self.allocation.width
                self._move(self._current, 0)

            self.hide()

    def toggle_animation(self):
        if self._animating or not self._child:
            return False

        self._animating = True
        self._stupid = True

        self.show()
        self.queue_resize()

        return True

    def get_active(self):
        return self._to_show

Layout.set_set_scroll_adjustments_signal('set-scroll-adjustments')

class AnimatedExpander(gtk.Frame):
    __gtype_name__ = "AnimatedExpander"
    __gsignals__ = {
        'activate' : (gobject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self, label=None, image=gtk.STOCK_PROPERTIES,
                 orientation=gtk.ORIENTATION_VERTICAL):

        gtk.Frame.__init__(self)
        self.set_shadow_type(gtk.SHADOW_NONE)

        if orientation is gtk.ORIENTATION_VERTICAL:
            self.mainbox = gtk.VBox(False, 2)
        else:
            self.mainbox = gtk.HBox(False, 2)

        # What we need is the arrow button a label with markup and
        # optionally a close button :)

        self._arrow = HIGArrowButton(orientation)
        self._arrow.set_relief(gtk.RELIEF_NONE)
        self._arrow.set_size_request(20, 20)

        self._arrow.connect('clicked', self.do_toggle_animation)
        self._arrow.connect('force-clicked', self.do_force_animation)

        self._label = gtk.Label('')
        self.label = label

        self._image = gtk.Image()
        self.image = image

        # The layout part
        self._layout = Layout(orientation)
        self._layout.connect('animation-end',
                             lambda w, z: self.emit('activate'))

        # Pack all

        if orientation is gtk.ORIENTATION_VERTICAL:
            box = gtk.HBox(False, 2)
            self._label.set_alignment(0, 0.5)
        else:
            box = gtk.VBox(False, 2)
            self._label.set_angle(270)
            self._label.set_alignment(0.5, 0)

        box.pack_start(self._arrow, False, False)
        box.pack_start(self._image, False, False)
        box.pack_start(self._label)

        frame = gtk.Frame()
        frame.add(box)

        self._happy_box = gtk.EventBox()
        self._happy_box.add(frame)

        self.mainbox.pack_start(self._happy_box, False, False)
        self.mainbox.pack_start(self._layout)

        gtk.Frame.add(self, self.mainbox)
        self.show_all()

    def do_realize(self):
        gtk.Frame.do_realize(self)

        bg_color = gtk.gdk.color_parse("#FFFFDC")
        gtk.gdk.colormap_get_system().alloc_color(bg_color)

        self._happy_box.modify_bg(gtk.STATE_NORMAL, bg_color)

        # Uhmma uhmma bad trick!
        if not self._layout._to_show:
            self._layout.hide()

    def add_widget(self, widget, show=False):
        """
        Add a widget to the expander.

        @param widget the widget to add
        @param show if the widget should be showed
        """

        self._layout.add(widget)
        self._layout.set_expanded(show)

    def add(self, widget):
        self.add_widget(widget, True)

    def get_label(self):
        return self._label.get_text()

    def set_label(self, txt):
        if not txt:
            txt = ""

        self._label.set_text(txt)
        self._label.set_use_markup(True)

    def do_force_animation(self, btn):
        "override me!"
        pass

    def do_toggle_animation(self, btn):
        if self._layout.toggle_animation():
            self._arrow.set_active(not self._arrow.get_active())

    def get_image(self):
        return self._image

    def set_image(self, stock):
        self._image.set_from_stock(stock, gtk.ICON_SIZE_MENU)

    def get_expanded(self):
        return self._layout.get_active()

    label = property(get_label, set_label)
    image = property(get_image, set_image)

gobject.type_register(AnimatedExpander)

class ToolPage(AnimatedExpander):
    """
    A ToolPage for ToolBox.

    (friend of ToolBox. Don't use in other widgets)
    """
    def __init__(self, parent, label=None, image=gtk.STOCK_PROPERTIES, \
                 expand=True):

        assert(isinstance(parent, ToolBox))

        super(ToolPage, self).__init__(label, image)

        self._parent = parent
        self._expand = expand

        self._layout.connect('animation-end', self.__on_end_anim)

    def __on_end_anim(self, blah, val):
        if not self._layout.get_active():
            if not self._parent._one_page or \
               (self._parent._one_page and self._parent._active_page == self):

                # Second stage! :(
                self._parent._unset_page(self)

    def do_force_animation(self, btn):
        # The user clicked with the right so we must force the hide
        # no repack man!!!

        self.do_toggle_animation(btn, False)

    def do_toggle_animation(self, btn, repack=True):
        if self._layout.get_active():

            # Here we could be too small and user press the button
            # not to hide but to increase the size allocate so
            # we need to handle this situation and repack our page
            # if it was packed with False False. If this function
            # returns False this mean that the widget is at the max
            # size right now so we should do the hide animation stuff
            if repack and self._parent._repack(self):
                return

            # We are active so we have our children naked!
            # what should we do?

            # animation (hide) -> repack

            # static check
            if self._parent._one_page:
                assert(self._parent._active_page == self)

            # the repack is on __end_anim
        else:
            # repack -> animation (show)

            self._parent._set_active_page(self)

        if self._layout.toggle_animation():
            self._arrow.set_active(not self._arrow.get_active())

class ToolBox(gtk.VBox):
    """
    A Simple widget that implements a Qt ToolBox
    like behaviour.
    """

    def __init__(self):
        super(ToolBox, self).__init__(False, 2)
        self.set_border_width(4)

        self._one_page = False
        self._active_page = None
        self._pages = []

    # Public API

    def append_page(self, child, txt=None, image=gtk.STOCK_PROPERTIES, \
                    expand=True):

        page = ToolPage(self, txt, image, expand)
        page.add_widget(child, expand)

        self.pack_start(page, expand, expand)
        self._pages.append(page)
        #self._set_active_page(page)

    # Private API

    def _set_expanded(self, page, val):
        """
        Change the packing of the page
        @param page the page for changes
        @param val if should be expanded
        """
        #page._layout.set_expanded(val)
        self.set_child_packing(page, val, val, 0, gtk.PACK_START)

    def _unset_page(self, page):
        self._set_expanded(page, False)

        #if self._active_page == page:
        # We should do a reverse foreach to find a page
        # that is active but packed with False False

        children = self.get_children()
        children.reverse()

        spulciato = filter(lambda x: x._expand and x._layout.get_active(),
                           children)

        if spulciato:
            children = spulciato

        for child in children:
            if page == child or \
               not isinstance(child, ToolPage) or \
               not child._layout.get_active():
                continue

            info = self.query_child_packing(page)

            # We should check with not because it returns 0 instead
            # of python boolean
            if not info[0] or not info[1]:
                self._active_page = child
                self.set_child_packing(child, True, True, 0, gtk.PACK_START)
                return

        self._active_page = None

    def _repack(self, page):
        if not page._expand:
            return False

        info = self.query_child_packing(page)

        if not info[0] or not info[1]:

            if self._active_page:
                self.set_child_packing(self._active_page, False, False, 0,
                                       gtk.PACK_START)

            self._active_page = page
            self.set_child_packing(page, True, True, 0, gtk.PACK_START)

            return True

        return False

    def _set_active_page(self, page):

        if page._expand and self._active_page:
            if self._one_page:
                self._set_expanded(self._active_page, False)
            else:
                self.set_child_packing(self._active_page, False, False, 0,
                                       gtk.PACK_START)

        self._active_page = page

        if page:

            # Here we should check if there's a child with True as packing
            # options if not ignore the page._expand and set the packing to True

            for child in self.get_children():

                if 1 in self.query_child_packing(child)[0:2]:
                    self.set_child_packing(page, page._expand, page._expand, 0,
                                           gtk.PACK_START)
                    return

            # If we are here not True :D
            self.set_child_packing(page, True, True, 0, gtk.PACK_START)


    # Public stuff

    def get_single_page(self):
        return self._one_page

    def set_single_page(self, val):
        self._one_page = val

    single_page = property(get_single_page, set_single_page)

def main(klass):
    w = gtk.Window()
    vbox = gtk.VBox()

    sw = gtk.ScrolledWindow()
    sw.add(gtk.TextView())
    sw.set_size_request(400, 400)

    exp = klass("miao")
    exp.add_widget(sw, False)

    vbox.pack_start(exp, False, False)

    sw = gtk.ScrolledWindow()
    sw.add(gtk.TextView())

    exp = klass("miao")
    exp.add_widget(sw, False)
    vbox.pack_start(exp)

    vbox.pack_start(gtk.Label("mias"), False, False)
    w.add(vbox)
    w.show_all()

def toolbox():
    w = gtk.Window()
    box = ToolBox()
    box.append_page(gtk.Label("Testing"), "miao")
    box.append_page(gtk.Label("Testing"), "miao", expand=False)
    box.append_page(gtk.Label("Testing"), "miao")
    w.add(box)
    w.show_all()

if __name__ == "__main__":
    main(AnimatedExpander)
    #main(gtk.Expander)
    toolbox()
    gtk.main()
