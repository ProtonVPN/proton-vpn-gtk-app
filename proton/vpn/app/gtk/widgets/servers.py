"""
This module defines the widgets used to present the VPN server list to the user.
"""
from __future__ import annotations

import logging
from concurrent.futures import Future
from typing import List

from gi.repository import GLib, GObject

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.servers.server_types import LogicalServer
from proton.vpn.servers.list import ServerList
from proton.vpn.core_api.logger import logger


class ServerRow(Gtk.Box):
    """Displays a single server as a row in the server list."""
    def __init__(self, server: LogicalServer):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.server = server
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

        self._connect_button = None
        if self.server.enabled:
            self._connect_button = Gtk.Button(label="Connect")
            handler_id = self._connect_button.connect("clicked", self._on_connect_button_clicked)
            self.connect("destroy", lambda _: self._connect_button.disconnect(handler_id))
            self.pack_end(
                self._connect_button,
                expand=False, fill=False, padding=10
            )
        else:
            self.pack_end(
                Gtk.Label(label="(under maintenance)"),
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
        self.add(self._container)
        self._server_list = server_list
        self._last_update_time = server_list.loads_update_timestamp if server_list else 0
        self._reload_servers_source_id = None
        self._current_server = None

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
    def server_rows(self) -> List[ServerRow]:
        """Returns the list of server rows that are currently being displayed.
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

    def connection_status_update(self, connection_status, vpn_server):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        def update_server_rows():
            if vpn_server:
                self._current_server = self._get_server_row(vpn_server)
                self._current_server.connection_state = connection_status.state
            elif self._current_server \
                    and connection_status.state == ConnectionStateEnum.DISCONNECTED:
                self._current_server.connection_state = connection_status.state

        GLib.idle_add(update_server_rows)

    def _on_realize(self, _servers_widget: ServersWidget):
        self.start_reloading_servers_periodically()

    def _on_unrealize(self, _servers_widget: ServersWidget):
        self.stop_reloading_servers_periodically()

    def _remove_server_rows(self):
        for row in self._container.get_children():
            self._container.remove(row)
            row.destroy()

    def _show_loading(self):
        self._remove_server_rows()
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
        def sorting_key(server: LogicalServer):
            server_name = server.name

            if server_name is None:
                server_name = ""
            server_name = server_name.lower()

            if "#" not in server_name:
                return server_name.lower()

            return f"{server_name.split('#')[0]}" \
                   f"{server_name.split('#')[1].zfill(5)}"

        servers_sorted_alphabetically = sorted(self._server_list, key=sorting_key)

        self._remove_server_rows()
        for server in servers_sorted_alphabetically:
            server_row = ServerRow(server=server)

            if self._current_server and self._current_server.server.name == server.name:
                self._current_server = server_row
                server_row.connection_state = ConnectionStateEnum.CONNECTED

            self._container.pack_start(
                server_row,
                expand=False, fill=False, padding=5
            )
            server_row.connect("server-connection-request", self._on_server_connection_request)

        self._container.show_all()
        logger.info("Server list updated.", category="APP", subcategory="SERVERS", event="RELOAD")
        self.emit("server-list-updated")

    def _get_server_row(self, vpn_server):
        for row in self._container.get_children():
            if row.server.name == vpn_server.servername:
                return row
        return None

    def _on_server_connection_request(self, server_row: ServerRow):
        self._controller.connect(server_name=server_row.server.name)
