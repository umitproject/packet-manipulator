import gtk
import gobject
import Backend

from umitCore.I18N import _

class SniffTree(gtk.ScrolledWindow):
    def __init__(self, context):
        super(SniffTree, self).__init__()
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self.store = gtk.ListStore(int, str, str, str, str, str, object)
        self.tree = gtk.TreeView(self.store)

        idx = 0
        for txt in (_('No.'), _('Time'), _('Source'), \
                    _('Destination'), _('Protocol'), _('Info')):

            col = gtk.TreeViewColumn(txt, gtk.CellRendererText(), text=idx)
            self.tree.append_column(col)
            idx += 1

        self.add(self.tree)

        self.context = context
        self.context.start()

        #gobject.idle_add(self.__update_tree)
        gobject.timeout_add(200, self.__update_tree)

    def __update_tree(self):
        for packet in self.context.get_data():
            print packet
            self.store.append(
                [
                 len(self.store) + 1, packet.get_time(), packet.get_source(),
                 packet.get_dest(), packet.get_protocol_str(), packet.summary(), packet
                ]
            )

        return self.context.isAlive()

class SniffFilter(gtk.HBox):
    pass


class SniffTab:
    pass

class SniffNotebook(gtk.Notebook):
    def create_session(self, iface):
        self.append_page(SniffTree(Backend.SniffContext(iface)))

if __name__ == "__main__":
    w = gtk.Window()
    w.add(SniffTree(SniffContext("wlan0")))
    w.show_all()
    gtk.main()
