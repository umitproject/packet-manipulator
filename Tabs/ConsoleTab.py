import gtk

from console import Console
from views import UmitView

class ConsoleTab(UmitView):
    label_text = "Packet Shell"

    def __create_widgets(self):
        self.console = Console()
        self.console.banner()

    def __pack_widgets(self):
        self._main_widget.add(self.console)
        self._main_widget.show_all()

    def create_ui(self):
        self.__create_widgets()
        self.__pack_widgets()