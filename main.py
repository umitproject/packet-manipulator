import gtk

try:
    from paned import *
except ImportError:
    print "moo not installed. Using fallback UmitPaned .."
    from fallbackpaned import *

from Tabs.VteTab import VteTab
from Tabs.MainTab import MainTab
from Tabs.ConsoleTab import ConsoleTab
from Tabs.ProtocolSelectorTab import ProtocolSelectorTab

class MainWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_title("Packet Manipulator")
        self.set_size_request(600, 400)

        self.__create_widgets()
        self.__pack_widgets()
        self.__connect_signals()

        self.show_all()

    def __create_widgets(self):
        "Create widgets"

        # Central widgets
        self.main_paned = UmitPaned()
        self.main_tab = MainTab()

        # Tabs
        self.vte_tab = VteTab()
        self.protocols_tab = ProtocolSelectorTab()
        self.console_tab = ConsoleTab()

    def __pack_widgets(self):
        "Pack widgets"
        self.add(self.main_paned)

        self.main_paned.add_view(PANE_CENTER, self.main_tab, False)

        self.main_paned.add_view(PANE_LEFT, self.protocols_tab, False)
        self.main_paned.add_view(PANE_BOTTOM, self.vte_tab, False)
        self.main_paned.add_view(PANE_BOTTOM, self.console_tab, False)

    def __connect_signals(self):
        "Connect signals"
        self.connect('delete-event', lambda *w: gtk.main_quit())

if __name__ == "__main__":
    MainWindow()
    gtk.main()
