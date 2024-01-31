"""
This module defines the country widgets.


Copyright (c) 2023 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

from typing import List, Tuple, Set
from gi.repository import Atk, GLib, GObject

from proton.vpn.app.gtk.utils import accessibility
from proton.vpn.app.gtk.utils.search import normalize
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.session.servers import Country
from proton.vpn import logging
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import \
    SmartRoutingIcon, P2PIcon, TORIcon, UnderMaintenanceIcon
from proton.vpn.app.gtk.widgets.vpn.serverlist.server import ServerRow
from proton.vpn.session.servers import LogicalServer
from proton.vpn.session.servers import ServerFeatureEnum

logger = logging.getLogger(__name__)


class CountryHeader(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """Header with the country name shown at the beginning of each CountryRow."""
    # pylint: disable=too-many-arguments
    def __init__(
            self,
            country: Country,
            under_maintenance: bool,
            upgrade_required: bool,
            server_features: Set[ServerFeatureEnum],
            smart_routing: bool,
            connection_state: ConnectionStateEnum,
            controller: Controller,
            show_country_servers: bool = False
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self._country = country
        self._under_maintenance = under_maintenance
        self._upgrade_required = upgrade_required
        self._server_features = server_features
        self._smart_routing = smart_routing
        self._controller = controller

        self._country_name_label = None
        self._under_maintenance_icon = None
        self._connect_button = None
        self._country_details = None

        self._collapsed_img = Gtk.Image.new_from_icon_name("pan-down-symbolic", Gtk.IconSize.BUTTON)
        self._expanded_img = Gtk.Image.new_from_icon_name("pan-up-symbolic", Gtk.IconSize.BUTTON)

        self._build_ui(connection_state)

        # The following setters needs to be called after the UI has been built
        # as they need to modify some UI widgets.
        self.show_country_servers = show_country_servers
        self._connection_state = connection_state

    def _build_ui(self, connection_state: ConnectionStateEnum):
        self._country_name_label = Gtk.Label(label=self.country_name)
        self.pack_start(self._country_name_label, expand=False, fill=False, padding=0)
        self.set_spacing(10)

        self._toggle_button = Gtk.Button()
        self._toggle_button.get_style_context().add_class("secondary")
        self._toggle_button.connect("clicked", self._on_toggle_button_clicked)
        self.pack_end(self._toggle_button, expand=False, fill=False, padding=0)

        self._show_under_maintenance_icon_or_country_details()

        self.connection_state = connection_state

    def update_under_maintenance_status(self, under_maintenance: bool):
        """Shows or hides the under maintenance status for the country."""
        self._under_maintenance = under_maintenance
        self._show_under_maintenance_icon_or_country_details()

    def _show_under_maintenance_icon_or_country_details(self):
        if self._under_maintenance:
            self._show_under_maintenance_icon()
        else:
            self._show_country_details()

    def _show_under_maintenance_icon(self):
        if self._country_details:
            self._country_details.hide()

        if not self._under_maintenance_icon:
            self._under_maintenance_icon = UnderMaintenanceIcon(self.country_name)
            self.pack_end(self._under_maintenance_icon, expand=False, fill=False, padding=0)

        self._country_name_label.set_property("sensitive", False)

    def _show_country_details(self):
        if self._under_maintenance_icon:
            self._under_maintenance_icon.hide()

        if not self._country_details:
            self._country_details = self._build_country_details()
            self.pack_end(self._country_details, expand=False, fill=False, padding=0)

        self._country_details.show()
        self._country_name_label.set_property("sensitive", True)

    def _build_country_details(self):
        country_details = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        if self._upgrade_required:
            button = self._build_upgrade_required_link_button()
            country_details.pack_end(button, expand=False, fill=False, padding=0)
        else:
            button = self._build_connect_button()
            self._connect_button = button
            country_details.pack_end(self._connect_button, expand=False, fill=False, padding=0)

        button_relationships = [(self._country_name_label, Atk.RelationType.LABELLED_BY)]

        country_row_icons = []
        if self._smart_routing:
            country_row_icons.append(SmartRoutingIcon())

        server_feature_icons = self._build_server_feature_icons()
        country_row_icons.extend(server_feature_icons)
        for icon in country_row_icons:
            button_relationships.append((icon, Atk.RelationType.DESCRIBED_BY))
            country_details.pack_end(icon, expand=False, fill=False, padding=5)

        accessibility.add_widget_relationships(button, button_relationships)

        return country_details

    @property
    def under_maintenance(self) -> bool:
        """Indicates whether all the servers for this country are under maintenance or not."""
        return self._under_maintenance

    @property
    def upgrade_required(self):
        """Indicates whether the user needs to upgrade to have access to this country or not."""
        return self._upgrade_required

    def _build_upgrade_required_link_button(self) -> Gtk.LinkButton:
        upgrade_button = Gtk.LinkButton.new_with_label("Upgrade")
        upgrade_button.set_uri("https://account.protonvpn.com/")
        return upgrade_button

    def _build_connect_button(self) -> Gtk.Button:
        connect_button = Gtk.Button()
        connect_button.connect("clicked", self._on_connect_button_clicked)
        connect_button.get_style_context().add_class("secondary")
        return connect_button

    def _build_server_feature_icons(self) -> List[Gtk.Image]:
        server_feature_icons = []
        if ServerFeatureEnum.P2P in self._server_features:
            server_feature_icons.append(P2PIcon())
        if ServerFeatureEnum.TOR in self._server_features:
            server_feature_icons.append(TORIcon())
        return server_feature_icons

    @property
    def server_features(self) -> Set[ServerFeatureEnum]:
        """Returns the set of features supported by the servers in this country."""
        return self._server_features

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
        self._toggle_button.set_image(
            self._expanded_img if self.show_country_servers else self._collapsed_img
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
        future = self._controller.connect_to_country(self.country_code)
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.

    def _on_connection_state_disconnected(self):
        """Flags this server as "not connected"."""
        self._connect_button.set_sensitive(True)
        self._connect_button.set_label("Connect")

    def _on_connection_state_connecting(self):
        """Flags this server as "connecting"."""
        self._connect_button.set_label("Connecting...")
        self._connect_button.set_sensitive(False)

    def _on_connection_state_connected(self):
        """Flags this server as "connected"."""
        self._connect_button.set_sensitive(False)
        self._connect_button.set_label("Connected")

    def _on_connection_state_disconnecting(self):
        pass

    def _on_connection_state_error(self):
        """Flags this server as "error"."""
        self._on_connection_state_disconnected()

    def click_toggle_country_servers_button(self):
        """Clicks the button to toggle the country servers.
        This method was made available for tests."""
        self._toggle_button.clicked()

    def click_connect_button(self):
        """Clicks the button to connect to the country.
        This method was made available for tests."""
        self._connect_button.clicked()


class CountryRow(Gtk.Box):  # pylint: disable=too-many-instance-attributes
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
        is_free_user = user_tier == 0

        # Properties initialized after building all server rows.
        self._is_free_country = None
        self._upgrade_required = None
        self._country_features = set()
        self._under_maintenance = None

        self._server_rows_revealer = Gtk.Revealer()
        server_rows_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._server_rows_revealer.add(server_rows_container)

        ordered_servers = []
        if is_free_user:
            ordered_servers.extend(free_servers)
            ordered_servers.extend(plus_servers)
        else:
            ordered_servers.extend(plus_servers)
            ordered_servers.extend(free_servers)

        # The country is set under maintenance until the opposite is proven.
        self._under_maintenance = True
        # The country connection state is set as disconnected until the opposite is proven.
        country_connection_state = ConnectionStateEnum.DISCONNECTED
        # Smart routing is assumed to be used until the opposite is proven.
        smart_routing_country = True
        for server in ordered_servers:
            self._country_features.update(server.features)
            self._is_free_country = self._is_free_country or server.tier == 0
            # The country is under maintenance if (1) that was the case up until now and
            # (2) the current server is also under maintenance (i.e. is not enabled).
            self._under_maintenance = (self._under_maintenance and not server.enabled)
            # A country is flagged as a "Smart rouging" location if *all* servers are
            # actually physically located in a neighbouring country.
            smart_routing_country = smart_routing_country and server.host_country is not None

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
                country_connection_state = server_row.connection_state = \
                    ConnectionStateEnum.CONNECTED

        self._upgrade_required = is_free_user and not self._is_free_country

        self._country_header = CountryHeader(
            country=country,
            under_maintenance=self._under_maintenance,
            upgrade_required=self._upgrade_required,
            server_features=self._country_features,
            smart_routing=smart_routing_country,
            connection_state=country_connection_state,
            controller=controller,
            show_country_servers=show_country_servers
        )
        self._country_header.connect(
            "toggle-country-servers", self._on_toggle_country_servers
        )

        self.pack_start(self._country_header, expand=False, fill=False, padding=5)
        self.pack_start(self._server_rows_revealer, expand=False, fill=False, padding=5)

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
    def _group_servers_by_tier(country_servers) -> Tuple[List[LogicalServer]]:
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

    def connection_status_update(self, connection_state):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        self._country_header.connection_state = connection_state.type
        server_id = connection_state.context.connection.server_id
        server = self._get_server_row(server_id)
        server.connection_state = connection_state.type

    def click_connect_button(self):
        """Clicks the button to connect to the country.
        This method was made available for tests."""
        self._country_header.click_connect_button()

    def update_server_loads(self):
        """Refreshes the UI after new server loads were retrieved."""
        # Start by setting the country under maintenance until the opposite is proven.
        self._under_maintenance = True
        for server_row in self._indexed_server_rows.values():
            server_row.update_server_load()
            self._under_maintenance = (
                    self._under_maintenance and server_row.under_maintenance
            )
        self._country_header.update_under_maintenance_status(
            self._under_maintenance
        )
