import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

from proton.session.exceptions import ProtonAPINotReachable, ProtonAPIError

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.view import MainWindow

logger = logging.getLogger(__name__)


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
        self.exception_handler = AppExceptionHandler()

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
            self.exception_handler._application_window = self.window

        self.window.show_all()
        self.window.present()

    @property
    def error_dialog(self):
        return self.exception_handler.error_dialog


class AppExceptionHandler:
    """Handles exceptions before they bubble all the way up."""

    def __init__(self, application_window: Gtk.ApplicationWindow = None):
        self._application_window = application_window
        self.error_dialog = None

        # Handle exceptions bubbling up in the main thread.
        sys.excepthook = self.handle_errors

        # Handle exceptions bubbling up in threads started with Thread.run().
        # Notice that an exception raised from a thread managed by a
        # ThreadPoolExecutor won't bubble up, as the executor won't allow it.
        # In this case, make sure that you call Future.result() on the future
        # returned by ThreadPoolExecutor.submit() in the main thread
        # (e.g. using GLib.idle_add())
        threading.excepthook = lambda args: self.handle_errors(args.exc_type, args.exc_value, args.exc_traceback)

    def handle_errors(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, ProtonAPINotReachable):
            error_message = "Our servers are not reachable. Please check your internet connection."
        elif isinstance(exc_value, ProtonAPIError) and exc_value.error:
            error_message = exc_value.error
        elif issubclass(exc_type, Exception):
            error_message = "We're sorry, an unexpected error occurred. " \
                            "Please try later."
        else:
            raise exc_value if exc_value else exc_type

        logger.error("Unexpected error.", exc_info=(exc_type, exc_value, exc_traceback))
        self._show_error_dialog(error_message)

    def _show_error_dialog(self, secondary_text, primary_text="Something went wrong"):
        self.error_dialog = Gtk.MessageDialog(
            transient_for=self._application_window,
            flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=primary_text,
        )
        self.error_dialog.format_secondary_text(secondary_text)
        self.error_dialog.run()
        self.error_dialog.destroy()
        self.error_dialog = None
