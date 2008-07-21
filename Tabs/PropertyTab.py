import gtk
from widgets.PropertyGrid import PropertyGrid
from views import UmitView

class PropertyTab(UmitView):
    label_text = "Properties"

    def create_ui(self):
        self.grid = PropertyGrid()
        self._main_widget.add(self.grid)
        self._main_widget.show_all()
