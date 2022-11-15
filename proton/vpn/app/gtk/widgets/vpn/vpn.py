"""
This module defines the VPN widget, which contains all the VPN functionality
that is shown to the user.
"""
# pylint: disable=R0801
from concurrent.futures import Future

from gi.repository import GObject, GLib

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.vpn.quick_connect import QuickConnectWidget
from proton.vpn.app.gtk.widgets.vpn.server_list import ServerListWidget
from proton.vpn.connection.enum import ConnectionStateEnum, StateMachineEventEnum
from proton.vpn.connection.states import Disconnected, Connected
from proton.vpn.core_api.exceptions import VPNConnectionFoundAtLogout
from proton.vpn import logging

from proton.vpn.app.gtk.widgets.vpn.status import VPNConnectionStatusWidget

logger = logging.getLogger(__name__)


class VPNWidget(Gtk.Box):  # pylint: disable=R0902
    """Exposes the ProtonVPN product functionality to the user."""

    def __init__(self, controller: Controller):
        super().__init__(spacing=10)
        self._controller = controller
        # Flag signaling when a logout is required after VPN disconnection.
        self._logout_after_vpn_disconnection = False

        self.set_orientation(Gtk.Orientation.VERTICAL)

        self._connection_status_widget = VPNConnectionStatusWidget(controller)
        self.pack_start(self._connection_status_widget, expand=False, fill=False, padding=0)

        self._logout_dialog = None
        self._logout_button = Gtk.Button(label="Logout")
        self._logout_button.connect("clicked", self._on_logout_button_clicked)
        self.pack_start(self._logout_button, expand=False, fill=False, padding=0)

        self._quick_connect_widget = QuickConnectWidget(controller)
        self.pack_start(self._quick_connect_widget, expand=False, fill=False, padding=0)

        self.servers_widget = ServerListWidget(controller)
        self.pack_end(self.servers_widget, expand=True, fill=True, padding=0)

        # Keep track of child widgets that need to be aware of VPN connection status changes.
        self._connection_update_subscribers = []
        for widget in [
            self._connection_status_widget,
            self._quick_connect_widget,
            self.servers_widget
        ]:
            self._connection_update_subscribers.append(widget)

        self.connect("realize", self._on_realize)
        self.connect("unrealize", self._on_unrealize)

    @GObject.Signal(name="user-logged-out")
    def user_logged_out(self):
        """Signal emitted once the user has been logged out."""

    def _on_realize(self, _servers_widget: ServerListWidget):
        self._initialize_ui()
        self._controller.register_connection_status_subscriber(self)

    def _initialize_ui(self):
        if self._controller.current_connection:
            self.status_update(Connected())
        else:
            self.status_update(Disconnected())

    def _on_unrealize(self, _servers_widget: ServerListWidget):
        if self._controller.is_connection_active:
            self._controller.disconnect()
            self._controller.unregister_connection_status_subscriber(self)

    def status_update(self, connection_status):
        """This method is called whenever the VPN connection status changes."""
        logger.debug(
            f"VPN widget received connection status update: "
            f"{connection_status.state.name}."
        )

        def update_widget():
            for widget in self._connection_update_subscribers:
                widget.connection_status_update(connection_status)

            if connection_status.state == ConnectionStateEnum.DISCONNECTED \
                    and self._logout_after_vpn_disconnection:
                self._logout_button.clicked()
                self._logout_after_vpn_disconnection = False
            elif connection_status.state == ConnectionStateEnum.ERROR:
                title = "VPN Connection Error"
                message = "Unable to establish VPN Connection"

                if connection_status.context.event.event == StateMachineEventEnum.AUTH_DENIED:
                    title = f"{title}: Authentication Denied"
                    message = "Unable to establish VPN due to " \
                        "wrong authentication credentials"

                self.emit(
                    "vpn-connection-error",
                    title,
                    message
                )

        GLib.idle_add(update_widget)

    @GObject.Signal(name="vpn-connection-error", arg_types=(str, str))
    def vpn_connection_error(self, title: str, text: str):
        """Signal emitted when a connection error occurred."""

    def _on_logout_button_clicked(self, *_):
        logger.info("Logout button clicked", category="UI", subcategory="LOGOUT", event="CLICK")
        future = self._controller.logout()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_logout_result, future)
        )

    def _on_logout_result(self, future: Future):
        try:
            future.result()
            logger.info("Successful logout", category="APP", subcategory="LOGOUT", event="SUCCESS")
            self.emit("user-logged-out")
        except VPNConnectionFoundAtLogout:
            self._show_disconnect_dialog()

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
        self._logout_dialog.get_content_area().add(label)
        self._logout_dialog.show_all()

    def _on_show_disconnect_response(self, _dialog, response):
        if response == Gtk.ResponseType.YES:
            logger.info("Yes", category="UI", subcategory="DIALOG", event="DISCONNECT")
            self._logout_after_vpn_disconnection = True
            self._quick_connect_widget.disconnect_button_click()
        else:
            logger.info("No", category="UI", subcategory="DIALOG", event="DISCONNECT")

        self._logout_dialog.destroy()
        self._logout_dialog = None

    def logout_button_click(self):
        """Clicks the logout button.
        This method was made available mainly for testing purposes."""
        self._logout_button.clicked()

    def close_dialog(self, end_current_connection):
        """Closes the logout dialog.
        This property was made available mainly for testing purposes."""
        self._logout_dialog.emit(
            "response",
            Gtk.ResponseType.YES if end_current_connection else Gtk.ResponseType.NO)
