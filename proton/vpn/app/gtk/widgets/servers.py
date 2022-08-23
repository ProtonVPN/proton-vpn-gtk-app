from __future__ import annotations

from concurrent.futures import Future
from typing import List

from gi.repository import GLib, GObject

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.servers.server_types import LogicalServer


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
    def __init__(self, controller: Controller):
        super().__init__()
        self._controller = controller
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self._container)
        self._servers = []

        self.connect("show", self._on_show)

    @GObject.Signal(name="server-list-ready")
    def server_list_ready(self):
        pass

    @property
    def server_rows(self) -> List[ServerRow]:
        return self._container.get_children()

    def _on_show(self, _servers_widget: ServersWidget):
        self.retrieve_servers()

    def retrieve_servers(self) -> Future:
        future = self._controller.get_server_list()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_servers_retrieved, future)
        )
        return future

    def _on_servers_retrieved(self, future: Future):
        server_list = future.result()

        def sorting_key(server: LogicalServer):
            if "#" not in server.name:
                return server.name
            else:
                return f"{server.name.split('#')[0]}{server.name.split('#')[1].zfill(5)}"

        self._servers = sorted(server_list, key=sorting_key)
        self._show_servers()

    def _show_servers(self):
        for server in self._servers:
            self._container.pack_start(
                ServerRow(server=server),
                expand=False, fill=False, padding=5
            )
        self._container.show_all()
        self.emit("server-list-ready")
