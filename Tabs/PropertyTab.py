import gtk
from views import UmitView
from widgets.PropertyGrid import PropertyGrid
from Tabs.MainTab import SessionPage

class PropertyTab(UmitView):
    label_text = "Properties"
    icon_name = gtk.STOCK_INDEX

    def create_ui(self):
        self.grid = PropertyGrid()
        self._main_widget.add(self.grid)
        self._main_widget.show_all()

        # Start disabled
        self._main_widget.set_sensitive(False)

    def connect_tab_signals(self):
        # I need to connect the session-notebook
        # signals from main tab here so we have
        # overriden this method to avoid errors

        from App import PMApp
        tab = PMApp().main_window.main_tab
        tab.session_notebook.connect('switch-page', self.__on_repopulate)

    def __on_repopulate(self, sess_nb, page, num):
        page = sess_nb.get_nth_page(num)

        self._main_widget.set_sensitive(False)
        self.grid.clear()

        if isinstance(page, SessionPage):
            # We need to get the protocol instance
            # so we can repopulate the PropertyGrid

            self.grid.populate(page.protocol)
            self._main_widget.set_sensitive(True)
