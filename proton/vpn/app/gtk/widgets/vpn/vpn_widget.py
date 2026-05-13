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
from concurrent.futures import Future
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
import time

from gi.repository import GObject, GLib

from proton.vpn import logging

from proton.vpn.connection.states import State
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.vpn.quick_connect_widget import QuickConnectWidget
from proton.vpn.app.gtk.widgets.vpn.search_results import SearchResults
from proton.vpn.app.gtk.widgets.vpn.search_entry import SearchEntry
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.serverlist import ServerListWidget
from proton.vpn.app.gtk.widgets.vpn.connection_status_widget import VPNConnectionStatusWidget
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.session.servers import ServerList

if TYPE_CHECKING:
    from proton.vpn.app.gtk.app import MainWindow

logger = logging.getLogger(__name__)

# The feature flag that enables the lazy loading serverlist UI
LINUX_DEFERRED_UI = "LinuxDeferredUI"


@dataclass
class VPNWidgetState:
    """
    Holds the state of the VPNWidget. This state is reset after login/logout.

    Attributes:
        is_widget_ready: flag set to True once the widget has been initialized.
        user_tier: tier of the logged-in user.
        load_start_time: timestamp set when the widget starts loading.
    """
    is_widget_ready: bool = False
    user_tier: Optional[int] = None
    load_start_time: Optional[float] = None


# pylint: disable=too-many-instance-attributes
class VPNWidget(Gtk.Box):
    """Exposes the ProtonVPN product functionality to the user."""

    def __init__(
        self, controller: Controller,
        main_window: "MainWindow",
        notifications=Notifications
    ):
        super().__init__(spacing=10)

        self.set_name("vpn-widget")
        self._state = VPNWidgetState()
        self._state.load_start_time = time.time()
        self._controller = controller

        self.connection_status_widget = VPNConnectionStatusWidget(
            controller, notifications
        )
        self.append(self.connection_status_widget)

        self._connected_signals: list[tuple[int, Gtk.Widget]] = []

        self.quick_connect_widget = QuickConnectWidget(self._controller)
        self.append(self.quick_connect_widget)

        self.search_widget = SearchEntry()
        self.server_list_widget = ServerListWidget(self._controller, self.search_widget)
        self.append(self.server_list_widget)
        self._connected_signals.append((
            safe_signal_connect(
                self.server_list_widget, "ui-updated", self._on_server_list_updated
            ),
            self.server_list_widget
        ))
        main_window.add_keyboard_shortcut(
            target_widget=self.search_widget,
            target_signal="request_focus",
            shortcut="<Control>f"
        )
        self.search_results_widget = SearchResults(self._controller)
        revealer = Gtk.Revealer()
        revealer.set_child(self.search_results_widget)
        self.search_results_widget.set_revealer(revealer)

        self._connected_signals.append((
            safe_signal_connect(
                self.search_widget,
                "search-changed",
                self.search_results_widget.on_search_changed,
            ),
            self.search_widget
        ))
        self._connected_signals.append((
            safe_signal_connect(
                self.search_results_widget,
                "result-chosen",
                self.server_list_widget.focus_on_entry
            ),
            self.search_results_widget
        ))
        self._connected_signals.append((
            safe_signal_connect(
                self.search_results_widget,
                "result-chosen",
                self._reset_search_on_result_chosen
            ),
            self.search_results_widget
        ))
        self.insert_child_after(self.search_widget, self.quick_connect_widget)
        self.insert_child_after(revealer, self.search_widget)

        self._state_subscribers = [
            self.connection_status_widget,
            self.quick_connect_widget,
        ]

        signal_id = safe_signal_connect(
            self,
            "connection-state-changed",
            self._broadcast_connection_state
        )
        self._connected_signals.append((signal_id, self))

        self.set_orientation(Gtk.Orientation.VERTICAL)

        safe_signal_connect(self, "unrealize", self._on_unrealize)

    def _reset_search_on_result_chosen(self, *_) -> None:
        self.search_widget.reset()

    def _broadcast_connection_state(self, _, state):
        for widget in self._state_subscribers:
            widget.connection_status_update(state)

    @GObject.Signal
    def vpn_widget_ready(self):
        """Signal emitted when all resources were loaded and widget is ready."""

    @GObject.Signal(name="connection-state-changed", arg_types=(object,))
    def connection_state_changed(self, state: State):
        """Signal emitted whenever the VPN connection state changes."""

    @property
    def user_tier(self) -> int:
        """Returns the tier of the user currently logged in."""
        return self._state.user_tier

    def _on_unrealize(self, _widget):
        self.unload()

    def status_update(self, connection_state: State):
        """This method is called whenever the VPN connection status changes."""
        logger.debug(
            f"VPN widget received connection status update: "
            f"{type(connection_state).__name__}."
        )

        GLib.idle_add(self.emit, "connection-state-changed", connection_state)

    def _on_refresher_enabled(
            self,
            future: Future
    ):
        future.result()
        self.display(self._controller.user_tier, self._controller.server_list)

    def load(self):
        """
        Starts loading the widget.

        The call to this method triggers networks calls to Proton's REST API
        to download the required data to display the widget. Once the required
        data has been downloaded, the widget will be automatically displayed.
        """
        self._state.load_start_time = time.time()
        self._controller.enable_refresher(self._on_refresher_enabled)

    def display(self, user_tier: int, server_list: ServerList):
        """Displays the widget once all necessary data from API has been acquired."""
        self._state.user_tier = user_tier

        # The VPN widget subscribes to connection status updates, and then
        # passes on these connection status updates to child widgets
        self._controller.register_connection_status_subscriber(self)
        self._controller.reconnector.enable()

        # Apply the correct connection state immediately so there's no flash of
        # "Unprotected" when the app starts already connected.
        self.status_update(self._controller.current_connection_status)

        self.server_list_widget.display(user_tier=user_tier, server_list=server_list)

    def _on_server_list_updated(self, *_):
        if not self._state.is_widget_ready:  # noqa: E501 # pylint: disable=line-too-long # nosemgrep: python.lang.maintainability.is-function-without-parentheses.is-function-without-parentheses
            # Only update the status at this point as widgets are already generated
            self.status_update(self._controller.current_connection_status)
            self._state.is_widget_ready = True  # noqa: E501 # pylint: disable=line-too-long # nosemgrep: python.lang.maintainability.is-function-without-parentheses.is-function-without-parentheses
            self.emit("vpn-widget-ready")
            logger.info(
                f"VPN widget is ready "
                f"(load time: {time.time()-self._state.load_start_time:.2f} seconds)",
                category="app", subcategory="vpn", event="widget_ready"
            )

    def unload(self):
        """Unloads the widget and resets its state."""
        for signal_id, widget in self._connected_signals:
            widget.disconnect(signal_id)
        self._connected_signals.clear()
        self._controller.disconnect()

        self._controller.unregister_connection_status_subscriber(self)
        self._controller.reconnector.disable()
        self._controller.disable_refresher()

        for widget in [
            self.connection_status_widget,
            self.quick_connect_widget, self.server_list_widget
        ]:
            widget.set_visible(False)

        # Reset widget state
        self._state = VPNWidgetState()
