import logging
from concurrent.futures import Future

from gi.repository import GObject

from proton.vpn.app.gtk.controller import Controller

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

logger = logging.getLogger(__name__)


class VPNWidget(Gtk.Grid):
    """Exposes the ProtonVPN product functionality to the user."""
    def __init__(self, controller: Controller):
        super().__init__(row_spacing=10, column_spacing=10)
        self._controller = controller

        self.set_column_homogeneous(True)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        self._logout_button = Gtk.Button(label="Logout")
        self._logout_button.connect("clicked", self._on_logout_button_clicked)
        self.add(self._logout_button)
        self._connect_button = Gtk.Button(label="Connect")
        self._connect_button.connect(
            "clicked", self._on_connect_button_clicked)
        self.add(self._connect_button)
        self._disconnect_button = Gtk.Button(label="Disconnect")
        self._disconnect_button.connect(
            "clicked", self._on_disconnect_button_clicked)
        self.add(self._disconnect_button)
        self._main_spinner = Gtk.Spinner()
        self.add(self._main_spinner)

    @GObject.Signal(name="user-logged-out")
    def user_logged_out(self):
        pass

    def _on_logout_button_clicked(self, _):
        logger.info("Disconnecting...")
        self._main_spinner.start()
        future = self._controller.logout()
        future.add_done_callback(self._on_logout_result)

    def _on_logout_result(self, future: Future):
        try:
            future.result()
        except Exception:
            logger.exception("Error during logout.")
            return
        finally:
            self._main_spinner.stop()

        logger.info("User logged out.")
        self.emit("user-logged-out")

    def _on_connect_button_clicked(self, _):
        logger.info("Connecting...")
        self._main_spinner.start()
        future = self._controller.connect()
        future.add_done_callback(self._on_connect_result)

    def _on_connect_result(self, future: Future):
        try:
            future.result()
        except Exception:
            logger.exception("Error during connect.")
            return
        finally:
            self._main_spinner.stop()
        logger.info("Connected.")

    def _on_disconnect_button_clicked(self, _):
        logger.info("Disconnecting...")
        self._main_spinner.start()
        future = self._controller.disconnect()
        future.add_done_callback(self._on_disconnect_result)

    def _on_disconnect_result(self, future: Future):
        try:
            future.result()
        except Exception:
            logger.exception("Error during disconnect.")
            return
        finally:
            self._main_spinner.stop()
        logger.info("Disconnected.")
