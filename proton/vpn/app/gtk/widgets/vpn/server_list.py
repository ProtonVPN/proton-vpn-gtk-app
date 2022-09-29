"""
This module defines the widgets used to present the VPN server list to the user.
"""
from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass, field
from itertools import groupby
from typing import List, Dict, Optional, Callable

from gi.repository import GLib, GObject

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.country import CountryRow
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.servers.server_types import LogicalServer, ServerFeatureEnum
from proton.vpn.servers.list import ServerList, VPNServer
from proton.vpn.core_api import vpn_logging as logging
from proton.vpn.app.gtk import utils


logger = logging.getLogger(__name__)


@dataclass
class ServerListWidgetState:
    """Class to hold the state of the ServerListWidget."""
    # List of servers to be displayed
    server_list: ServerList = None
    # Last time the server list was updated
    last_update_time: int = 0
    # ID of the GTK Source which reloads the server list periodically
    reload_servers_source_id: int = None
    # Row of the country we are connected to.
    connected_country_row: CountryRow = None
    # Country rows indexed by country code.
    country_rows: Dict[str, CountryRow] = field(default_factory=dict)
    # Flag signaling when the widget finished loading
    widget_loaded: bool = False

    def get_server_by_name(self, server_name: str) -> LogicalServer:
        """Returns the server with the given name."""
        if self.server_list:
            return self.server_list.get_by_name(server_name)
        return None

    @property
    def connected_server_id(self) -> Optional[str]:
        """Returns the ID of the server the user is currently connected.
        If the user didn't connect yet to a server, then it returns None."""
        return self.connected_country_row.connected_server_id \
            if self.connected_country_row else None


class ServerListWidget(Gtk.ScrolledWindow):
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
        self._state = ServerListWidgetState(
            server_list=server_list,
            last_update_time=server_list.loads_update_timestamp if server_list else 0,
        )

        if self._state.server_list:
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
        return list(self._state.country_rows.values())

    def retrieve_servers(self) -> Future:
        """
        Requests the list of servers. Note that a remote API call is only
        triggered if the server list cache expired.
        :return: A future wrapping the server list.
        """
        logger.debug("Retrieving servers", category="APP", subcategory="SERVERS", event="RETRIEVE")
        future = self._controller.get_server_list()
        if not self.country_rows:
            self._show_loading()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_servers_retrieved, future)
        )
        return future

    def start_reloading_servers_periodically(self):
        """Schedules retrieve_servers to be called periodically according
        to ServerListWidget.RELOAD_INTERVAL_IN_SECONDS."""
        self.retrieve_servers()
        self._state.reload_servers_source_id = GLib.timeout_add(
            interval=self.RELOAD_INTERVAL_IN_SECONDS * 1000,
            function=self.retrieve_servers
        )

    def stop_reloading_servers_periodically(self):
        """Stops the periodic calls to retrieve_servers."""
        if self._state.reload_servers_source_id is not None:
            GLib.source_remove(self._state.reload_servers_source_id)
            self._state.reload_servers_source_id = None
        else:
            logger.info(msg="Servers are not being reloaded periodically. "
                        "There is nothing to do.",
                        category="APP", subcategory="SERVERS", event="RELOAD")

    def connection_status_update(self, connection_status, vpn_server: VPNServer):
        """
        This method is called by VPNWidget whenever the VPN connection status changes.
        Important: as this method is always called from another thread, we need
        to make sure that any resulting actions are passed to the main thread
        running GLib's main loop with GLib.idle_add.
        """
        def update_server_rows():
            if self._state.widget_loaded and vpn_server:
                country_row = self._get_country_row(vpn_server)
                country_row.connection_status_update(connection_status, vpn_server)

                if connection_status.state == ConnectionStateEnum.CONNECTED:
                    self._state.connected_country_row = country_row
                elif connection_status.state == ConnectionStateEnum.DISCONNECTED:
                    self._state.connected_country_row = None

        GLib.idle_add(update_server_rows)

    def reset(self):
        """Resets the widget state."""
        self.stop_reloading_servers_periodically()
        self._remove_all_servers()
        self._state = ServerListWidgetState()

    def _on_realize(self, _servers_widget: ServerListWidget):
        self.start_reloading_servers_periodically()

    def _on_unrealize(self, _servers_widget: ServerListWidget):
        self.reset()

    def _remove_all_servers(self):
        for row in self._container.get_children():
            self._container.remove(row)
            row.destroy()
        self._state.country_rows = {}

    def _show_loading(self):
        self._remove_all_servers()
        self._container.pack_start(
            Gtk.Label(label="Loading..."),
            expand=False, fill=False, padding=5
        )
        self._container.show_all()

    def _is_server_list_outdated(self, new_server_list: ServerList):
        new_timestamp = new_server_list.loads_update_timestamp
        return self._state.last_update_time < new_timestamp

    def _on_servers_retrieved(self, future_server_list: Future):
        new_server_list = future_server_list.result()
        if self._is_server_list_outdated(new_server_list):
            self._state.last_update_time = new_server_list.loads_update_timestamp
            self._state.server_list = new_server_list
            self._show_servers()
        else:
            logger.debug(
                "Skipping server list reload because it's already up to date.",
                category="APP", subcategory="SERVERS", event="RELOAD"
            )

    def _show_servers(self):
        old_country_rows = self._state.country_rows
        self._remove_all_servers()
        self._add_all_servers(old_country_rows)

        self._container.show_all()
        self._state.widget_loaded = True
        self.emit("server-list-updated")
        logger.info("Server list updated.", category="APP", subcategory="SERVERS", event="RELOAD")

    def _add_all_servers(self, old_country_rows: Dict[str, CountryRow]):
        sorting_key = get_server_list_sorting_key_function(self._controller.user_tier)

        self._state.server_list.sort(key=sorting_key)

        def grouping_key(server: LogicalServer):
            return server.exit_country.lower()

        country_rows = []
        for country_code, country_servers in groupby(self._state.server_list, grouping_key):
            show_country_servers = False
            if old_country_rows and old_country_rows.get(country_code):
                show_country_servers = old_country_rows[country_code].showing_servers

            country_row = CountryRow(
                country_code=country_code,
                country_servers=list(country_servers),
                controller=self._controller,
                connected_server_id=self._state.connected_server_id,
                show_country_servers=show_country_servers
            )
            country_rows.append(country_row)
            self._state.country_rows[country_code.lower()] = country_row

        if self._controller.user_tier == 0:
            # If the current user has a free account, show the countries having
            # free servers first.
            country_rows.sort(
                key=free_countries_first_sorting_key
            )

        for country_number, country_row in enumerate(country_rows):
            self._container.pack_start(
                country_row,
                expand=False, fill=False, padding=0
            )
            if country_number < len(country_rows) - 1:
                separator = Gtk.Separator()
                separator.set_margin_bottom(10)
                self._container.pack_start(
                    separator,
                    expand=False, fill=False, padding=0
                )

    def _get_country_row(self, vpn_server) -> CountryRow:
        logical_server = self._state.get_server_by_name(vpn_server.servername)
        country_code = logical_server.exit_country.lower()
        try:
            return self._state.country_rows[country_code]
        except KeyError as error:
            raise RuntimeError(
                f"Unable to get country row {country_code} for server "
                f"{vpn_server.servername}."
            ) from error


def get_server_list_sorting_key_function(user_tier: int) -> Callable:
    """
    Returns the key function to be able to sort the server list.

    Usage:

    .. code-block:: python
        sort_key_func = get_server_list_sort_key_func(user_tier)
        server_list.sort(key=sort_key_func)

    This key sorts servers by the following fields in the following order:
        1) Country name. That is, the full name of the exit country of the
        server in ascending order.
        2) Server tier:
            a) In ascending order for free users. That is, first free servers
            (tier 0), then the ones in the tier above and so on.
            b) In descending order for paid users. That is, first the servers
            in the user tier, then the ones on the tier below and so on.
        3) Secure core. Servers without the secure core feature are sorted
        before servers having such feature.
        4) Server name. If the server name is in the form of COUNTRY_CODE#NUMBER,
        the number is padded with zeros to be able to sort it alphabetically
        in ascending order.

    This sorting schema has 2 goals:
        1) Sorting the servers by country so that afterwards we can easily
        group them by country.
        2) Sorting the servers *in each country* according to the business
        requirements mentioned above.

    Note however that, after grouping the servers into country groups,
    another sorting schema may be required to sort the country groups
    themselves according to business requirements (for example, users in
    the free tier should see countries having free servers first).

    :param user_tier: The user tier to use when sorting the servers in a country.
    :returns: The function used to generate the comparison key to sort each
    server in the list.
    """
    def sorting_key(server: LogicalServer):
        country_name = utils.get_country_name_by_code(server.exit_country)

        if user_tier == 0:
            # Free users (tier 0) see country servers ordered by server tier
            # in ascending order: 0 (free servers), 2 (plus servers)
            tier_priority = server.tier
        else:
            # Paid users see country servers ordered by server tier but in
            # descending order: 3 (employee servers), 2 (plus servers),
            # 0 (free servers)
            tier_priority = user_tier - server.tier

        # Severs without secure core are shown before servers with secure core
        secure_core_priority = 1 if ServerFeatureEnum.SECURE_CORE in server.features else 0

        server_name = server.name or ""
        server_name = server_name.lower()
        if "#" in server_name:
            # Pad server number with zeros to sort servers alphabetically
            server_name = f"{server_name.split('#')[0]}#" \
                          f"{server_name.split('#')[1].zfill(10)}"

        return f"{country_name}__{tier_priority}__{secure_core_priority}__{server_name}"

    return sorting_key


def free_countries_first_sorting_key(row: CountryRow):
    """
    Returns the comparison key to sort countries according to
    business rules for free users.

    Apart from sorting country rows by country name, free users should
    have countries having free servers sorted first.

    :param row: country row to generate the comparison key for.
    :return: The comparison key.
    """
    return f"{0 if row.is_free_country else 1}__{row.country_name}"
