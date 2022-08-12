import logging
from concurrent.futures import Future

from gi.repository import GObject, GLib

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn.core_api.exceptions import VPNConnectionFoundAtLogout


logger = logging.getLogger(__name__)


class VPNWidget(Gtk.Grid):
    """Exposes the ProtonVPN product functionality to the user."""
    def __init__(self, controller: Controller):
        super().__init__(row_spacing=10, column_spacing=10)
        self._controller = controller

        self.set_column_homogeneous(True)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        self._logout_dialog = None
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
        self.__vpn_disconnected_signal_id = None

    @GObject.Signal(name="user-logged-out")
    def user_logged_out(self):
        pass

    @GObject.Signal(name="vpn-disconnected")
    def vpn_disconnected(self):
        pass

    def _on_logout_button_clicked(self, *_):
        logger.info("Logging out...")
        self._main_spinner.start()
        future = self._controller.logout()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_logout_result, future)
        )

    def _on_logout_result(self, future: Future):
        try:
            future.result()
            logger.info("User logged out.")
            self.emit("user-logged-out")
        except VPNConnectionFoundAtLogout:
            self._main_spinner.start()
            self._show_disconnect_dialog()
        finally:
            self._main_spinner.stop()

    def _on_connect_button_clicked(self, _):
        logger.info("Connecting...")
        self._main_spinner.start()
        future = self._controller.connect()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_connect_result, future)
        )

    def _on_connect_result(self, future: Future):
        try:
            future.result()
        finally:
            self._main_spinner.stop()
        logger.info("Connected.")

    def _on_disconnect_button_clicked(self, _):
        logger.info("Disconnecting...")
        self._main_spinner.start()
        future = self._controller.disconnect()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_disconnect_result, future)
        )

    def _on_disconnect_result(self, future: Future):
        try:
            future.result()
            self.emit("vpn-disconnected")
        finally:
            self._main_spinner.stop()
        logger.info("Disconnected.")

    def _show_disconnect_dialog(self):
        self._logout_dialog = Gtk.Dialog()
        self._logout_dialog.set_title("Active connection found")
        self._logout_dialog.set_default_size(500, 200)
        self._logout_dialog.add_button("_Yes", Gtk.ResponseType.YES)
        self._logout_dialog.add_button("_No", Gtk.ResponseType.NO)
        self._logout_dialog.connect("response", self._on_show_disconnect_response)
        label = Gtk.Label(
            label="Logging out of the application will disconnect the active"
                  " vpn connection.\n\nDo you want to continue ?"
        )
        self._logout_dialog.vbox.add(label)
        self._logout_dialog.show_all()

    def _on_show_disconnect_response(self, dialog, response):
        if response == Gtk.ResponseType.YES:
            def disconnect_before_logout(_):
                GObject.signal_handler_disconnect(self, self.__vpn_disconnected_signal_id)
                self.__vpn_disconnected_signal_id = None
                self._logout_button.clicked()

            self.__vpn_disconnected_signal_id = self.connect("vpn-disconnected", disconnect_before_logout)
            self._disconnect_button.clicked()

        self._logout_dialog.destroy()
        self._logout_dialog = None

    def logout_button_click(self):
        """Simulates logout button click.
        This property was made available mainly for testing purposes."""
        self._logout_button.clicked()

    def close_dialog(self, end_current_connection):
        """Simulates interaction with logout dialog.
        This property was made available mainly for testing purposes."""
        self._logout_dialog.emit(
            "response",
            Gtk.ResponseType.YES if end_current_connection else Gtk.ResponseType.NO)
