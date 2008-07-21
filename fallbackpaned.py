import gtk

PANE_CENTER = 'Center'
PANE_RIGHT = 'Rigth'
PANE_LEFT = 'Left'
PANE_TOP = 'Top'
PANE_BOTTOM = 'Bottom'

class UmitPaned(gtk.VBox):
    """Fallback UmitPaned based on gtk.Paned
    """

    def __init__(self):
        super(UmitPaned, self).__init__(2, False)

        self.hpaned = gtk.HPaned()
        self.vpaned = gtk.VPaned()

        self.hnotebook = gtk.Notebook()
        self.vnotebook = gtk.Notebook()
        
        self.vnotebook.set_tab_pos(gtk.POS_BOTTOM)

        self.pack_start(self.vpaned)
        self.vpaned.add2(self.vnotebook) # bottom
        
        self.vpaned.add1(self.hpaned)
        self.hpaned.add1(self.hnotebook) # left
        
        self.show_all()

    def add_view(self, pos, tab, unused=False):
        widget = tab.get_toplevel()

        if pos == PANE_CENTER:
            if not self.hpaned.get_child2():
                self.hpaned.add2(widget)
                return

        label = gtk.HBox()

        image = gtk.image_new_from_stock(tab.icon_name, gtk.ICON_SIZE_MENU)

        label.pack_start(image, False, False)
        label.pack_start(gtk.Label(tab.label_text))
        label.show_all()

        print "Adding widget", widget, "to", pos

        if pos == PANE_RIGHT or pos == PANE_LEFT:
            self.hnotebook.append_page(widget, label)
        elif pos == PANE_TOP or pos == PANE_BOTTOM:
            self.vnotebook.append_page(widget, label)

if __name__ == "__main__":
    w = gtk.Window()
    p = UmitPaned()
    p.add_view("Top", gtk.Label("miao"))
    p.add_view("Center", gtk.Label("Center"))
    p.add_view("Right", gtk.Label("miao"))
    w.add(p)
    w.show_all()
    gtk.main()
