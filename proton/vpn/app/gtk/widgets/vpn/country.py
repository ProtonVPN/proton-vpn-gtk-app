"""
This module defines the country widgets.
"""

from __future__ import annotations

from typing import List, Tuple
from gi.repository import GObject
from proton.vpn.app.gtk.utils.search import normalize
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.servers import Country
from proton.vpn import logging
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.server import ServerRow


logger = logging.getLogger(__name__)


class CountryHeader(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """Header with the country name shown at the beginning of each CountryRow."""
    def __init__(
            self,
            country: Country,
            upgrade_required: bool,
            controller: Controller,
            show_country_servers: bool = False
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self._country = country
        self.upgrade_required = upgrade_required
        self.under_maintenance = all(not server.enabled for server in country.servers)
        self._controller = controller

        self._connection_state = None

        self._build_ui()

        # The following setters needs to be called after the UI has been built
        # as they need to modify some UI widgets.
        self.show_country_servers = show_country_servers
        self.connection_state = ConnectionStateEnum.DISCONNECTED

    def _build_ui(self):
        country_name_label = Gtk.Label(label=self.country_name)
        self.pack_start(country_name_label, expand=False, fill=False, padding=0)
        self.set_spacing(10)

        self._toggle_button = Gtk.Button()
        self._toggle_button.connect("clicked", self._on_toggle_button_clicked)
        self.pack_end(self._toggle_button, expand=False, fill=False, padding=0)

        if self.upgrade_required:
            upgrade_button = Gtk.LinkButton.new_with_label("Upgrade")
            upgrade_button.set_tooltip_text(
                f"Upgrade to connect to {self.country_name}"
            )
            upgrade_button.set_uri("https://account.protonvpn.com/")
            self.pack_end(upgrade_button, expand=False, fill=False, padding=0)

        if self.under_maintenance:
            under_maintenance_label = Gtk.Label(label="(under maintenance)")
            self.pack_end(under_maintenance_label, expand=False, fill=False, padding=0)

        if self.available:
            self._connect_button = Gtk.Button()
            self._connect_button.connect("clicked", self._on_connect_button_clicked)
            self.pack_end(self._connect_button, expand=False, fill=False, padding=0)

    @GObject.Signal(name="toggle-country-servers")
    def toggle_country_servers(self):
        """Signal when the user clicks the button to expand/collapse the servers
        from a country."""

    @property
    def country_code(self):
        """Returns the code of the country this header is for."""
        return self._country.code

    @property
    def country_name(self):
        """Returns the name of the country this header is for."""
        return self._country.name

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
    def available(self) -> bool:
        """Returns True if the country is available, meaning the user can
        connect to one of its servers. Otherwise, it returns False."""
        return not self.upgrade_required and not self.under_maintenance

    @property
    def connection_state(self):
        """Returns the connection state of the server shown in this row."""
        return self._connection_state

    @connection_state.setter
    def connection_state(self, connection_state: ConnectionStateEnum):
        """Sets the connection state, modifying the row depending on the state."""
        # pylint: disable=duplicate-code
        self._connection_state = connection_state

        if self.available:
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

    def _on_connection_state_error(self):
        """Flags this server as "error"."""
        self._on_connection_state_disconnected()

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

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            country: Country,
            user_tier: int,
            controller: Controller,
            connected_server_id: str = None,
            show_country_servers: bool = False,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self._indexed_server_rows = {}

        free_servers, plus_servers = self._group_servers_by_tier(country.servers)
        self._is_free_country = len(free_servers) > 0
        is_free_user = user_tier == 0
        self._upgrade_required = (is_free_user and not country.is_free)

        self._country_header = CountryHeader(
            country=country,
            upgrade_required=self.upgrade_required,
            controller=controller,
            show_country_servers=show_country_servers
        )
        self.pack_start(self._country_header, expand=False, fill=False, padding=5)
        self._country_header.connect(
            "toggle-country-servers", self._on_toggle_country_servers
        )

        self._server_rows_revealer = Gtk.Revealer()
        self.pack_start(self._server_rows_revealer, expand=False, fill=False, padding=5)
        server_rows_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._server_rows_revealer.add(server_rows_container)

        ordered_servers = []
        if is_free_user:
            ordered_servers.extend(free_servers)
            ordered_servers.extend(plus_servers)
        else:
            ordered_servers.extend(plus_servers)
            ordered_servers.extend(free_servers)

        for server in ordered_servers:
            server_row = ServerRow(
                server=server,
                user_tier=user_tier,
                controller=self._controller
            )
            server_rows_container.pack_start(
                server_row,
                expand=False, fill=False, padding=5
            )

            self._indexed_server_rows[server.id] = server_row

            # If we are currently connected to a server then set its row state to "connected".
            if connected_server_id == server.id:
                self._country_header.connection_state = ConnectionStateEnum.CONNECTED
                server_row.connection_state = ConnectionStateEnum.CONNECTED

        if show_country_servers:
            self._server_rows_revealer.set_reveal_child(True)

    @property
    def country_name(self):
        """Returns the name of the country.
        This method was made available for tests."""
        return self._country_header.country_name

    @property
    def upgrade_required(self):
        """Returns True if this country is not in the currently logged-in
        user tier, and therefore it requires a plan upgrade. Otherwise, it
        returns False."""
        return self._upgrade_required

    @property
    def is_free_country(self) -> bool:
        """Returns True if this country has any servers available to
        users with a free account. Otherwise, it returns False."""
        return self._is_free_country

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
        return self._server_rows_revealer.get_child().get_children()

    @property
    def connection_state(self):
        """Returns the connection state for this row."""
        return self._country_header.connection_state

    @property
    def header_searchable_content(self) -> str:
        """Returns the normalized searchable content for the country header."""
        return normalize(self.country_name)

    @staticmethod
    def _group_servers_by_tier(country_servers) -> Tuple[List]:
        free_servers = []
        plus_servers = []
        for server in country_servers:
            if server.tier == 0:
                free_servers.append(server)
            else:
                plus_servers.append(server)

        return free_servers, plus_servers

    def _on_toggle_country_servers(self, country_header: CountryHeader):
        self._server_rows_revealer.set_reveal_child(country_header.show_country_servers)

    def set_servers_visibility(self, visible: bool):
        """Country servers will be shown if set to True. Otherwise, they'll be hidden."""
        self._country_header.show_country_servers = visible
        self._server_rows_revealer.set_reveal_child(visible)

    def _get_server_row(self, server_id: str) -> ServerRow:
        try:
            return self._indexed_server_rows[server_id]
        except KeyError as error:
            raise RuntimeError(
                f"Unable to get server row for {server_id}."
            ) from error

    def connection_status_update(self, connection_status):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        self._country_header.connection_state = connection_status.state
        server_id = connection_status.context.connection.server_id
        server = self._get_server_row(server_id)
        server.connection_state = connection_status.state

    def click_connect_button(self):
        """Clicks the button to connect to the country.
        This method was made available for tests."""
        self._country_header.click_connect_button()
