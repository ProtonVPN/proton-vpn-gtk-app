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
from proton.vpn.app.gtk.widgets.vpn.server import ServerRow
from proton.vpn.app.gtk import utils


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
        country_name = utils.get_country_name_by_code(country_code)
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
