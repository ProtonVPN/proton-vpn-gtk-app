from concurrent.futures import ThreadPoolExecutor

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.view import MainWindow


class App(Gtk.Application):
    """
    Application entry point.

    It inherits a set of common app functionality from Gtk.Application.
    For example, only one instance of the application is allowed.
    """

    def __init__(self, thread_pool_executor: ThreadPoolExecutor):
        super().__init__(application_id="proton.vpn.app.gtk")
        self._controller = Controller(
            thread_pool_executor=thread_pool_executor
        )
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = MainWindow(self._controller)
            # Windows are associated with the application like this.
            # When the last one is closed, the application shuts down.
            self.add_window(self.window)

        self.window.show_all()
