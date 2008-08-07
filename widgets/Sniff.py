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
        super(SniffPage, self).__init__(False, 2)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.store = gtk.ListStore(int, str, str, str, str, str, gtk.gdk.Color, object)
        self.tree = gtk.TreeView(self.store)

        idx = 0
        for txt in (_('No.'), _('Time'), _('Source'), \
                    _('Destination'), _('Protocol'), _('Info')):

            rend = SniffRenderer()
            col = gtk.TreeViewColumn(txt, rend, text=idx, cell_background_gdk=6)
            self.tree.append_column(col)
            idx += 1

        sw.add(self.tree)

        self.statusbar = HIGAnimatedBar(_('Sniffing on <tt>%s</tt> ...') % context.iface, gtk.STOCK_INFO)

        self.pack_start(sw)
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
                self.tree.scroll_to_cell(id - 1)

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

class SniffFilter(gtk.HBox):
    pass


class SniffTab:
    pass

class SniffNotebook(gtk.Notebook):
    def create_session(self, iface, args):
        page = SniffPage(Backend.SniffContext(iface, **args))
        page.show()

        self.append_page(page)

if __name__ == "__main__":
    w = gtk.Window()
    w.add(SniffTree(SniffContext("wlan0")))
    w.show_all()
    gtk.main()
