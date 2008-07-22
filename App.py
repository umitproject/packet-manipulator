from Icons import register_icons
from MainWindow import MainWindow

class Singleton(object):
    """
    A class for singleton pattern
    Support also gobject if Singleton base subclass if specified first
    """

    instances = {}
    def __new__(cls, *args, **kwargs): 
        from gobject import GObject

        if Singleton.instances.get(cls) is None:
            cls.__original_init__ = cls.__init__
            if issubclass(cls, GObject):
                Singleton.instances[cls] = GObject.__new__(cls)
            else:
                Singleton.instances[cls] = object.__new__(cls, *args, **kwargs)
        elif cls.__init__ == cls.__original_init__:
            def nothing(*args, **kwargs):
                pass
            cls.__init__ = nothing
        return Singleton.instances[cls]

class PMApp(Singleton):
    def __init__(self):
        register_icons()

        self.main_window = MainWindow()
        self.main_window.connect_tabs_signals()

    def run(self):
        from gtk import main
        main()
