import gtk

class Page(gtk.VBox):
    def __init__(self):
        super(Page, self).__init__(False, 4)
        self.set_border_width(4)
        self.create_ui()
        self.show_all()

    def create_ui(self):
        pass

class GUIPage(Page):
    def create_ui(self):
        self.pack_start(gtk.CheckButton("Use docking windows"), False, False)

class PreferenceDialog(gtk.Dialog):
    def __init__(self, parent):
        super(PreferenceDialog, self).__init__(
            "Preferences - PacketManipulator", parent,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_REJECT,
             gtk.STOCK_APPLY, gtk.RESPONSE_ACCEPT)
        )

        self.store = gtk.ListStore(str)
        self.tree = gtk.TreeView(self.store)

        self.tree.append_column(
            gtk.TreeViewColumn('', gtk.CellRendererText(), text=0))
        self.tree.set_headers_visible(False)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.tree)

        hbox = gtk.HBox()
        hbox.pack_start(sw, False, False)

        self.notebook = gtk.Notebook()
        self.notebook.set_show_border(False)
        self.notebook.set_show_tabs(False)
        hbox.pack_end(self.notebook)

        self.__populate()

        hbox.show_all()
        self.vbox.pack_start(hbox)
        self.vbox.set_border_width(4)
        self.vbox.set_spacing(4)

    def __populate(self):
        self.store.append(["GUI"])
        self.notebook.append_page(GUIPage())

if __name__ == "__main__":
    d = PreferenceDialog(None)
    d.show()
    gtk.main()
