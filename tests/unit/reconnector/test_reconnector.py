from unittest.mock import Mock, patch, PropertyMock

import pytest

from proton.vpn.connection import events, states
from proton.vpn.connection.events import EVENT_TYPES
from proton.vpn.core_api.connection import VPNConnectionHolder

from proton.vpn.app.gtk.widgets.vpn.reconnector.network_monitor import NetworkMonitor
from proton.vpn.app.gtk.widgets.vpn.reconnector.reconnector import VPNReconnector
from proton.vpn.app.gtk.widgets.vpn.reconnector.session_monitor import SessionMonitor


@pytest.fixture
def vpn_monitor():
    return Mock()


@pytest.fixture
def network_monitor():
    return Mock(NetworkMonitor)


@pytest.fixture
def session_monitor():
    return Mock(SessionMonitor)


@pytest.fixture
def vpn_connector():
    return Mock(VPNConnectionHolder)


def test_enable_enables_vpn_and_network_and_session_monitors(
        vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    reconnector = VPNReconnector(vpn_connector, vpn_monitor, network_monitor, session_monitor)

    reconnector.enable()

    vpn_monitor.enable.assert_called_once()
    network_monitor.enable.assert_called_once()
    session_monitor.enable.assert_called_once()


def test_disable_disables_vpn_and_network_and_session_monitors(
        vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    reconnector = VPNReconnector(vpn_connector, vpn_monitor, network_monitor, session_monitor)

    reconnector.disable()

    vpn_monitor.disable.assert_called_once()
    network_monitor.disable.assert_called_once()
    session_monitor.disable.assert_called_once()


def test_did_vpn_drop_returns_false_if_there_is_not_a_vpn_connection(
        vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    vpn_connector.current_connection = None
    reconnector = VPNReconnector(vpn_connector, vpn_monitor, network_monitor, session_monitor)

    assert not reconnector.did_vpn_drop


@pytest.mark.parametrize("state", [
    state() for state in states.BaseState.__subclasses__()
])
def test_did_vpn_drop_returns_true_only_if_the_current_connection_state_is_error(
        state,
        vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    vpn_connector.current_connection.status = state
    reconnector = VPNReconnector(vpn_connector, vpn_monitor, network_monitor, session_monitor)

    expected_result = isinstance(state, states.Error)
    assert reconnector.did_vpn_drop is expected_result


@pytest.mark.parametrize(
    "current_connection_exists,is_session_unlocked,is_network_up,expected_result", [
        (False, False, False, False),
        (True, False, False, False),
        (True, True, False, False),
        (True, True, True, True)
    ]
)
def test_is_reconnection_possible(
        current_connection_exists, is_session_unlocked, is_network_up, expected_result,
        vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    if not current_connection_exists:
        vpn_connector.current_connection = None

    session_monitor.is_session_unlocked = is_session_unlocked
    network_monitor.is_network_up = is_network_up

    reconnector = VPNReconnector(vpn_connector, vpn_monitor, network_monitor, session_monitor)

    assert reconnector.is_reconnection_possible == expected_result


@pytest.mark.parametrize("did_vpn_drop, reconnection_expected", [
    (False, False),
    (True, True)
])
def test_reconnect_is_called_once_network_connectivity_is_detected_only_if_vpn_connection_dropped(
        did_vpn_drop, reconnection_expected,
        vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    reconnector = VPNReconnector(
        vpn_connector, vpn_monitor, network_monitor, session_monitor
    )

    with patch.object(VPNReconnector, "did_vpn_drop", new_callable=PropertyMock) as did_vpn_drop_patch, \
         patch.object(VPNReconnector, "reconnect"):
        # Mock whether a VPN connection dropped happened or not
        did_vpn_drop_patch.return_value = did_vpn_drop

        # Simulate network up.
        network_monitor.network_up_callback()

        assert reconnector.reconnect.called is reconnection_expected


@pytest.mark.parametrize("did_vpn_drop, reconnection_expected", [
    (False, False),
    (True, True)
])
def test_reconnect_is_called_once_user_session_is_unlocked_only_if_vpn_connection_dropped(
        did_vpn_drop, reconnection_expected,
        vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    reconnector = VPNReconnector(
        vpn_connector, vpn_monitor, network_monitor, session_monitor
    )

    with patch.object(VPNReconnector, "did_vpn_drop", new_callable=PropertyMock) as did_vpn_drop_patch, \
            patch.object(VPNReconnector, "reconnect"):
        # Mock whether a VPN connection dropped happened or not
        did_vpn_drop_patch.return_value = did_vpn_drop

        # Simulate user session unlocked.
        session_monitor.session_unlocked_callback()

        assert reconnector.reconnect.called is reconnection_expected


@pytest.mark.parametrize(
    "event_type", EVENT_TYPES
)
def test_reconnect_currently_only_reconnects_on_device_disconnected_and_timeout_events(
    event_type,
    vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    # Mock current connection's last event.
    vpn_connector.current_connection.status.context.event = event_type()

    reconnector = VPNReconnector(
        vpn_connector, vpn_monitor, network_monitor, session_monitor
    )

    reconnector.reconnect()

    # Reconnection currently should only happen on these events:
    connection_expected = event_type in (events.DeviceDisconnected, events.Timeout)
    assert vpn_connector.connect.called == connection_expected
