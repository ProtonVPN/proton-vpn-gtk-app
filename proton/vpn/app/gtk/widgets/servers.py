"""
This module defines the widgets used to present the VPN server list to the user.
"""
from __future__ import annotations

from concurrent.futures import Future
from itertools import groupby
from typing import List

from gi.repository import GLib, GObject
from iso3166 import countries

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.servers.server_types import LogicalServer
from proton.vpn.servers.list import ServerList, VPNServer
from proton.vpn.core_api import vpn_logging as logging


logger = logging.getLogger(__name__)


class CountryHeader(Gtk.Box):
    """Header with the country name shown at the beginning of each CountryRow."""
    def __init__(self, country_name: str, show_country_servers=False):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.country_name = country_name

        self.pack_start(Gtk.Label(label=country_name), expand=False, fill=False, padding=5)
        self._toggle_button = Gtk.Button(label="")
        self._toggle_button.connect("clicked", self._on_toggle_button_clicked)
        self.pack_end(self._toggle_button, expand=False, fill=False, padding=5)

        self.show_country_servers = show_country_servers

    @GObject.Signal(name="toggle-country-servers")
    def toggle_country_servers(self):
        """Signal when the user clicks the button to expand/collapse the servers
        from a country."""

    @property
    def show_country_servers(self):
        """Returns whether the country servers should be shown or not."""
        return self._show_country_servers

    @show_country_servers.setter
    def show_country_servers(self, show_country_servers: bool):
        """Sets whether the country servers should be shown or not."""
        self._show_country_servers = show_country_servers
        if self.show_country_servers:
            self._toggle_button.set_label("Hide servers")
        else:
            self._toggle_button.set_label("Show servers")

    def click_toggle_country_servers_button(self):
        """Clicks the button to toggle the country servers.
        This method was made available for tests."""
        self._toggle_button.clicked()

    def _on_toggle_button_clicked(self, _toggle_button: Gtk.Button):
        self.show_country_servers = not self.show_country_servers
        self.emit("toggle-country-servers")


class CountryRow(Gtk.Box):
    """Row containing all servers from a country."""
    def __init__(
            self,
            country_code: str,
            country_servers: List[LogicalServer],
            user_tier: int,
            connected_country_row: CountryRow = None,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._indexed_server_rows = {}
        self.connected_server_row = None

        self._server_rows_revealer = Gtk.Revealer()
        country_name = _get_country_name_by_code(country_code)
        self._country_header = CountryHeader(country_name)
        self.pack_start(self._country_header, expand=False, fill=False, padding=5)
        self._country_header.connect("toggle-country-servers", self._on_toggle_country_servers)

        self._server_rows_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(self._server_rows_revealer, expand=False, fill=False, padding=5)
        self._server_rows_revealer.add(self._server_rows_container)

        for server in country_servers:
            server_row = ServerRow(server=server, user_tier=user_tier)
            self._server_rows_container.pack_start(
                server_row,
                expand=False, fill=False, padding=5
            )
            server_row.connect(
                "server-connection-request",
                self._on_server_connection_request
            )

            self._indexed_server_rows[server.name] = server_row

            # If we are currently connected to a server then set its row state to "connected".
            if connected_country_row and \
                    connected_country_row.connected_server_row.server.name == server.name:
                self.connected_server_row = server_row
                server_row.connection_state = ConnectionStateEnum.CONNECTED

    @GObject.Signal(name="server-connection-request", arg_types=(object,))
    def server_connection_request(self, server_row: ServerRow):
        """
        Signal emitted when the user request to connect to a server.
        """

    @property
    def country_name(self):
        """Returns the name of the country.
        This method was made available for tests."""
        return self._country_header.country_name

    @property
    def showing_servers(self):
        """Returns True if the servers are being showed and False otherwise.
        This method was made available for tests."""
        return self._server_rows_revealer.get_reveal_child()

    def click_toggle_country_servers_button(self):
        """
        Clicks the button to toggle the visibility of the country servers.
        This method was made available for tests.
        """
        self._country_header.click_toggle_country_servers_button()

    @property
    def server_rows(self) -> List[ServerRow]:
        """Returns the list of server rows for this server.
        This method was made available for tests."""
        return self._server_rows_container.get_children()

    def _on_toggle_country_servers(self, country_header: CountryHeader):
        self._server_rows_revealer.set_reveal_child(country_header.show_country_servers)

    def _get_server_row(self, vpn_server) -> ServerRow:
        try:
            return self._indexed_server_rows[vpn_server.servername]
        except KeyError as error:
            raise RuntimeError(
                f"Unable to get server row for {vpn_server.servername}."
            ) from error

    def connection_status_update(self, connection_status, vpn_server: VPNServer):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        server = self._get_server_row(vpn_server)
        server.connection_state = connection_status.state
        if connection_status.state == ConnectionStateEnum.CONNECTED:
            self.connected_server_row = server
        elif connection_status.state == ConnectionStateEnum.DISCONNECTED:
            self.connected_server_row = None

    def _on_server_connection_request(self, server_row: ServerRow):
        self.emit("server-connection-request", server_row)


class ServerRow(Gtk.Box):
    """Displays a single server as a row in the server list."""
    def __init__(self, server: LogicalServer, user_tier: int):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.server = server
        self._user_tier = user_tier
        self._connection_state: ConnectionStateEnum = None
        self._build_row()

    @property
    def connection_state(self):
        """Returns the connection state of the server shown in this row."""
        return self._connection_state

    @connection_state.setter
    def connection_state(self, connection_state: ConnectionStateEnum):
        """Sets the connection state, modifying the row depending on the state."""
        self._connection_state = connection_state

        # Update the server row according to the connection state.
        method = f"_on_connection_state_{connection_state.name.lower()}"
        if hasattr(self, method):
            getattr(self, method)()

    def _build_row(self):
        self._server_label = Gtk.Label(label=self.server.name)
        self.pack_start(
            self._server_label,
            expand=False, fill=False, padding=10
        )

        self._load_label = Gtk.Label(label=f"{self.server.load}%")
        self.pack_start(
            self._load_label,
            expand=False, fill=False, padding=10
        )

        if not self.server.enabled:
            self.pack_end(
                Gtk.Label(label="(under maintenance)"),
                expand=False, fill=False, padding=10
            )
            return

        if self.upgrade_required:
            self._upgrade_button = Gtk.LinkButton.new_with_label("Upgrade")
            self._upgrade_button.set_uri("https://account.protonvpn.com/")
            _button_to_attach = self._upgrade_button
        else:
            self._connect_button = Gtk.Button(label="Connect")
            self._connect_button.set_sensitive(True)
            handler_id = self._connect_button.connect("clicked", self._on_connect_button_clicked)
            self.connect("destroy", lambda _: self._connect_button.disconnect(handler_id))
            _button_to_attach = self._connect_button

        self.pack_end(
            _button_to_attach,
            expand=False, fill=False, padding=10
        )

    @GObject.Signal(name="server-connection-request")
    def server_connection_request(self):
        """
        Signal emitted when the user request to connect to a server.
        """

    def _on_connection_state_connecting(self):
        """Flags this server as "connecting"."""
        self._connect_button.set_label("Connecting...")
        self._connect_button.set_sensitive(False)

    def _on_connection_state_connected(self):
        """Flags this server as "connected"."""
        self._connect_button.set_sensitive(False)
        self._connect_button.set_label("Connected")

    def _on_connection_state_disconnected(self):
        """Flags this server as "not connected"."""
        self._connect_button.set_sensitive(True)
        self._connect_button.set_label("Connect")

    def _on_connect_button_clicked(self, _):
        self.emit("server-connection_request")

    @property
    def upgrade_required(self) -> bool:
        """Returns if a plan upgrade is required to connect to server."""
        return self.server.tier > self._user_tier

    @property
    def server_label(self):
        """Returns the server label.
        This method was made available for tests."""
        return self._server_label.get_label()

    @property
    def under_maintenance(self):
        """Returns if the server is under maintenance.
        This method was made available for tests."""
        return not self.server.enabled

    def click_connect_button(self):
        """Clicks the connect button.
        This method was made available for tests."""
        self._connect_button.clicked()


class ServersWidget(Gtk.ScrolledWindow):
    """Displays the VPN servers list."""

    # Number of seconds to wait before checking if the servers cache expired.
    RELOAD_INTERVAL_IN_SECONDS = 60

    def __init__(self, controller: Controller, server_list: ServerList = None):
        super().__init__()
        self.set_policy(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self._controller = controller
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._container.set_margin_end(15)  # Leave space for the scroll bar.
        self.add(self._container)
        self._server_list = server_list
        self._last_update_time = server_list.loads_update_timestamp if server_list else 0
        self._reload_servers_source_id = None
        self._connected_country_row = None  # Row of the country we are connected to.
        self._country_rows = {}  # Country rows indexed by country code.

        if self._server_list:
            self._show_servers()

        self.connect("realize", self._on_realize)
        self.connect("unrealize", self._on_unrealize)

    @GObject.Signal(name="server-list-updated")
    def server_list_updated(self):
        """Signal emitted once the server list has been updated. That
        happens the first time the server list is rendered and every
        time the server list changes."""

    @property
    def country_rows(self) -> List[CountryRow]:
        """Returns the list of country rows that are currently being displayed.
        This method was made available for tests."""
        return self._container.get_children()

    def retrieve_servers(self) -> Future:
        """
        Requests the list of servers. Note that a remote API call is only
        triggered if the server list cache expired.
        :return: A future wrapping the server list.
        """
        logger.debug("Retrieving servers", category="APP", subcategory="SERVERS", event="RETRIEVE")
        future = self._controller.get_server_list()
        if not self._server_list:
            self._show_loading()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_servers_retrieved, future)
        )
        return future

    def start_reloading_servers_periodically(self):
        """Schedules retrieve_servers to be called periodically according
        to ServersWidget.RELOAD_INTERVAL_IN_SECONDS."""
        self.retrieve_servers()
        self._reload_servers_source_id = GLib.timeout_add(
            interval=self.RELOAD_INTERVAL_IN_SECONDS * 1000,
            function=self.retrieve_servers
        )

    def stop_reloading_servers_periodically(self):
        """Stops the periodic calls to retrieve_servers."""
        if self._reload_servers_source_id is not None:
            GLib.source_remove(self._reload_servers_source_id)
        else:
            logger.info(msg="Servers are not being reloaded periodically. "
                        "There is nothing to do.",
                        category="APP", subcategory="SERVERS", event="RELOAD")

    def connection_status_update(self, connection_status, vpn_server: VPNServer):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        if vpn_server:
            def update_server_rows():
                country_row = self._get_country_row(vpn_server)
                country_row.connection_status_update(connection_status, vpn_server)

                if connection_status.state == ConnectionStateEnum.CONNECTED:
                    self._connected_country_row = country_row
                elif connection_status.state == ConnectionStateEnum.DISCONNECTED:
                    self._connected_country_row = None

            GLib.idle_add(update_server_rows)

    def _on_realize(self, _servers_widget: ServersWidget):
        self.start_reloading_servers_periodically()

    def _on_unrealize(self, _servers_widget: ServersWidget):
        self.stop_reloading_servers_periodically()

    def _remove_all_servers(self):
        for row in self._container.get_children():
            self._container.remove(row)
            row.destroy()
        self._country_rows = {}

    def _show_loading(self):
        self._remove_all_servers()
        self._container.pack_start(
            Gtk.Label(label="Loading..."),
            expand=False, fill=False, padding=5
        )
        self._container.show_all()

    def _is_server_list_outdated(self, new_server_list: ServerList):
        new_timestamp = new_server_list.loads_update_timestamp
        return self._last_update_time < new_timestamp

    def _on_servers_retrieved(self, future_server_list: Future):
        new_server_list = future_server_list.result()
        if self._is_server_list_outdated(new_server_list):
            self._last_update_time = new_server_list.loads_update_timestamp
            self._server_list = new_server_list
            self._show_servers()
        else:
            logger.debug(
                "Skipping server list reload because it's already up to date.",
                category="APP", subcategory="SERVERS", event="RELOAD"
            )

    def _show_servers(self):
        self._remove_all_servers()
        self._add_all_servers()

        self._container.show_all()
        logger.info("Server list updated.", category="APP", subcategory="SERVERS", event="RELOAD")
        self.emit("server-list-updated")

    def _add_all_servers(self):
        def sorting_key(server: LogicalServer):
            server_name = server.name

            if server_name is None:
                server_name = ""
            server_name = server_name.lower()

            if "#" not in server_name:
                return server_name.lower()

            country_name = _get_country_name_by_code(server.exit_country)

            return f"{country_name}__" \
                   f"{server_name.split('#')[0]}" \
                   f"{server_name.split('#')[1].zfill(5)}"

        self._server_list.sort(key=sorting_key)

        def grouping_key(server: LogicalServer):
            return server.exit_country.lower()

        for country_code, country_servers in groupby(self._server_list, grouping_key):
            country_row = CountryRow(
                country_code, country_servers, self._controller.user_tier,
                self._connected_country_row
            )
            self._container.pack_start(
                country_row,
                expand=False, fill=False, padding=5
            )
            self._country_rows[country_code.lower()] = country_row
            country_row.connect(
                "server-connection-request",
                self._on_server_connection_request
            )

    def _get_country_row(self, vpn_server) -> CountryRow:
        logical_server = self._server_list.get_by_name(vpn_server.servername)
        country_code = logical_server.exit_country.lower()
        try:
            return self._country_rows[country_code]
        except KeyError as error:
            raise RuntimeError(
                f"Unable to get country row {country_code} for server "
                f"{vpn_server.servername}."
            ) from error

    def _on_server_connection_request(
            self, _country_row: CountryRow, server_row: ServerRow
    ):
        self._controller.connect(server_name=server_row.server.name)


def _get_country_name_by_code(country_code: str):
    if country_code.lower() == "uk":
        # Even though we use UK, the correct ISO 3166 code is GB.
        country_code = "gb"

    country = countries.get(country_code.lower(), default=None)

    # If the country name was not found then default to the country code.
    return country.name if country else country_code
