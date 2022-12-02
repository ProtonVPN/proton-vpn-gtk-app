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
from proton.vpn.servers.list import ServerList
from proton.vpn.core_api.client_config import ClientConfig
from proton.vpn.connection.enum import ConnectionStateEnum, StateMachineEventEnum
from proton.vpn.connection.states import Disconnected
from proton.vpn.core_api.exceptions import VPNConnectionFoundAtLogout
from proton.vpn import logging

from proton.vpn.app.gtk.widgets.vpn.status import VPNConnectionStatusWidget

logger = logging.getLogger(__name__)


class VPNWidget(Gtk.Box):  # pylint: disable=R0902
    """Exposes the ProtonVPN product functionality to the user."""

    # Number of seconds to wait before checking if the servers cache expired.
    RELOAD_INTERVAL_IN_SECONDS = 60

    def __init__(
        self,
        controller: Controller,
        server_list: "ServerList" = None,
        client_config: "ClientConfig" = None,
    ):
        super().__init__(spacing=10)

        self._reload_servers_source_id = None
        self._reload_clientconfig_source_id = None
        self._is_widget_loaded = False
        self._logout_button = None
        self._logout_dialog = None
        self._connection_status_widget = None
        self._quick_connect_widget = None

        self._server_list = server_list
        self._client_config = client_config
        # Keep track of child widgets that need to be aware of VPN connection status changes.
        self._connection_update_subscribers = []

        self.servers_widget = None
        # Last time the server list was updated
        self.last_server_list_update_time: int = 0

        self._controller = controller
        # Flag signaling when a logout is required after VPN disconnection.
        self._logout_after_vpn_disconnection = False
        self.set_orientation(Gtk.Orientation.VERTICAL)

        if not self._is_widget_loaded and self.is_api_data_retrieved:
            self.load_widget()

        self.connect("realize", self._on_realize)
        self.connect("unrealize", self._on_unrealize)

    @property
    def is_api_data_retrieved(self) -> bool:
        """Returns if the necessary data from API is retrived."""
        return self._server_list and self._client_config

    @GObject.Signal(name="vpn-widget-ready")
    def vpn_ready(self):
        """Signal emitted when all resources were loaded and widget is ready."""

    @GObject.Signal(name="update-server-list", arg_types=(object,))
    def update_server_list(self, server_list: object):
        """Signal emitted when server list object has been updated."""

    @GObject.Signal(name="update-client-config")
    def update_client_config(self):
        """Signal emitted when client config object has been updated."""

    @GObject.Signal(name="vpn-connection-error", arg_types=(str, str))
    def vpn_connection_error(self, title: str, text: str):
        """Signal emitted when a connection error occurred."""

    @GObject.Signal(name="user-logged-out")
    def user_logged_out(self):
        """Signal emitted once the user has been logged out."""

    def _on_realize(self, _servers_widget: ServerListWidget):
        self.start_reloading_data_periodically()
        self._controller.register_connection_status_subscriber(self)

    def _update_connection_status(self):
        connection = self._controller.current_connection
        if connection:
            self.status_update(connection.status)
        else:
            self.status_update(Disconnected())

    def _on_unrealize(self, _servers_widget: ServerListWidget):
        self.stop_reloading_data_periodically()
        if self._controller.is_connection_active:
            self._controller.disconnect()
            self._controller.unregister_connection_status_subscriber(self)

    def start_reloading_data_periodically(self):
        """Schedules retrieve_client_config to be called periodically according
        to VPNWidget.RELOAD_INTERVAL_IN_SECONDS."""
        self.retrieve_client_config()
        self.retrieve_servers()
        self._reload_clientconfig_source_id = GLib.timeout_add(
            interval=self.RELOAD_INTERVAL_IN_SECONDS * 1000,
            function=self.retrieve_client_config
        )
        self._reload_servers_source_id = GLib.timeout_add(
            interval=self.RELOAD_INTERVAL_IN_SECONDS * 1000,
            function=self.retrieve_servers
        )

    def retrieve_client_config(self) -> Future:
        """Returns client config."""
        future = self._controller.get_client_config()
        future.add_done_callback(
            lambda future: GLib.idle_add(
                self._on_clientconfig_retrieved, future
            )
        )
        return future

    def retrieve_servers(self) -> Future:
        """
        Requests the list of servers. Note that a remote API call is only
        triggered if the server list cache expired.
        :return: A future wrapping the server list.
        """
        logger.debug("Retrieving servers", category="APP", subcategory="SERVERS", event="RETRIEVE")
        future = self._controller.get_server_list()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_servers_retrieved, future)
        )
        return future

    def stop_reloading_data_periodically(self):
        """Stops the periodic calls to retrieve_client_config."""
        if self._reload_clientconfig_source_id is not None:
            GLib.source_remove(self._reload_clientconfig_source_id)
            self._reload_clientconfig_source_id = None
        if self._reload_servers_source_id is not None:
            GLib.source_remove(self._reload_servers_source_id)
            self._reload_servers_source_id = None
        else:
            logger.info(msg="Client config is not being reloaded periodically. "
                        "There is nothing to do.",
                        category="APP", subcategory="CLIENTCONFIG", event="RELOAD")

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
            self._logout_after_vpn_disconnection = True
            self._quick_connect_widget.disconnect_button_click()
        else:
            logger.info("No", category="UI", subcategory="DIALOG", event="DISCONNECT")

        self._logout_dialog.destroy()
        self._logout_dialog = None

    def _on_clientconfig_retrieved(self, future_client_config: Future):
        """Callback that emits a signals when the client config has been
        received.

        This is crucial for the widget to be displayed.
        """
        self._client_config = future_client_config.result()
        self.emit("update-client-config")

        if not self._is_widget_loaded and self.is_api_data_retrieved:
            self.load_widget()

    def _on_servers_retrieved(self, future_server_list: Future):
        """Callback that emits a signal if the server list has been updated
        or not, based on previous timestamp.

        This is crucial for the widget to be displayed.
        """
        server_list = future_server_list.result()
        if self._is_server_list_outdated(server_list):
            self._server_list = server_list
            self.last_server_list_update_time = server_list.loads_update_timestamp
            self.emit("update-server-list", server_list)
        else:
            logger.debug(
                "Skipping server list reload because it's already up to date.",
                category="APP", subcategory="SERVERS", event="RELOAD"
            )

        if not self._is_widget_loaded and self.is_api_data_retrieved:
            self.load_widget()

    def _is_server_list_outdated(self, new_server_list: ServerList):
        """Returns if server list is outdated or not."""
        new_timestamp = new_server_list.loads_update_timestamp
        return self.last_server_list_update_time < new_timestamp

    def load_widget(self):
        """Loads the widget once all necessary data from API is acquired."""
        self._connection_status_widget = VPNConnectionStatusWidget(
            self._controller
        )
        self.pack_start(self._connection_status_widget, expand=False, fill=False, padding=0)

        self._logout_dialog = None
        self._logout_button = Gtk.Button(label="Logout")
        self._logout_button.connect("clicked", self._on_logout_button_clicked)
        self.pack_start(self._logout_button, expand=False, fill=False, padding=0)

        self._quick_connect_widget = QuickConnectWidget(self._controller)
        self.pack_start(self._quick_connect_widget, expand=False, fill=False, padding=0)

        self.servers_widget = ServerListWidget(self._controller, self._server_list)
        self.pack_end(self.servers_widget, expand=True, fill=True, padding=0)

        for widget in [
            self._connection_status_widget,
            self._quick_connect_widget,
            self.servers_widget
        ]:
            self._connection_update_subscribers.append(widget)

        self._update_connection_status()
        self.connect("update-server-list", self.servers_widget.on_servers_update)
        self.show_all()
        self.emit("vpn-widget-ready")
        self._is_widget_loaded = True
