"""
This module defines the VPN widget, which contains all the VPN functionality
that is shown to the user.
"""
from concurrent.futures import Future
from dataclasses import dataclass

from gi.repository import GObject, GLib

from proton.vpn import logging

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.services import VPNDataRefresher
from proton.vpn.app.gtk.widgets.vpn.quick_connect import QuickConnectWidget
from proton.vpn.app.gtk.widgets.vpn.server_list import ServerListWidget
from proton.vpn.app.gtk.widgets.vpn.status import VPNConnectionStatusWidget
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.core_api.exceptions import VPNConnectionFoundAtLogout
from proton.vpn.core_api.client_config import ClientConfig
from proton.vpn.servers.list import ServerList

logger = logging.getLogger(__name__)


@dataclass
class VPNWidgetState:
    """
    Holds the state of the VPNWidget. This state is reset after login/logout.

    Attributes:
        is_widget_ready: flag set to True once the widget has been initialized.
        user_tier: tier of the logged-in user.
        vpn_data_ready_handler_id: handler id obtained when connecting to the
        vpn-data-ready signal on VPNDataRefresher.
        logout_after_vpn_disconnection: flag signaling when a logout is required
        after VPN disconnection.
        logout_dialog: confirmation dialog shown to the user when logout is
        requested while being connected to the VPN.
    """
    is_widget_ready: bool = False
    user_tier: int = None
    vpn_data_ready_handler_id: int = None
    logout_after_vpn_disconnection: bool = False
    logout_dialog: Gtk.Dialog = None


class VPNWidget(Gtk.Box):
    """Exposes the ProtonVPN product functionality to the user."""

    def __init__(self, controller: Controller):
        super().__init__(spacing=10)
        self._state = VPNWidgetState()

        self._controller = controller

        self.connection_status_widget = VPNConnectionStatusWidget()
        self.pack_start(self.connection_status_widget, expand=False, fill=False, padding=0)

        self.logout_button = Gtk.Button(label="Logout")
        self.logout_button.connect("clicked", self._on_logout_button_clicked)
        self.pack_start(self.logout_button, expand=False, fill=False, padding=0)

        self.quick_connect_widget = QuickConnectWidget(self._controller)
        self.pack_start(self.quick_connect_widget, expand=False, fill=False, padding=0)

        self.server_list_widget = ServerListWidget(self._controller)
        self.pack_end(self.server_list_widget, expand=True, fill=True, padding=0)

        self.connection_status_subscribers = []
        for widget in [
            self.connection_status_widget,
            self.quick_connect_widget,
            self.server_list_widget
        ]:
            self.connection_status_subscribers.append(widget)

        self.set_orientation(Gtk.Orientation.VERTICAL)

        self.connect("unrealize", self._on_unrealize)

    @GObject.Signal
    def vpn_widget_ready(self):
        """Signal emitted when all resources were loaded and widget is ready."""

    @GObject.Signal
    def user_logged_out(self):
        """Signal emitted once the user has been logged out."""

    @property
    def user_tier(self) -> int:
        """Returns the tier of the user currently logged in."""
        return self._state.user_tier

    def _on_unrealize(self, _widget):
        self.unload()

    def status_update(self, connection_status):
        """This method is called whenever the VPN connection status changes."""
        logger.debug(
            f"VPN widget received connection status update: "
            f"{connection_status.state.name}."
        )

        def update_widget():
            for widget in self.connection_status_subscribers:
                widget.connection_status_update(connection_status)

            if connection_status.state == ConnectionStateEnum.DISCONNECTED \
                    and self._state.logout_after_vpn_disconnection:
                self.logout_button.clicked()
                self._state.logout_after_vpn_disconnection = False

        GLib.idle_add(update_widget)

    def _on_logout_button_clicked(self, *_):
        logger.info("Logout button clicked", category="UI", subcategory="LOGOUT", event="CLICK")
        future = self._controller.logout()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_logout_result, future)
        )

    def _show_disconnect_dialog(self):
        """Displays the disconnect dialog.

        This method is called when the user attempts to logout while there is still
        an active VPN connection.
        """
        logout_dialog = Gtk.Dialog()
        logout_dialog.set_title("Active connection found")
        logout_dialog.set_default_size(500, 200)
        logout_dialog.add_button("_Yes", Gtk.ResponseType.YES)
        logout_dialog.add_button("_No", Gtk.ResponseType.NO)
        logout_dialog.connect("response", self._on_show_disconnect_response)
        label = Gtk.Label(
            label="Logging out of the application will disconnect the active"
                  " vpn connection.\n\nDo you want to continue ?"
        )
        logout_dialog.get_content_area().add(label)
        self._state.logout_dialog = logout_dialog
        logout_dialog.show_all()

    def logout_button_click(self):
        """Clicks the logout button.
        This method was made available mainly for testing purposes."""
        self.logout_button.clicked()

    def close_dialog(self, end_current_connection):
        """Closes the logout dialog.
        This property was made available mainly for testing purposes."""
        self._state.logout_dialog.emit(
            "response",
            Gtk.ResponseType.YES if end_current_connection else Gtk.ResponseType.NO)

    def _on_logout_result(self, future: Future):
        """Callback when attempting to logout.
        Mainly used to emit if a sucessful logout has happened, or if a
            connection is found at logout, to display the dialog to the user.
        """
        try:
            future.result()
            logger.info("Successful logout", category="APP", subcategory="LOGOUT", event="SUCCESS")
            self.emit("user-logged-out")
        except VPNConnectionFoundAtLogout:
            self._show_disconnect_dialog()

    def _on_show_disconnect_response(self, _dialog, response):
        """Callback that is triggered once the user presses on a button from
        a dialog that is triggered from `_show_disconnect_dialog` """
        if response == Gtk.ResponseType.YES:
            logger.info("Yes", category="UI", subcategory="DIALOG", event="DISCONNECT")
            self._state.logout_after_vpn_disconnection = True
            self.quick_connect_widget.disconnect_button_click()
        else:
            logger.info("No", category="UI", subcategory="DIALOG", event="DISCONNECT")

        self._state.logout_dialog.destroy()
        self._state.logout_dialog = None

    def _on_vpn_data_ready(
            self,
            _vpn_data_refresher: VPNDataRefresher,
            server_list: ServerList,
            _client_config: ClientConfig
    ):
        if not self._state.is_widget_ready:
            self.display(self._state.user_tier, server_list)

    def load(self, user_tier: int):
        """
        Starts loading the widget.

        The call to this method triggers networks calls to Proton's REST API
        to download the required data to display the widget. Once the required
        data has been downloaded, the widget will be automatically displayed.
        """
        self._state.user_tier = user_tier
        self._controller.vpn_data_refresher.connect(
            "vpn-data-ready", self._on_vpn_data_ready
        )

        self._controller.vpn_data_refresher.enable()

    def display(self, user_tier: int, server_list: ServerList):
        """Displays the widget once all necessary data from API has been acquired."""
        self.server_list_widget.display(user_tier=user_tier, server_list=server_list)

        # Initialize connection status subscribers with current connection status.
        self.status_update(self._controller.current_connection_status)

        # The VPN widget subscribes to connection status updates, and then
        # passes on these connection status updates to child widgets
        self._controller.register_connection_status_subscriber(self)

        self._controller.reconnector.enable()

        self.show_all()
        self.emit("vpn-widget-ready")
        self._state.is_widget_ready = True
        logger.info(
            "VPN widget is ready",
            category="app", subcategory="VPN", event="widget_ready"
        )

    def unload(self):
        """Unloads the widget and resets its state."""
        if self._controller.is_connection_active:
            self._controller.disconnect()

        self._controller.unregister_connection_status_subscriber(self)

        self._controller.reconnector.disable()
        self._controller.vpn_data_refresher.disable()

        for widget in [
            self.connection_status_widget, self.logout_button,
            self.quick_connect_widget, self.server_list_widget
        ]:
            widget.hide()

        # Reset widget state
        self._state = VPNWidgetState()
