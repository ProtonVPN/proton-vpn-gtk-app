from __future__ import annotations

from concurrent.futures import Future

from gi.repository import GLib, GObject

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.servers import VPNServer


class ServerRow(Gtk.Box):
    def __init__(self, server: VPNServer):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self._server = server
        self.pack_start(
            Gtk.Label(label=server.name),
            expand=False, fill=False, padding=10
        )
        if not server.enabled:
            self.pack_start(
                Gtk.Label(label="(Under maintenance)"),
                expand=False, fill=False, padding=5
            )
        connect_button = Gtk.Button(label="Connect (WIP)")
        connect_button.set_sensitive(False)
        self.pack_end(
            connect_button,
            expand=False, fill=False, padding=10
        )


class ServersWidget(Gtk.ScrolledWindow):
    def __init__(self, controller: Controller):
        super().__init__()
        self._controller = controller
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._container.set_border_width(5)
        self.add(self._container)
        self._servers = []

        self.connect("show", self._on_show)

    @GObject.Signal(name="server-list-ready")
    def server_list_ready(self):
        pass

    def _on_show(self, _servers_widget: ServersWidget):
        self._retrieve_servers()

    def _retrieve_servers(self):
        future = self._controller.get_server_list()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_servers_retrieved, future)
        )

    def _on_servers_retrieved(self, future: Future):
        server_list = future.result()
        self._servers = sorted(
            server_list,
            key=lambda server: f"{server.name.split('#')[0]}"
                               f"{server.name.split('#')[1].zfill(5)}"
        )
        self._show_servers()

    def _show_servers(self):
        for server in self._servers:
            self._container.pack_start(
                ServerRow(server=server),
                expand=False, fill=False, padding=5
            )
        self._container.show_all()
        self.emit("server-list-ready")
