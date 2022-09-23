"""
This module defines the widgets used to present the VPN server list to the user.
"""
from __future__ import annotations

from concurrent.futures import Future
from itertools import groupby
from typing import List

from gi.repository import GLib, GObject

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.country import CountryRow
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.servers.server_types import LogicalServer
from proton.vpn.servers.list import ServerList, VPNServer
from proton.vpn.core_api import vpn_logging as logging
from proton.vpn.app.gtk.widgets.vpn.server import ServerRow
from proton.vpn.app.gtk import utils


logger = logging.getLogger(__name__)


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
        to ServerListWidget.RELOAD_INTERVAL_IN_SECONDS."""
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

    def _on_realize(self, _servers_widget: ServerListWidget):
        self.start_reloading_servers_periodically()

    def _on_unrealize(self, _servers_widget: ServerListWidget):
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

            country_name = utils.get_country_name_by_code(server.exit_country)

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
