"""
This module provides:
- HIGTooltipData
- HIGTooltip
"""

import gtk
import gobject
import cairo

from umit.pm.core.i18n import _

class HIGTooltipData(object):
    """
    A class to holds tooltip messages information
    """

    def __init__(self, message, \
                 title=_("<span size=\"medium\"><b>Information</b></span>"), \
                 stock=gtk.STOCK_DIALOG_INFO, file=None):
        """
        Create a HIGTooltipData object

        @param message the message to show (with markups)
        @param the title of ballons (with markups)
        @param stock the stock image to use
        @param file the file to use with image
        """
        self.title = title
        self.message = message
        self.stock = stock
        self.file = file
        self.widgets = []

    def append_widget(self, widget, expand=True, fill=True, padding=0, show=True):
        self.widgets.append(((widget, expand, fill, padding), show))

class HIGTooltip(gtk.Window):
    """
    This is a singleton class so not create
    other instances
    """

    __gtype_name__ = "HIGTooltip"
    __instance = None

    def __init__(self):
        """
        Create a HIGTooltip object
        """
        gtk.Window.__init__(self)#, gtk.WINDOW_POPUP)
        self.set_decorated(False)

        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_MENU) # should be tooltip
        self.set_app_paintable(True)
        self.set_redraw_on_allocate(False)

        self.__create_widgets()
        self.__pack_widgets()

        self._widgets = {}
        self._hover = None
        self._interval = 1000
        self._timeout_id = None
        self._timeout_started = False

        # Used to track placement
        self._is_top = False
        self._is_left = False

        self._tail_height = 20
        self._tail_width = 10
        self._tail_offset = 10

    def __create_widgets(self):
        self._title = gtk.Label()
        self._message = gtk.Label()
        self._icon = gtk.image_new_from_stock(gtk.STOCK_DIALOG_INFO, \
                                              gtk.ICON_SIZE_MENU)

        self._message.set_alignment(0, 0.5)

        # We use label as separator
        
        self._top = gtk.Label()
        self._bottom = gtk.Label()
        self._right = gtk.Label()
        self._left = gtk.Label()

        self.vbox = gtk.VBox()

    def __pack_widgets(self):
        hbox = gtk.HBox(False, 2)
        hbox.pack_start(self._icon, False, False, 0)
        hbox.pack_start(self._title)
        hbox.set_spacing(4)

        self.vbox.pack_start(hbox, False, False, 0)
        self.vbox.pack_start(gtk.HSeparator(), False, False, 0)
        self.vbox.pack_start(self._message, False, False, 0)

        self.vbox.set_spacing(4)
        self.vbox.set_border_width(10)

        table = gtk.Table(3, 3)
        table.attach(self._top, 1, 2, 0, 1, yoptions=gtk.SHRINK)
        table.attach(self._bottom, 1, 2, 2, 3, yoptions=gtk.SHRINK)
        table.attach(self._left, 0, 1, 0, 3, xoptions=gtk.SHRINK)
        table.attach(self._right, 2, 3, 0, 3, xoptions=gtk.SHRINK)
        
        table.attach(self.vbox, 1, 2, 1, 2)

        table.show_all()
        self.add(table)

    def __update_gradient(self):
        alloc = self.allocation

        x, y, w, h = alloc.x, alloc.y, alloc.width, alloc.height
        x, y = 0, 0

        # We use yellow colors
        #start = self.to_cairo_color(self.style.light[gtk.STATE_NORMAL])
        #end   = self.to_cairo_color(self.style.mid[gtk.STATE_NORMAL])

        start = gtk.gdk.color_parse("#FFFFDD")
        end   = gtk.gdk.color_parse("#D0D0B0")

        start = self.to_cairo_color(start)
        end   = self.to_cairo_color(end)

        self.gradient = cairo.LinearGradient(x, y, x, y + h)
        self.gradient.add_color_stop_rgb(0.3, *start)
        self.gradient.add_color_stop_rgb(0.9, *end)

    def do_size_allocate(self, alloc):
        self.__update_gradient()

        return gtk.Window.do_size_allocate(self, alloc)

    def __draw_round_rect(self, cr, x, y, w, h, radius_x=5, radius_y=5):
        ARC_TO_BEZIER = 0.55228475

        if radius_x > w - radius_x:
            radius_x = w / 2
        if radius_y > h - radius_y:
            radius_y = h / 2
    
        c1 = ARC_TO_BEZIER * radius_x
        c2 = ARC_TO_BEZIER * radius_y
    
        cr.new_path()
        cr.move_to(x + radius_x, y)
        cr.rel_line_to(w - 2 * radius_x, 0.0)
        cr.rel_curve_to(c1, 0.0, radius_x, c2, radius_x, radius_y)
        cr.rel_line_to(0, h - 2 * radius_y)
        cr.rel_curve_to(0.0, c2, c1 - radius_x, radius_y, -radius_x, radius_y)
        cr.rel_line_to(-w + 2 * radius_x, 0)
        cr.rel_curve_to(-c1, 0, -radius_x, -c2, -radius_x, -radius_y)
        cr.rel_line_to(0, -h + 2 * radius_y)
        cr.rel_curve_to(0.0, -c2, radius_x - c1, -radius_y, radius_x, -radius_y)
        cr.close_path()

    def set_source_color(self, cr, color):
        cr.set_source_rgb(
                *self.to_cairo_color(color)
        )

    def to_cairo_color(self, color):
        t = (
            float(float(color.red >> 8) / 255.0),
            float(float(color.green >> 8) / 255.0),
            float(float(color.blue >> 8) / 255.0)
        )
        return t

    def __draw_borders(self, alloc, cr=None):
        x, y, w, h = alloc.x, alloc.y, alloc.width, alloc.height
        x, y = 0, 0

        shaping = False

        if not cr:
            shaping = True

            bmp = gtk.gdk.Pixmap(None, w, h, 1)
            cr = bmp.cairo_create()

            # Clear the bmp
            cr.save()
            cr.rectangle(0, 0, w, h)
            cr.set_operator(cairo.OPERATOR_CLEAR)
            cr.fill()
            cr.restore()

            cr.set_source_rgb(1, 1, 1)
        else:
            # Set the gradient
            cr.set_source(self.gradient)

        if self._is_top:
            # If top we should decrease height
            h -= self._tail_height
        else:
            # increase y
            y += self._tail_height
            h -= self._tail_offset * 2 # investigate on it

        if self._is_left:
            # If left we should decrease width
            w -= self._tail_width - self._tail_offset
        else:
            # increase x
            x += self._tail_width - self._tail_offset

        self.__draw_round_rect(cr, x, y, w, h, 8, 10)
        cr.fill_preserve()

        if not shaping:
            # Set the color for border
            cr.set_source_rgb( \
                *self.to_cairo_color(self.style.dark[gtk.STATE_NORMAL]) \
            )
            cr.set_line_width(2)
            cr.stroke()

            cr.set_source(self.gradient)

        # Restore my precious coordinates :D
        x, y, w, h = alloc.x, alloc.y, alloc.width, alloc.height
        x, y = 0, 0

        cr.new_path()
        cr.line_to(*self.__draw_tail(cr, (x, y, w, h)))
        cr.close_path()

        cr.fill()

        if shaping:
            self.shape_combine_mask(bmp, 0, 0)
        else:
            # Set the color for border
            cr.set_line_width(1.5)
            cr.set_source_rgb( \
                *self.to_cairo_color(self.style.dark[gtk.STATE_NORMAL]) \
            )

            # I need the coords
            x, y, w, h = self.__draw_tail(None, (x, y, w, h))

            cr.move_to(x, y)
            cr.rel_line_to(w, h)
            cr.move_to(x, y)

            # Dirty hack here :D
            w *= 3
            w = float(w)

            if w < 0:
                w += 2
            else:
                w -= 2

            cr.rel_line_to(w, h)
            
            cr.stroke()

    def __draw_tail(self, cr, alloc):
        # Dirty zipped function

        x, y, w, h = alloc

        _w = self._tail_width
        _h = self._tail_height

        if cr:
            _h += 2

        start_x = w
        start_y = y

        if self._is_left:
            _w *= -1
        else:
            start_x = x
        
        if self._is_top:
            _h *= -1
            start_y = h

        if cr:
            cr.move_to(start_x, start_y)
            cr.rel_line_to(_w, _h)
            cr.rel_line_to(_w * 2, 0)

            return (start_x, start_y)
        else:
            return (start_x, start_y, _w, _h)

    def do_realize(self):
        gtk.Window.do_realize(self)
        self.__update_gradient()

    def do_expose_event(self, evt):
        # Reshape
        self.__draw_borders(self.allocation, None)

        # Redraw man!
        self.__draw_borders(self.allocation, self.window.cairo_create())

        return gtk.Window.do_expose_event(self, evt)

    def __on_widget_event(self, widget, evt):

        if evt.type == gtk.gdk.LEAVE_NOTIFY:
            self._hover = None
            self._timeout_started = False

            if self._timeout_id:
                gobject.source_remove(self._timeout_id)
                self._timeout_id = None

            self.hide()
        elif evt.type == gtk.gdk.ENTER_NOTIFY:

            if not self._timeout_id:
                self._hover = widget
                self._timeout_started = True

                self._timeout_id = gobject.timeout_add(self._interval, \
                                                       self.__show_tooltip, \
                                                       widget)

    @staticmethod
    def add_widget(widget, data):
        """
        Add a tooltip to the widget

        @param widget the widget
        @param data the HIGTooltipData
        """
        assert isinstance(data, HIGTooltipData), \
               "must be a HIGTooltipData object"

        if widget in HIGTooltip.get_instance().widgets:
            return

        widget.add_events(
            gtk.gdk.ALL_EVENTS_MASK |        \
            gtk.gdk.LEAVE_NOTIFY_MASK |      \
            gtk.gdk.PROXIMITY_IN_MASK |      \
            gtk.gdk.ENTER_NOTIFY_MASK |      \
            gtk.gdk.FOCUS_CHANGE_MASK |      \
            gtk.gdk.POINTER_MOTION_MASK |    \
            gtk.gdk.POINTER_MOTION_HINT_MASK
        )
        widget.connect('event', HIGTooltip.get_instance().__on_widget_event)

        HIGTooltip.get_instance().widgets[widget] = data
    
    def show_at(self, w, data, x, y, time=None):
        """
        Show the tooltip at location

        (make x, y optional)
        """

        assert self != HIGTooltip.__instance, \
               "You should create another HIGTooltip object to do it"

        if self._timeout_started or \
           self.flags() & gtk.VISIBLE or \
           self._hover:
            return False

        # We pack the childs now
        for child, show in data.widgets:
            self.vbox.pack_start(*child)

            if show:
                child[0].show()

        w.get_toplevel().connect('configure-event', self.__close_on_event)

        self._hover = w
        self._timeout_started = True
        self.__show_tooltip(w, data, x, y)

        if time:
            self._timeout_id = gobject.timeout_add(time, self.close_and_destroy)
    def __close_on_event(self, w, event):
        self.close_and_destroy()

    def close_and_destroy(self):
        """
        Hide the widget resetting values used and also destroy window
        """
        assert self != HIGTooltip.__instance, \
               "You should create another HIGTooltip object to do it"

        self._hover = None
        self._timeout_started = False

        if self._timeout_id:
            gobject.source_remove(self._timeout_id)
            self._timeout_id = None

        self.hide()
        self.destroy()

        return False

    def __show_tooltip(self, w, data=None, x=None, y=None):
        if not self._timeout_started or \
           self.flags() & gtk.VISIBLE or \
           self._hover != w:
            return False

        if not data:
            window = w.get_toplevel().window

            x, y = window.get_position()
            px, py, pmask = window.get_pointer()

            x += px; y += py

        rect = w.get_allocation()

        # We need to choose where show the ballons
        # bottom, top, right, left, bright, bleft, tright, tleft

        offset = 100
        s_w, s_h = gtk.gdk.screen_width(), gtk.gdk.screen_height()

        if x > s_w - offset: self._is_left = True
        else: self._is_left = False

        if y > s_h - offset: self._is_top = True
        else: self._is_top = False
        
        if not data:
            data = self._widgets[w]

        self.title = data.title
        self.message = data.message
        
        if data.stock:
            self.icon = data.stock
        else:
            self.set_icon_from_file(data.file)

        self.bottom = -1
        self.right = -1
        self.left = -1
        self.top = -1

        if self._is_top:
            self.top = 0
            y -= 100
        else:
            self.bottom = 0
            y += 5

        if self._is_left:
            self.left = 0
            x -= 150
        else:
            self.right = 0
            x += 5

        self.move(x, y)
        self.resize(150, 100)
        self.show()

        return False

    @staticmethod
    def get_instance():
        "Return the instance of HIGTooltip"
        if not HIGTooltip.__instance:
            HIGTooltip.__instance = HIGTooltip()

        return HIGTooltip.__instance

    def get_icon(self):
        return self._icon

    def set_icon(self, value):
        self._icon.set_from_stock(value, gtk.ICON_SIZE_MENU)

    def set_icon_from_file(self, value):
        self._icon.set_from_file(value)

    def get_title(self):
        return self._title.get_text()

    def set_title(self, txt):
        self._title.set_text(txt)
        self._title.set_use_markup(True)

    def get_message(self):
        return self._message.get_text()

    def set_message(self, txt):
        self._message.set_text(txt)
        self._message.set_use_markup(True)

    def get_widgets(self):
        return self._widgets

    widgets = property(get_widgets)
    icon = property(get_icon, set_icon)
    title = property(get_title, set_title)
    message = property(get_message, set_message)

    def get_top(self):
        return 0
    def set_top(self, x):
        self._top.set_size_request(-1, x)

    def get_bottom(self):
        return 0
    def set_bottom(self, x):
        self._bottom.set_size_request(-1, x)


    top = property(get_top, set_top)
    bottom = property(get_bottom, set_bottom)

    def get_left(self):
        return 0
    def set_left(self, y):
        self._left.set_size_request(y, -1)

    def get_right(self):
        return 0
    def set_right(self, y):
        self._right.set_size_request(y, -1)

    left = property(get_left, set_left)
    right = property(get_right, set_right)

if __name__ == "__main__":
    w = gtk.Window()
    b = gtk.Button(stock=gtk.STOCK_OK)
    
    HIGTooltip.add_widget(
        b,
        HIGTooltipData(
            "<b>This</b> is an error:\n<tt>what the hell</tt>",
            stock=gtk.STOCK_DIALOG_ERROR
        )
    )
    bb = gtk.VBox()
    bb.pack_start(b)

    b = gtk.Button(stock=gtk.STOCK_CANCEL)
    HIGTooltip.add_widget(
        b,
        HIGTooltipData(
            "This is a message with a throbber as image :)",
            stock=None,
            file="share/pixmaps/Throbber.gif"
        )
    )
    bb.pack_start(b)
    
    w.add(bb)
    w.show_all()
    
    w.connect('delete-event', lambda *w: gtk.main_quit())
    gtk.main()
