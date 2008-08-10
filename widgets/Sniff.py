import gtk
import pango
import gobject
import Backend

from umitCore.I18N import _

from Manager.PreferenceManager import Prefs
from higwidgets.higanimates import HIGAnimatedBar

class SniffRenderer(gtk.CellRendererText):
    __gtype_name__ = "SniffRenderer"

    def do_render(self, window, widget, back, cell, expose, flags):
        cr = window.cairo_create()
        cr.save()

        cr.set_line_width(0.5)
        cr.set_dash([1, 1], 1)
        cr.move_to(back.x, back.y + back.height)
        cr.line_to(back.x + back.width, back.y + back.height)
        cr.stroke()

        cr.restore()

        return gtk.CellRendererText.do_render(self, window, widget, back, cell, expose, flags)

gobject.type_register(SniffRenderer)

class SniffPage(gtk.VBox):
    COL_NO     = 0
    COL_TIME   = 1
    COL_SRC    = 2
    COL_DST    = 3
    COL_PROTO  = 4
    COL_INFO   = 5
    COL_COLOR  = 6
    COL_OBJECT = 7

    def __init__(self, context):
        super(SniffPage, self).__init__(False, 4)
        
        self.set_border_width(2)

        self.__create_toolbar()
        self.__create_view()

        self.statusbar = HIGAnimatedBar(_('Sniffing on <tt>%s</tt> ...') % \
                                        context.iface, gtk.STOCK_INFO)
        self.pack_start(self.statusbar, False, False)

        self.show_all()

        self.use_colors = True

        # TODO: get from preference
        self.colors = (
            gtk.gdk.color_parse('#FFFA99'),
            gtk.gdk.color_parse('#8DFF7F'),
            gtk.gdk.color_parse('#FFE3E5'),
            gtk.gdk.color_parse('#C797FF'),
            gtk.gdk.color_parse('#A0A0A0'),
            gtk.gdk.color_parse('#D6E8FF'),
            gtk.gdk.color_parse('#C2C2FF'),
        )

        Prefs()['gui.maintab.sniffview.font'].connect(self.__modify_font)
        Prefs()['gui.maintab.sniffview.usecolors'].connect(self.__modify_colors)

        self.context = context
        self.context.start()

        self.timeout_id = gobject.timeout_add(200, self.__update_tree)
        self.tree.get_selection().connect('changed', self.__on_selection_changed)
        self.filter.get_entry().connect('activate', self.__on_apply_filter)

    def __create_toolbar(self):
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        stocks = (
            gtk.STOCK_MEDIA_STOP,
            gtk.STOCK_SAVE_AS
        )

        callbacks = (
            self.__on_stop,
            self.__on_save_as
        )

        for stock, callback in zip(stocks, callbacks):
            action = gtk.Action(None, None, None, stock)
            action.connect('activate', callback)

            self.toolbar.insert(action.create_tool_item(), -1)

        self.filter = SniffFilter()

        item = gtk.ToolItem()
        item.add(self.filter)
        item.set_expand(True)

        self.toolbar.insert(item, -1)

        self.pack_start(self.toolbar, False, False)

    def __create_view(self):
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.store = gtk.ListStore(int, str, str, str, str, str, gtk.gdk.Color, object)
        self.tree = gtk.TreeView(self.store)

        # Create a filter function
        self.model_filter = self.store.filter_new()
        self.model_filter.set_visible_func(self.__filter_func)

        self.tree.set_model(self.model_filter)

        idx = 0
        for txt in (_('No.'), _('Time'), _('Source'), \
                    _('Destination'), _('Protocol'), _('Info')):

            rend = SniffRenderer()
            col = gtk.TreeViewColumn(txt, rend, text=idx, cell_background_gdk=6)
            self.tree.append_column(col)
            idx += 1

        sw.add(self.tree)
        self.pack_start(sw)

    def __modify_font(self, font):
        try:
            desc = pango.FontDescription(font)

            for col in self.tree.get_columns():
                for rend in col.get_cell_renderers():
                    rend.set_property('font-desc', desc)
        except:
            # Block change

            return True
    
    def __modify_colors(self, value):
        self.use_colors = value
        self.tree.set_rules_hint(not self.use_colors)

        self.store.foreach(self.__update_row_color)

    def __update_row_color(self, model, path, iter):
        model.set_value(iter, 6, self.__get_color(model.get_value(iter, 7)))

    def __get_color(self, packet):
        if self.use_colors:
            proto = packet.get_protocol_str()
            return self.colors[hash(proto) % len(self.colors)]
        else:
            return None

    def __update_tree(self):
        for packet in self.context.get_data():
            id = len(self.store) + 1

            self.store.append(
                [
                 id, packet.get_time(), packet.get_source(),
                 packet.get_dest(), packet.get_protocol_str(), packet.summary(),
                 self.__get_color(packet), packet
                ]
            )

            # Scroll to end
            if self.context.auto_scroll:
                self.tree.scroll_to_cell(len(self.model_filter) - 1)

        alive = self.context.is_alive()

        if self.context.exception:
            self.statusbar.label = "<b>%s</b>" % self.context.exception
            self.statusbar.image = gtk.STOCK_DIALOG_ERROR
            self.statusbar.start_animation(True)
        elif not alive:
            self.statusbar.label = \
                _("<b>Sniffing session finished (%d packets caputered)</b>") % self.context.tot_count
            self.statusbar.image = gtk.STOCK_INFO
            self.statusbar.start_animation(True)

        return alive

    def stop_sniffing(self):
        if self.context:
            self.context.destroy()

    # Signals callbacks

    def __on_selection_changed(self, selection):
        model, iter = selection.get_selected()

        if not iter:
            return

        packet = model.get_value(iter, self.COL_OBJECT)

        if not packet:
            return

        from App import PMApp
        nb = PMApp().main_window.get_tab("MainTab").session_notebook
        nb.set_view_page(packet)

    def __on_apply_filter(self, entry):
        self.model_filter.refilter()

    def __filter_func(self, model, iter):
        txt = self.filter.get_text()

        if not txt:
            return True

        for idx in xrange(6):
            if txt in str(model.get_value(iter, idx)):
                return True

        return False

    def __on_stop(self, action):
        if self.context.is_alive():
            self.context.destroy()

    def __on_save_as(self, action):
        if self.context.is_alive():
            return

        if not self.context.cap_file:
            dialog = gtk.FileChooserDialog(_('Save Pcap file to'),
                    self.get_toplevel(), gtk.FILE_CHOOSER_ACTION_SAVE,
                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                             gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))

            for name, pattern in ((_('Pcap files'), '*.pcap'),
                                  (_('Pcap gz files'), '*.pcap.gz'),
                                  (_('All files'), '*')):

                filter = gtk.FileFilter()
                filter.set_name(name)
                filter.add_pattern(pattern)
                dialog.add_filter(filter)

            if dialog.run() == gtk.RESPONSE_ACCEPT:
                self.context.cap_file = dialog.get_filename()

            dialog.hide()
            dialog.destroy()

        if not self.context.cap_file:
            return

        lst = []
        iter = None

        for idx in xrange(len(self.store)):
            iter = self.store.get_iter((idx, ))
            lst.append(self.store.get_value(iter, self.COL_OBJECT))

        # Now dump to file
        self.statusbar.label = \
            _("<b>Written %d packets to %s</b>") % (len(lst), self.context.cap_file)

        Backend.write_pcap_file(self.context.cap_file, lst)

        self.statusbar.image = gtk.STOCK_HARDDISK
        self.statusbar.start_animation(True)

class SniffFilter(gtk.HBox):
    __gtype_name__ = "SniffFilter"

    def __init__(self):
        super(SniffFilter, self).__init__(False, 2)

        self.set_border_width(4)

        self._entry = gtk.Entry()
        self._box = gtk.EventBox()
        self._box.add(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_MENU))

        self._entry.set_has_frame(False)

        self.pack_start(self._entry)
        self.pack_end(self._box, False, False)

        self._box.connect('button-release-event', self.__on_button_release)
        self._entry.connect('changed', self.__on_update)

        self._colors = None
    
    def do_realize(self):
        gtk.HBox.do_realize(self)

        self._colors = (
            self.style.white,
            gtk.gdk.color_parse("#FEFEDC")
        )
        
        self.__on_update(self._entry)

    def do_expose_event(self, evt):
        alloc = self.allocation    
        rect = gtk.gdk.Rectangle(alloc.x, alloc.y, alloc.width, alloc.height)

        self.style.paint_flat_box(
            self.window,          
            self._entry.state,  
            self._entry.get_property('shadow_type'),
            alloc,                                    
            self._entry,                            
            'entry_bg',                               
            rect.x, rect.y, rect.width, rect.height   
        )                                             

        self.style.paint_shadow(
            self.window,        
            self._entry.state,
            self._entry.get_property('shadow_type'),
            alloc,                                    
            self._entry,                            
            'entry',                                  
            rect.x, rect.y, rect.width, rect.height   
        )

        return gtk.HBox.do_expose_event(self, evt)

    def __on_button_release(self, image, evt):
        if evt.button == 1:
            self._entry.set_text('')

    def __on_update(self, entry):
        if self._entry.get_text():
            color = self._colors[1]
        else:
            color = self._colors[0]

        self._entry.modify_base(gtk.STATE_NORMAL, color)
        self._box.modify_bg(gtk.STATE_NORMAL, color)
        self.modify_base(gtk.STATE_NORMAL, color)

    def get_text(self):
        return self._entry.get_text()

    def set_text(self, txt):
        self._entry.set_text(txt)

    def get_entry(self):
        return self._entry

gobject.type_register(SniffFilter)

class SniffNotebook(gtk.Notebook):
    def create_session(self, iface, args):
        page = SniffPage(Backend.SniffContext(iface, **args))
        page.show()

        self.append_page(page)

    def load_session(self, fname):
        """
        Load a session from pcap files

        @param fname the pcap file path
        """

        page = SniffPage(Backend.SniffContext(iface=None, capfile=fname))
        page.show()
        
        self.append_page(page)

if __name__ == "__main__":
    w = gtk.Window()
    w.add(SniffFilter())
    w.show_all()
    gtk.main()
