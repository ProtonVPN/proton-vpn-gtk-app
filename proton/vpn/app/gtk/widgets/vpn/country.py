"""
This module defines the country widgets.
"""

from __future__ import annotations
from typing import List
from gi.repository import GObject
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.servers.server_types import LogicalServer
from proton.vpn.servers.list import VPNServer
from proton.vpn.core_api import vpn_logging as logging
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.server import ServerRow
from proton.vpn.app.gtk import utils


logger = logging.getLogger(__name__)


class CountryHeader(Gtk.Box):  # pylint: disable=R0902
    """Header with the country name shown at the beginning of each CountryRow."""
    def __init__(
            self, country_code: str,
            upgrade_required: bool,
            controller: Controller,
            show_country_servers: bool = False
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.upgrade_required = upgrade_required
        self._controller = controller

        self.country_code = country_code
        country_name = utils.get_country_name_by_code(country_code)
        self.country_name = country_name

        self._connection_state = None

        self._build_ui(country_name, upgrade_required)

        # The following setters needs to be called after the UI has been built
        # as they need to modify some UI widgets.
        self.show_country_servers = show_country_servers
        self.connection_state = ConnectionStateEnum.DISCONNECTED

    def _build_ui(self, country_name, upgrade_required):
        country_name_label = Gtk.Label(label=country_name)
        self.pack_start(country_name_label, expand=False, fill=False, padding=5)

        self._toggle_button = Gtk.Button()
        self._toggle_button.connect("clicked", self._on_toggle_button_clicked)
        self.pack_end(self._toggle_button, expand=False, fill=False, padding=5)

        if upgrade_required:
            self._upgrade_button = Gtk.LinkButton.new_with_label("Upgrade")
            self._upgrade_button.set_tooltip_text(
                f"Upgrade to connect to {self.country_name}"
            )
            self._upgrade_button.set_uri("https://account.protonvpn.com/")
            button_to_pack = self._upgrade_button
        else:
            self._connect_button = Gtk.Button()
            self._connect_button.connect("clicked", self._on_connect_button_clicked)
            button_to_pack = self._connect_button

        self.pack_end(button_to_pack, expand=False, fill=False, padding=5)

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
        self._toggle_button.set_label(
            "-" if self.show_country_servers else "+"
        )
        self._toggle_button.set_tooltip_text(
            f"Hide all servers from {self.country_name}" if self.show_country_servers else
            f"Show all servers from {self.country_name}"
        )

    @property
    def connection_state(self):
        """Returns the connection state of the server shown in this row."""
        return self._connection_state

    @connection_state.setter
    def connection_state(self, connection_state: ConnectionStateEnum):
        """Sets the connection state, modifying the row depending on the state."""
        # pylint: disable=duplicate-code
        self._connection_state = connection_state

        if not self.upgrade_required:
            # Update the server row according to the connection state.
            method = f"_on_connection_state_{connection_state.name.lower()}"
            if hasattr(self, method):
                getattr(self, method)()

    def _on_toggle_button_clicked(self, _toggle_button: Gtk.Button):
        self.show_country_servers = not self.show_country_servers
        self.emit("toggle-country-servers")

    def _on_connect_button_clicked(self, _connect_button: Gtk.Button):
        self._controller.connect_to_country(self.country_code)

    def _on_connection_state_connecting(self):
        """Flags this server as "connecting"."""
        self._connect_button.set_label("Connecting...")
        self._connect_button.set_tooltip_text(
            f"Connecting to {self.country_name}..."
        )
        self._connect_button.set_sensitive(False)

    def _on_connection_state_connected(self):
        """Flags this server as "connected"."""
        self._connect_button.set_sensitive(False)
        self._connect_button.set_tooltip_text(
            f"Connected to {self.country_name}"
        )
        self._connect_button.set_label("Connected")

    def _on_connection_state_disconnected(self):
        """Flags this server as "not connected"."""
        self._connect_button.set_sensitive(True)
        self._connect_button.set_tooltip_text(
            f"Connect to {self.country_name}"
        )
        self._connect_button.set_label("Connect")

    def click_toggle_country_servers_button(self):
        """Clicks the button to toggle the country servers.
        This method was made available for tests."""
        self._toggle_button.clicked()

    def click_connect_button(self):
        """Clicks the button to connect to the country.
        This method was made available for tests."""
        self._connect_button.clicked()


class CountryRow(Gtk.Box):
    """Row containing all servers from a country."""
    def __init__(
            self,
            country_code: str,
            country_servers: List[LogicalServer],
            controller: Controller,
            connected_country_row: CountryRow = None,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self._indexed_server_rows = {}
        self.connected_server_row = None
        self.upgrade_required = all(
            server.tier > self._controller.user_tier for server in country_servers
        )

        self._server_rows_revealer = Gtk.Revealer()
        self._country_header = CountryHeader(country_code, self.upgrade_required, controller)

        self.pack_start(self._country_header, expand=False, fill=False, padding=5)
        self._country_header.connect("toggle-country-servers", self._on_toggle_country_servers)

        self._server_rows_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(self._server_rows_revealer, expand=False, fill=False, padding=5)
        self._server_rows_revealer.add(self._server_rows_container)

        for server in country_servers:
            server_row = ServerRow(server=server, controller=self._controller)
            self._server_rows_container.pack_start(
                server_row,
                expand=False, fill=False, padding=5
            )

            self._indexed_server_rows[server.name] = server_row

            # If we are currently connected to a server then set its row state to "connected".
            if connected_country_row and \
                    connected_country_row.connected_server_row.server.name == server.name:
                self.connected_server_row = server_row
                self._country_header.connection_state = ConnectionStateEnum.CONNECTED
                server_row.connection_state = ConnectionStateEnum.CONNECTED

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

    @property
    def connection_state(self):
        """Returns the connection state for this row."""
        return self._country_header.connection_state

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
        self._country_header.connection_state = connection_status.state
        server = self._get_server_row(vpn_server)
        server.connection_state = connection_status.state
        if connection_status.state == ConnectionStateEnum.CONNECTED:
            self.connected_server_row = server
        elif connection_status.state == ConnectionStateEnum.DISCONNECTED:
            self.connected_server_row = None

    def click_connect_button(self):
        """Clicks the button to connect to the country.
        This method was made available for tests."""
        self._country_header.click_connect_button()
