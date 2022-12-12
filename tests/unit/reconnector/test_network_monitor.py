from unittest.mock import Mock

import pytest

import gi
gi.require_version("NM", "1.0")
from gi.repository import NM

from proton.vpn.app.gtk.widgets.vpn.reconnector.network_monitor import NetworkMonitor


def test_enable_connects_to_nm_client_state_changes():
    nm_client = Mock()
    monitor = NetworkMonitor(nm_client)

    monitor.enable()

    nm_client.connect.assert_called_once_with("notify::state", monitor._on_network_state_changed)


def test_disable_does_not_disconnect_from_nm_client_if_enabled_was_not_called_before():
    nm_client = Mock()
    monitor = NetworkMonitor(nm_client)

    monitor.disable()

    nm_client.disconnect.assert_not_called()


def test_disable_unhooks_monitor_from_network_manager_state_changes():
    nm_client = Mock()
    nm_client.connect.return_value = 23
    monitor = NetworkMonitor(nm_client)

    monitor.enable()
    monitor.disable()

    nm_client.disconnect.assert_called_once_with(23)


@pytest.mark.parametrize("nm_state,is_network_up", [
    (NM.State.CONNECTED_GLOBAL, True),
    (NM.State.CONNECTED_LOCAL, False)
])
def test_is_network_up_returns_true_if_network_manager_state_is_connected_global(
        nm_state, is_network_up
):
    nm_client = Mock()
    nm_client.get_state.return_value = nm_state
    monitor = NetworkMonitor(nm_client)

    monitor.is_network_up is is_network_up


def test_network_up_callback_is_called_once_network_manager_state_is_connected_global():
    nm_client = Mock()
    nm_client.get_state.return_value = NM.State.CONNECTED_GLOBAL
    monitor = NetworkMonitor(nm_client)
    monitor.network_up_callback = Mock()

    # Simulate NM notifying the monitor about a state change
    monitor._on_network_state_changed(nm_client, "state")

    monitor.network_up_callback.assert_called_once()
