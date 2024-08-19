"""
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
from unittest.mock import Mock, patch

import pytest

from proton.vpn.connection import states
from proton.vpn.core.connection import VPNConnector

from proton.vpn.app.gtk.services.reconnector.vpn_monitor import VPNMonitor


def test_enable_registers_monitor_to_connection_state_updated():
    vpn_connector = Mock(VPNConnector)
    monitor = VPNMonitor(vpn_connector)

    monitor.enable()

    vpn_connector.register.assert_called_once()


def test_disable_unregisters_monitor_from_connection_state_updates():
    vpn_connector = Mock(VPNConnector)
    monitor = VPNMonitor(vpn_connector)

    monitor.disable()

    vpn_connector.unregister.assert_called_once()


@pytest.mark.parametrize("state,vpn_drop_callback_called", [
    (states.Disconnected(), False),
    (states.Connecting(), False),
    (states.Connected(), False),
    (states.Disconnected(), False),
    (states.Error(), True)
])
@patch("proton.vpn.app.gtk.services.reconnector.vpn_monitor.GLib")
def test_status_update_only_triggers_vpn_drop_callback_on_error_connection_state(
        glib_mock, state, vpn_drop_callback_called
):
    vpn_connector = Mock(VPNConnector)
    monitor = VPNMonitor(vpn_connector)
    monitor.vpn_drop_callback = Mock()

    event = state.context.event
    monitor.status_update(state)

    if vpn_drop_callback_called:
        glib_mock.idle_add.assert_called_with(monitor.vpn_drop_callback, event)
    else:
        glib_mock.idle_add.assert_not_called()


@pytest.mark.parametrize("state,vpn_up_callback_called", [
    (states.Disconnected(), False),
    (states.Connecting(), False),
    (states.Connected(), True),
    (states.Disconnected(), False),
    (states.Error(), False)
])
@patch("proton.vpn.app.gtk.services.reconnector.vpn_monitor.GLib")
def test_status_update_only_triggers_vpn_up_callback_on_connected_connection_state(
        glib_mock, state, vpn_up_callback_called
):
    vpn_connector = Mock(VPNConnector)
    monitor = VPNMonitor(vpn_connector)
    monitor.vpn_up_callback = Mock()

    monitor.status_update(state)

    if vpn_up_callback_called:
        glib_mock.idle_add.assert_called_with(monitor.vpn_up_callback)
    else:
        glib_mock.idle_add.assert_not_called()


def test_status_update_does_not_fail_when_callbacks_were_not_set():
    pass
