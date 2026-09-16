"""
Copyright (c) 2026 Proton AG

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


Demo factories for the quick-connect widget — one labelled group per
connection state.
"""
from proton.vpn.connection import states

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo.registry import register_demo
from proton.vpn.app.gtk.demo.mocks import mock_controller
from proton.vpn.app.gtk.demo.framing import framed_like_app
from proton.vpn.app.gtk.widgets.vpn.quick_connect_widget import QuickConnectWidget


def _quick_connect(state: states.State) -> Gtk.Widget:
    widget = QuickConnectWidget(mock_controller())
    widget.connection_status_update(state)
    # In the app the widget is a band within the MainWindow's column (it doesn't
    # fill the height), so frame it at that width with its natural height.
    return framed_like_app(widget, fill_height=False)


@register_demo("quick-connect", label="disconnected")
def quick_connect_disconnected() -> Gtk.Widget:
    """Quick-connect widget while disconnected."""
    return _quick_connect(states.Disconnected())


@register_demo("quick-connect", label="connecting")
def quick_connect_connecting() -> Gtk.Widget:
    """Quick-connect widget while connecting."""
    return _quick_connect(states.Connecting())


@register_demo("quick-connect", label="connected")
def quick_connect_connected() -> Gtk.Widget:
    """Quick-connect widget while connected."""
    return _quick_connect(states.Connected())


@register_demo("quick-connect", label="error")
def quick_connect_error() -> Gtk.Widget:
    """Quick-connect widget in the error state."""
    return _quick_connect(states.Error())


def _cooling_down(server_changes: int) -> Gtk.Widget:
    """Quick-connect widget after the given number of server changes."""
    controller = mock_controller()
    controller.server_selection_requires_upgrade = True
    # The cooldown does arithmetic with these, so they cannot stay mocks.
    controller.client_config.change_server_attempt_limit = 4
    controller.client_config.change_server_short_delay_sec = 90
    controller.client_config.change_server_long_delay_sec = 1200

    widget = QuickConnectWidget(controller)
    for _ in range(server_changes):
        widget.change_server_button.emit("clicked")
        widget.connection_status_update(states.Connected())

    return framed_like_app(widget, fill_height=False)


@register_demo("quick-connect", label="cooling-down-short")
def quick_connect_cooling_down_short() -> Gtk.Widget:
    """Quick-connect widget during the short cooldown after a server change."""
    return _cooling_down(server_changes=1)


@register_demo("quick-connect", label="cooling-down-long")
def quick_connect_cooling_down_long() -> Gtk.Widget:
    """Quick-connect widget during the long cooldown, once the limit is reached."""
    return _cooling_down(server_changes=4)
