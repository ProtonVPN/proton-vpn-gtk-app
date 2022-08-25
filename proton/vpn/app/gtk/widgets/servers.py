from __future__ import annotations

import logging
from concurrent.futures import Future
from typing import List

from gi.repository import GLib, GObject

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.servers.server_types import LogicalServer
from proton.vpn.servers.list import ServerList

logger = logging.getLogger(__name__)


class ServerRow(Gtk.Box):
    def __init__(self, server: LogicalServer):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self._server = server
        self._server_label = Gtk.Label(label=server.name)
        self.pack_start(
            self._server_label,
            expand=False, fill=False, padding=10
        )
        if not server.enabled:
            self._server_label.set_label(
                f"{self._server_label.get_label()} (under maintenance)"
            )
        connect_button = Gtk.Button(label="Connect (WIP)")
        connect_button.set_sensitive(False)
        self.pack_end(
            connect_button,
            expand=False, fill=False, padding=10
        )

    @property
    def server_label(self):
        return self._server_label.get_label()


class ServersWidget(Gtk.ScrolledWindow):
    RELOAD_INTERVAL_IN_SECONDS = 60

    def __init__(self, controller: Controller):
        super().__init__()
        self.set_policy(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self._controller = controller
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self._container)
        self._server_list = None
        self._last_update_time = 0
        self._reload_servers_source_id = None

        self.connect("realize", self._on_realize)
        self.connect("unrealize", self._on_unrealize)

    @GObject.Signal(name="server-list-updated")
    def server_list_updated(self):
        pass

    @property
    def server_rows(self) -> List[ServerRow]:
        return self._container.get_children()

    def retrieve_servers(self) -> Future:
        logger.debug("Retrieving servers...")
        future = self._controller.get_server_list()
        if not self._server_list:
            self._show_loading()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_servers_retrieved, future)
        )
        return future

    def start_reloading_servers_periodically(self):
        self.retrieve_servers()
        self._reload_servers_source_id = GLib.timeout_add(
            interval=self.RELOAD_INTERVAL_IN_SECONDS * 1000,
            function=self.retrieve_servers
        )

    def stop_reloading_servers_periodically(self):
        if self._reload_servers_source_id is not None:
            GLib.source_remove(self._reload_servers_source_id)
        else:
            logger.info("Servers are not being reloaded periodically. "
                        "There is nothing to do.")

    def _on_realize(self, _servers_widget: ServersWidget):
        self.start_reloading_servers_periodically()

    def _on_unrealize(self, _servers_widget: ServersWidget):
        self.stop_reloading_servers_periodically()

    def _reset_server_rows(self):
        for row in self._container.get_children():
            self._container.remove(row)
            row.destroy()

    def _show_loading(self):
        self._reset_server_rows()
        self._container.pack_start(
            Gtk.Label(label="Loading..."),
            expand=False, fill=False, padding=5
        )
        self._container.show_all()

    def _is_server_list_outdated(self, new_server_list: ServerList):
        new_timestamp = new_server_list.logicals_update_timestamp
        return self._last_update_time < new_timestamp

    def _on_servers_retrieved(self, future_server_list: Future):
        new_server_list = future_server_list.result()
        if self._is_server_list_outdated(new_server_list):
            self._last_update_time = new_server_list.logicals_update_timestamp
            self._server_list = new_server_list
            self._show_servers()
        else:
            logger.debug("Skipping server list reload because it's already up to date.")

    def _show_servers(self):
        def sorting_key(server: LogicalServer):
            server_name = server.name

            if server_name is None:
                server_name = ""
            server_name = server_name.lower()

            if "#" not in server_name:
                return server_name.lower()
            else:
                return f"{server_name.split('#')[0]}" \
                       f"{server_name.split('#')[1].zfill(5)}"

        servers_sorted_alphabetically = sorted(self._server_list, key=sorting_key)

        self._reset_server_rows()
        for server in servers_sorted_alphabetically:
            server = ServerRow(server=server)
            self._container.pack_start(
                server,
                expand=False, fill=False, padding=5
            )
        self._container.show_all()

        logger.info("Server list updated.")

        self.emit("server-list-updated")
