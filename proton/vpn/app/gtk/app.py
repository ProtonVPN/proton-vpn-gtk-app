import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from gi.repository import GObject

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
        self._signal_connect_queue = []

    def do_activate(self):
        """
        Method called by Gtk.Application when the default first window should
        be shown to the user.
        """
        if not self.window:
            self.window = MainWindow(self._controller)
            # Process signal connection requests asap.
            self._process_signal_connect_queue()
            # Disable exception handler as soon as the main window is closed.
            self.connect("window-removed", lambda *_: self.exception_handler.disable())
            # Windows are associated with the application like this.
            # When the last one is closed, the application shuts down.
            self.add_window(self.window)
            self.exception_handler.enable()

        self.window.show_all()
        self.window.present()
        self.emit("app-ready")

    @property
    def error_dialogs(self):
        return self.exception_handler.error_dialogs

    @GObject.Signal(name="app-ready")
    def app_ready(self):
        """Signal emitted when the app is ready for interaction."""
        pass

    def queue_signal_connect(self, signal_spec: str, callback: Callable):
        """Queues a request to connect a callback to a signal.

        This method should only be used by tests that need to connect a
        callback to a widget signal before the app window, which contains
        all app widgets, has been created.

        Note that the window is not created in the Gtk.Application constructor
        but when the app receives the ``activate`` signal. Fore more info:
        https://wiki.gnome.org/HowDoI/GtkApplication

        While testing, we might want to use this method to make sure that we
        are able to connect our callback **before** the signal has already
        fired. This method allows the app to queue a
        request to connect a callback to one of the widgets' signals. The queued
        request will be processed as soon as the app window (with all its
        children widgets) have been created.

        Usage example:
        .. code-block:: python
            with ThreadPoolExecutor() as thread_pool_executor:
                app = App(thread_pool_executor)
                app.queue_signal_connect(
                    signal_spec="main_widget.vpn_widget.servers_widget::server-list-ready",
                    callback=my_func
                )
                sys.exit(app.run(sys.argv))

        The widget/signal the callback should be connected to is specified
        with the ``signal_spec`` parameter, which should have the following
        form: ``widget_attr.[widget_attr.]::signal-name``.

        ``widget_attr`` refers to a widget attribute from the app window
        which, in turn, can contain other widget attributes. The ``signal-name``
        after the double colon is the name of the signal to attach the callback
        to.

        So in the example above, the resulting action once the app window is
        created will be to run the following code:

        .. code-block:: python
            app.window.main_widget.vpn_widget.servers.connect(
                "server-list-ready", my_func
            )

        :param signal_spec: signal specification.
        :param callback: Callback to connect to the specified signal.
        """
        self._signal_connect_queue.append((signal_spec, callback))
        if self.window:
            # if the window already exist then the queue is processed instantly
            self._process_queued_signal_callbacks()

    def _process_signal_connect_queue(self):
        """Processes all signal connection requests queued by calling
        `queue_signal_connect`"""
        for _ in range(len(self._signal_connect_queue)):
            signal_spec, callback = self._signal_connect_queue.pop(0)
            widget_path, signal_name = signal_spec.split("::")
            obj = self.window
            for widget_path_segment in widget_path.split("."):
                obj = getattr(obj, widget_path_segment)

            assert isinstance(obj, GObject.Object), \
                f"{type(obj)} does not inherit from GObject.Object."
            obj.connect(signal_name, callback)


class AppExceptionHandler:
    """Handles exceptions before they bubble all the way up."""

    def __init__(self, application_window: Gtk.ApplicationWindow = None):
        self._application_window = application_window
        self.error_dialogs = []
        self._previous_sys_excepthook = sys.excepthook
        self._previous_threading_excepthook = threading.excepthook

    def enable(self):
        self._previous_sys_excepthook = sys.excepthook
        # Handle exceptions bubbling up in the main thread.
        sys.excepthook = self.handle_errors

        self._previous_threading_excepthook = threading.excepthook
        # Handle exceptions bubbling up in threads started with Thread.run().
        # Notice that an exception raised from a thread managed by a
        # ThreadPoolExecutor won't bubble up, as the executor won't allow it.
        # In this case, make sure that you call Future.result() on the future
        # returned by ThreadPoolExecutor.submit() in the main thread
        # (e.g. using GLib.idle_add())
        threading.excepthook = lambda args: self.handle_errors(
            args.exc_type, args.exc_value, args.exc_traceback
        )

    def disable(self):
        sys.excepthook = self._previous_sys_excepthook
        threading.excepthook = self._previous_threading_excepthook

    def handle_errors(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, ProtonAPINotReachable):
            error_message = "Our servers are not reachable. " \
                            "Please check your internet connection."
        elif isinstance(exc_value, ProtonAPIError) and exc_value.error:
            error_message = exc_value.error
        elif isinstance(exc_value, AssertionError):
            # We shouldn't catch assertion errors raised by tests.
            raise exc_value
        elif issubclass(exc_type, Exception):
            error_message = "We're sorry, an unexpected error occurred. " \
                            "Please try later."
        else:
            raise exc_value if exc_value else exc_type

        logger.error(
            "Unexpected error.",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        self._show_error_dialog(error_message)

    def _show_error_dialog(
            self, secondary_text, primary_text="Something went wrong"
    ):
        error_dialog = Gtk.MessageDialog(
            transient_for=self._application_window,
            flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=primary_text,
        )
        self.error_dialogs.append(error_dialog)
        error_dialog.format_secondary_text(secondary_text)
        error_dialog.run()
        error_dialog.destroy()
        self.error_dialogs.remove(error_dialog)
