"""
This module defines the server widget.
"""

from gi.repository import GObject
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.servers.server_types import LogicalServer
from proton.vpn.app.gtk import Gtk
from proton.vpn.core_api import vpn_logging as logging


logger = logging.getLogger(__name__)


class ServerRow(Gtk.Box):
    """Displays a single server as a row in the server list."""
    def __init__(self, server: LogicalServer, user_tier: int):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.server = server
        self._user_tier = user_tier
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

        if self.under_maintenance:
            self.pack_end(
                Gtk.Label(label="(under maintenance)"),
                expand=False, fill=False, padding=10
            )
            return

        if self.upgrade_required:
            self._upgrade_button = Gtk.LinkButton.new_with_label("Upgrade")
            self._upgrade_button.set_uri("https://account.protonvpn.com/")
            _button_to_attach = self._upgrade_button
        else:
            self._connect_button = Gtk.Button(label="Connect")
            self._connect_button.set_sensitive(True)
            handler_id = self._connect_button.connect("clicked", self._on_connect_button_clicked)
            self.connect("destroy", lambda _: self._connect_button.disconnect(handler_id))
            _button_to_attach = self._connect_button

        self.pack_end(
            _button_to_attach,
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
    def upgrade_required(self) -> bool:
        """Returns if a plan upgrade is required to connect to server."""
        return self.server.tier > self._user_tier

    @property
    def server_label(self):
        """Returns the server label.
        This method was made available for tests."""
        return self._server_label.get_label()

    @property
    def under_maintenance(self):
        """Returns if the server is under maintenance."""
        return not self.server.enabled

    def click_connect_button(self):
        """Clicks the connect button.
        This method was made available for tests."""
        self._connect_button.clicked()
