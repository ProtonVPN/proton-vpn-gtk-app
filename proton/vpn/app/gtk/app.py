from concurrent.futures import ThreadPoolExecutor

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.view import MainWindow


class App(Gtk.Application):
    """
    Proton VPN GTK application.

    It inherits a set of common app functionality from Gtk.Application:
    https://docs.gtk.org/gtk3/class.Application.html.

    For example:
     - It guarantees that only one instance of the application is
       allowed (new app instances exit immediately if there is already
       an instance running).
     - It manages the windows associated to the application. The application
       exits automatically when the last one is closed.
     - It allows desktop shell integration by exporting actions and menus.
    """

    def __init__(self, thread_pool_executor: ThreadPoolExecutor):
        super().__init__(application_id="proton.vpn.app.gtk")
        self._controller = Controller(
            thread_pool_executor=thread_pool_executor
        )
        self.window = None

    def do_activate(self):
        """
        Method called by Gtk.Application when the default first window should
        be shown to the user.
        """
        if not self.window:
            self.window = MainWindow(self._controller)
            # Windows are associated with the application like this.
            # When the last one is closed, the application shuts down.
            self.add_window(self.window)

        self.window.show_all()
        self.window.present()

        if self._controller.display_login:
            self.window.display_login_widget()
        else:
            self.window.display_vpn_widget()
