 import gtk

try:
    from paned import *
except ImportError:
    print "moo not installed. Using fallback UmitPaned .."
    from fallbackpaned import *

from Tabs.VteTab import VteTab
from Tabs.MainTab import MainTab
from Tabs.ConsoleTab import ConsoleTab
from Tabs.PropertyTab import PropertyTab
from Tabs.ProtocolSelectorTab import ProtocolSelectorTab

from umitCore.I18N import _
from umitCore.Paths import Path

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

        self.main_actions = [
            ('File', None, _('_File'), None),
            ('Import', gtk.STOCK_CONVERT, _('_Import'), None),
        ]

        self.default_ui = """<menubar>
            <menu action='File'>
                <menuitem action='Import'/>
            </menu>
            </menubar>

            <toolbar>
            <toolitem action='Import'/>
            </toolbar>
            """

        self.ui_manager = gtk.UIManager()

        self.main_accel_group = gtk.AccelGroup()
        self.main_action_group = gtk.ActionGroup('MainActionGroup')
        self.main_action_group.add_actions(self.main_actions)
        
        self.add_accel_group(self.main_accel_group)

        for action in self.main_action_group.list_actions():
            action.set_accel_group(self.main_accel_group)
            action.connect_accelerator()

        self.ui_manager.insert_action_group(self.main_action_group, 0)
        self.ui_manager.add_ui_from_string(self.default_ui)

        # Central widgets
        self.main_paned = UmitPaned()
        self.main_tab = MainTab()

        # Tabs
        self.vte_tab = VteTab()
        self.protocols_tab = ProtocolSelectorTab()
        self.property_tab = PropertyTab()
        self.console_tab = ConsoleTab()
        
        self.vbox = gtk.VBox(False, 2)

    def __pack_widgets(self):
        "Pack widgets"

        self.menubar = self.ui_manager.get_widget("/menubar")
        self.vbox.pack_start(self.menubar, False, False, 0)

        self.toolbar = self.ui_manager.get_widget("/toolbar")
        self.vbox.pack_start(self.toolbar, False, False, 0)
        
        self.vbox.pack_start(self.main_paned)

        self.main_paned.add_view(PANE_CENTER, self.main_tab, False)

        self.main_paned.add_view(PANE_LEFT, self.protocols_tab, False)
        self.main_paned.add_view(PANE_RIGHT, self.property_tab, False)

        self.main_paned.add_view(PANE_BOTTOM, self.vte_tab, False)
        self.main_paned.add_view(PANE_BOTTOM, self.console_tab, False)

        self.add(self.vbox)

    def __connect_signals(self):
        "Connect signals"
        self.connect('delete-event', lambda *w: gtk.main_quit())
    
    def run(self):
        gtk.main()

if __name__ == "__main__":
    app = MainWindow()
    app.run()
