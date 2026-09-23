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


Demo factories for the connection status widget, per plan and connection state.
"""
from unittest.mock import Mock

from proton.vpn.connection import states
from proton.vpn.session.servers import ServerList, TierEnum

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo.registry import register_demo
from proton.vpn.app.gtk.demo.mocks import mock_controller
from proton.vpn.app.gtk.demo.framing import framed_like_app
from proton.vpn.app.gtk.widgets.vpn.connection_status_widget import (
    VPNConnectionStatusWidget,
)

# The cities only surface in the connected state, which shows "{city} - {server}".
FREE_COUNTRY_CITIES = [
    ("US", "New York"), ("JP", "Tokyo"), ("PL", "Warsaw"),
    ("NL", "Amsterdam"), ("RO", "Bucharest"), ("MX", "Mexico City"),
    ("SG", "Singapore"), ("CA", "Toronto"), ("NO", "Oslo"),
    ("CH", "Zurich"),
]


def _server_list() -> ServerList:
    """A server list with one free server per free-tier country."""
    return ServerList.from_dict({
        "MaxTier": TierEnum.PLUS.value,
        "LogicalServers": [
            {
                "ID": index,
                "Name": f"{country_code}#1",
                "Status": 1,
                "Load": 20,
                "Servers": [{"Status": 1}],
                "ExitCountry": country_code,
                "City": city,
                "Tier": TierEnum.FREE.value,
            }
            for index, (country_code, city) in enumerate(FREE_COUNTRY_CITIES)
        ],
    })


def _controller(user_tier: TierEnum):
    """A controller reporting the given plan."""
    controller = mock_controller()
    controller.user_logged_in = True
    controller.user_tier = user_tier
    controller.server_selection_requires_upgrade = user_tier == TierEnum.FREE
    controller.server_list = _server_list()
    # Suppress the split-tunneling and protocol notifications.
    controller.get_setting_attr.return_value = False
    controller.feature_flags.get.return_value = False
    return controller


def _connection_status(state: states.State, user_tier: TierEnum):
    widget = VPNConnectionStatusWidget(_controller(user_tier), Mock())
    widget.connection_status_update(state)
    return framed_like_app(widget, fill_height=False, state=state)


def _disconnected() -> states.Disconnected:
    state = states.Disconnected()
    state.context.reconnection = False
    state.context.connection = None
    return state


@register_demo("connection-status", label="disconnected-free")
def connection_status_disconnected_free() -> Gtk.Widget:
    """Free tier: the "Auto-selected from" summary."""
    return _connection_status(_disconnected(), TierEnum.FREE)


@register_demo("connection-status", label="disconnected-paid")
def connection_status_disconnected_paid() -> Gtk.Widget:
    """Paid tier: no free-countries summary at all."""
    return _connection_status(_disconnected(), TierEnum.PLUS)


@register_demo("connection-status", label="connected")
def connection_status_connected() -> Gtk.Widget:
    """Connected state"""
    state = states.Connected()
    state.context.reconnection = False
    state.context.connection = Mock(server_name="CH#1")
    return _connection_status(state, TierEnum.FREE)
