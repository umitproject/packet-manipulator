import gtk
import gobject
import Backend

from higwidgets.higanimates import HIGAnimatedBar
from umitCore.I18N import _

class SniffPage(gtk.VBox):
    def __init__(self, context):
        super(SniffPage, self).__init__(False, 2)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.store = gtk.ListStore(int, str, str, str, str, str, object)
        self.tree = gtk.TreeView(self.store)

        idx = 0
        for txt in (_('No.'), _('Time'), _('Source'), \
                    _('Destination'), _('Protocol'), _('Info')):

            col = gtk.TreeViewColumn(txt, gtk.CellRendererText(), text=idx)
            self.tree.append_column(col)
            idx += 1

        sw.add(self.tree)

        self.statusbar = HIGAnimatedBar(_('Sniffing on <tt>%s</tt> ...') % context.iface, gtk.STOCK_INFO)

        self.pack_start(sw)
        self.pack_start(self.statusbar, False, False)

        self.show_all()

        self.context = context
        self.context.start()

        self.timeout_id = gobject.timeout_add(200, self.__update_tree)

    def __update_tree(self):
        for packet in self.context.get_data():
            id = len(self.store) + 1

            self.store.append(
                [
                 id, packet.get_time(), packet.get_source(),
                 packet.get_dest(), packet.get_protocol_str(), packet.summary(), packet
                ]
            )

            # Scroll to end
            if self.context.auto_scroll:
                self.tree.scroll_to_cell(id - 1)

        if self.context.exception:
            self.statusbar.label = "<b>%s</b>" % self.context.exception
            self.statusbar.image = gtk.STOCK_DIALOG_ERROR
            self.statusbar.start_animation(True)

        return self.context.is_alive()

    def stop_sniffing(self):
        if self.context:
            self.context.destroy()

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
