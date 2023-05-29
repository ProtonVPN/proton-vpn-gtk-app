"""
This module defines the VPN widget, which contains all the VPN functionality
that is shown to the user.


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
from dataclasses import dataclass
from typing import TYPE_CHECKING
import time

from gi.repository import GObject, GLib

from proton.vpn import logging

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.services import VPNDataRefresher
from proton.vpn.app.gtk.widgets.vpn.quick_connect_widget import QuickConnectWidget
from proton.vpn.app.gtk.widgets.vpn.serverlist.serverlist import ServerListWidget
from proton.vpn.app.gtk.widgets.vpn.search_entry import SearchEntry
from proton.vpn.app.gtk.widgets.vpn.connection_status_widget import VPNConnectionStatusWidget
from proton.vpn.core_api.client_config import ClientConfig
from proton.vpn.servers.list import ServerList

if TYPE_CHECKING:
    from proton.vpn.app.gtk.app import MainWindow

logger = logging.getLogger(__name__)


@dataclass
class VPNWidgetState:
    """
    Holds the state of the VPNWidget. This state is reset after login/logout.

    Attributes:
        is_widget_ready: flag set to True once the widget has been initialized.
        user_tier: tier of the logged-in user.
        vpn_data_ready_handler_id: handler id obtained when connecting to the
        vpn-data-ready signal on VPNDataRefresher.
        after VPN disconnection.
    """
    is_widget_ready: bool = False
    user_tier: int = None
    vpn_data_ready_handler_id: int = None
    load_start_time: int = None


# pylint: disable=too-many-instance-attributes
class VPNWidget(Gtk.Box):
    """Exposes the ProtonVPN product functionality to the user."""

    def __init__(self, controller: Controller, main_window: "MainWindow"):
        super().__init__(spacing=10)

        self.set_name("vpn-widget")
        self._state = VPNWidgetState()
        self._state.load_start_time = time.time()
        self._controller = controller

        self.connection_status_widget = VPNConnectionStatusWidget()
        self.pack_start(self.connection_status_widget, expand=False, fill=False, padding=0)

        self.quick_connect_widget = QuickConnectWidget(self._controller)
        self.pack_start(self.quick_connect_widget, expand=False, fill=False, padding=0)

        self.server_list_widget = ServerListWidget(self._controller)
        self.pack_end(self.server_list_widget, expand=True, fill=True, padding=0)
        self.server_list_widget.connect("ui-updated", self._on_server_list_updated)

        self.search_widget = SearchEntry(self.server_list_widget)
        main_window.add_keyboard_shortcut(
            target_widget=self.search_widget,
            target_signal="request_focus",
            shortcut="<Control>f"
        )
        self.pack_start(self.search_widget, expand=False, fill=True, padding=0)

        self.connection_status_subscribers = []
        for widget in [
            self.connection_status_widget,
            self.quick_connect_widget,
            self.server_list_widget
        ]:
            self.connection_status_subscribers.append(widget)

        self.set_orientation(Gtk.Orientation.VERTICAL)

        self.connect("unrealize", self._on_unrealize)

    @GObject.Signal
    def vpn_widget_ready(self):
        """Signal emitted when all resources were loaded and widget is ready."""

    @property
    def user_tier(self) -> int:
        """Returns the tier of the user currently logged in."""
        return self._state.user_tier

    def _on_unrealize(self, _widget):
        self.unload()

    def status_update(self, connection_state):
        """This method is called whenever the VPN connection status changes."""
        logger.debug(
            f"VPN widget received connection status update: "
            f"{type(connection_state).__name__}."
        )

        def update_widget():
            for widget in self.connection_status_subscribers:
                widget.connection_status_update(connection_state)

        GLib.idle_add(update_widget)

    def _on_vpn_data_ready(
            self,
            _vpn_data_refresher: VPNDataRefresher,
            server_list: ServerList,
            _client_config: ClientConfig
    ):
        if not self._state.is_widget_ready:
            self.display(self._state.user_tier, server_list)

    def load(self, user_tier: int):
        """
        Starts loading the widget.

        The call to this method triggers networks calls to Proton's REST API
        to download the required data to display the widget. Once the required
        data has been downloaded, the widget will be automatically displayed.
        """
        self._state.load_start_time = time.time()
        self._state.user_tier = user_tier
        self._state.vpn_data_ready_handler_id = self._controller.vpn_data_refresher.connect(
            "vpn-data-ready", self._on_vpn_data_ready
        )
        self._controller.vpn_data_refresher.enable()

    def display(self, user_tier: int, server_list: ServerList):
        """Displays the widget once all necessary data from API has been acquired."""
        self.show_all()

        # The VPN widget subscribes to connection status updates, and then
        # passes on these connection status updates to child widgets
        self._controller.register_connection_status_subscriber(self)
        self._controller.reconnector.enable()

        self.server_list_widget.display(user_tier=user_tier, server_list=server_list)

    def _on_server_list_updated(self, *_):
        if not self._state.is_widget_ready:
            # Only update the status at this point as widgets are already generated
            self.status_update(self._controller.current_connection_status)
            self._state.is_widget_ready = True
            self.emit("vpn-widget-ready")
            logger.info(
                f"VPN widget is ready "
                f"(load time: {time.time()-self._state.load_start_time:.2f} seconds)",
                category="app", subcategory="vpn", event="widget_ready"
            )

    def unload(self):
        """Unloads the widget and resets its state."""
        self._controller.disconnect()
        self._controller.vpn_data_refresher.disconnect(
            self._state.vpn_data_ready_handler_id
        )

        self._controller.unregister_connection_status_subscriber(self)
        self._controller.reconnector.disable()
        self._controller.vpn_data_refresher.disable()

        for widget in [
            self.connection_status_widget,
            self.quick_connect_widget, self.server_list_widget
        ]:
            widget.hide()

        # Reset widget state
        self._state = VPNWidgetState()
