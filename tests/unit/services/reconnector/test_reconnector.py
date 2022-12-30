from unittest.mock import Mock, patch, PropertyMock

import pytest

from proton.vpn.connection import states
from proton.vpn.core_api.connection import VPNConnectionHolder

from proton.vpn.app.gtk.services.reconnector.network_monitor import NetworkMonitor
from proton.vpn.app.gtk.services.reconnector.reconnector import VPNReconnector
from proton.vpn.app.gtk.services.reconnector.session_monitor import SessionMonitor
from proton.vpn.app.gtk.services.reconnector.vpn_monitor import VPNMonitor


@pytest.fixture
def vpn_monitor():
    return Mock(VPNMonitor)


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


@pytest.mark.parametrize("did_vpn_drop, is_session_unlocked, reconnection_expected", [
    (False, False, False),
    (True, False, False),
    (False, True, False),
    (True, True, True)
])
def test_schedule_reconnection_is_called_once_network_connectivity_is_detected_only_if_vpn_connection_dropped_and_session_is_unlocked(
        did_vpn_drop, is_session_unlocked, reconnection_expected,
        vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    reconnector = VPNReconnector(
        vpn_connector, vpn_monitor, network_monitor, session_monitor
    )

    with patch.object(VPNReconnector, "did_vpn_drop", new_callable=PropertyMock) as did_vpn_drop_patch, \
            patch.object(VPNReconnector, "schedule_reconnection"):

        # Mock whether a VPN connection dropped happened or not
        did_vpn_drop_patch.return_value = did_vpn_drop

        session_monitor.is_session_unlocked = is_session_unlocked

        # Simulate network up.
        network_monitor.network_up_callback()

        assert reconnector.schedule_reconnection.called is reconnection_expected


@pytest.mark.parametrize("did_vpn_drop, is_network_up, reconnection_expected", [
    (False, False, False),
    (True, False, False),
    (False, True, False),
    (True, True, True)
])
def test_reconnect_is_called_once_user_session_is_unlocked_only_if_vpn_connection_dropped_and_network_is_up(
        did_vpn_drop, is_network_up, reconnection_expected,
        vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    reconnector = VPNReconnector(
        vpn_connector, vpn_monitor, network_monitor, session_monitor
    )

    with patch.object(VPNReconnector, "did_vpn_drop", new_callable=PropertyMock) as did_vpn_drop_patch, \
            patch.object(VPNReconnector, "schedule_reconnection"):
        # Mock whether a VPN connection dropped happened or not
        did_vpn_drop_patch.return_value = did_vpn_drop

        network_monitor.is_network_up = is_network_up

        # Simulate user session unlocked.
        session_monitor.session_unlocked_callback()

        assert reconnector.schedule_reconnection.called is reconnection_expected


@patch("proton.vpn.app.gtk.services.reconnector.reconnector.GLib")
def test_schedule_reconnection_only_schedule_a_reconnection_if_there_is_not_one_already_scheduled(
    glib_mock,
    vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    glib_mock.timeout_add_seconds.return_value = 1

    reconnector = VPNReconnector(
        vpn_connector, vpn_monitor, network_monitor, session_monitor
    )

    reconnection_scheduled = reconnector.schedule_reconnection()
    assert reconnection_scheduled
    glib_mock.timeout_add_seconds.assert_called_once()

    reconnection_scheduled = reconnector.schedule_reconnection()
    assert not reconnection_scheduled
    # assert that Glib was not called a second time.
    glib_mock.timeout_add_seconds.assert_called_once()


@patch("proton.vpn.app.gtk.services.reconnector.reconnector.GLib")
@patch("proton.vpn.app.gtk.services.reconnector.reconnector.VPNReconnector.did_vpn_drop")
def test_schedule_reconnection_attempt_to_reconnect_after_network_up_with_error(
    did_vpn_drop_mock, glib_mock,
    vpn_connector, vpn_monitor, network_monitor, session_monitor
):
    VPNReconnector(
        vpn_connector, vpn_monitor, network_monitor, session_monitor
    )

    glib_mock.timeout_add_seconds.return_value = 1
    did_vpn_drop_mock = True
    session_monitor.is_session_unlocked = True

    network_monitor.network_up_callback()
    glib_mock.timeout_add_seconds.call_count == 1

    num_of_reconnect_attempts = 1
    for num_attempts in range(0, 4):
        vpn_monitor.vpn_drop_callback()
        num_of_reconnect_attempts += 1

    glib_mock.timeout_add_seconds.call_count == num_of_reconnect_attempts
