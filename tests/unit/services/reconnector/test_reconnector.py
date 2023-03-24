from unittest.mock import Mock, patch, PropertyMock

import pytest

from proton.vpn.connection import states
from proton.vpn.core_api.connection import VPNConnectorWrapper

from proton.vpn.app.gtk.services import VPNDataRefresher
from proton.vpn.app.gtk.services.reconnector.network_monitor import NetworkMonitor
from proton.vpn.app.gtk.services.reconnector.reconnector import VPNReconnector
from proton.vpn.app.gtk.services.reconnector.session_monitor import SessionMonitor
from proton.vpn.app.gtk.services.reconnector.vpn_monitor import VPNMonitor


@pytest.fixture
def vpn_connector():
    return Mock(VPNConnectorWrapper)


@pytest.fixture
def vpn_data_refresher():
    return Mock(VPNDataRefresher)


@pytest.fixture
def vpn_monitor():
    return Mock(VPNMonitor)


@pytest.fixture
def network_monitor():
    return Mock(NetworkMonitor)


@pytest.fixture
def session_monitor():
    return Mock(SessionMonitor)


def test_enable_enables_vpn_and_network_and_session_monitors(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
):
    reconnector = VPNReconnector(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
    )

    reconnector.enable()

    vpn_monitor.enable.assert_called_once()
    network_monitor.enable.assert_called_once()
    session_monitor.enable.assert_called_once()


def test_enable_raises_runtime_error_if_vpn_data_refresher_is_not_ready(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
):
    """
    The reconnector retrieves the server list and the client configuration
    required to initiate a reconnection from its VPNDataRefresher instance.
    For this reason, it cannot be enabled if the VPNDataRefresher is not
    ready. That is, the VPNDataRefresher did not retrieve the server list
    and/or the client configuration yet.
    """
    reconnector = VPNReconnector(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
    )

    vpn_data_refresher.is_vpn_data_ready = False

    with pytest.raises(RuntimeError):
        reconnector.enable()


def test_disable_disables_vpn_and_network_and_session_monitors(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
):
    reconnector = VPNReconnector(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
    )

    reconnector.disable()

    vpn_monitor.disable.assert_called_once()
    network_monitor.disable.assert_called_once()
    session_monitor.disable.assert_called_once()


def test_did_vpn_drop_returns_false_if_there_is_not_a_vpn_connection(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
):
    vpn_connector.current_connection = None
    reconnector = VPNReconnector(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
    )

    assert not reconnector.did_vpn_drop


@pytest.mark.parametrize("state", [
    state() for state in states.State.__subclasses__()
])
def test_did_vpn_drop_returns_true_only_if_the_current_connection_state_is_error(
        state,
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
):
    vpn_connector.current_state = state
    reconnector = VPNReconnector(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
    )

    expected_result = isinstance(state, states.Error)
    assert reconnector.did_vpn_drop is expected_result


@pytest.mark.parametrize("did_vpn_drop, scheduled_reconnection_expected", [
    (False, False),
    (True, True)
])
def test_schedule_reconnection_is_called_once_network_connectivity_is_detected_only_if_vpn_connection_dropped(
        did_vpn_drop, scheduled_reconnection_expected,
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
):
    reconnector = VPNReconnector(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
    )

    with patch.object(VPNReconnector, "did_vpn_drop", new_callable=PropertyMock) as did_vpn_drop_patch, \
            patch.object(VPNReconnector, "schedule_reconnection"):
        # Mock whether a VPN connection dropped happened or not
        did_vpn_drop_patch.return_value = did_vpn_drop

        # Simulate network up.
        network_monitor.network_up_callback()

        assert reconnector.schedule_reconnection.called is scheduled_reconnection_expected


@pytest.mark.parametrize("did_vpn_drop, scheduled_reconnection_expected", [
    (False, False),
    (True, True)
])
def test_schedule_reconnection_is_called_once_user_session_is_unlocked_only_if_vpn_connection_dropped(
        did_vpn_drop, scheduled_reconnection_expected,
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
):
    reconnector = VPNReconnector(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
    )

    with patch.object(VPNReconnector, "did_vpn_drop", new_callable=PropertyMock) as did_vpn_drop_patch, \
            patch.object(VPNReconnector, "schedule_reconnection"):
        # Mock whether a VPN connection dropped happened or not
        did_vpn_drop_patch.return_value = did_vpn_drop

        # Simulate user session unlocked.
        session_monitor.session_unlocked_callback()

        assert reconnector.schedule_reconnection.called is scheduled_reconnection_expected


@patch("proton.vpn.app.gtk.services.reconnector.reconnector.GLib")
def test_schedule_reconnection_only_schedule_a_reconnection_if_there_is_not_one_already_scheduled(
    glib_mock,
    vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
):
    glib_mock.timeout_add_seconds.return_value = 1

    reconnector = VPNReconnector(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
    )

    reconnection_scheduled = reconnector.schedule_reconnection()
    assert reconnection_scheduled
    glib_mock.timeout_add.assert_called_once()

    reconnection_scheduled = reconnector.schedule_reconnection()
    assert not reconnection_scheduled
    # assert that Glib was not called a second time.
    glib_mock.timeout_add.assert_called_once()


@patch("proton.vpn.app.gtk.services.reconnector.reconnector.random")
@patch("proton.vpn.app.gtk.services.reconnector.reconnector.GLib")
def test_on_vpn_drop_a_reconnection_attempt_is_scheduled_with_an_exponential_backoff_delay(
    glib_mock, random_mock,
    vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
):
    """After each reconnection attempt, the backoff delay should increase
    exponentially."""
    VPNReconnector(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
    )

    glib_mock.timeout_add_seconds.return_value = 1
    random_mock.uniform.return_value = 1  # Get rid of randomness.

    for number_of_attempts in range(4):
        vpn_monitor.vpn_drop_callback()  # Simulate VPN drop.

        glib_mock.timeout_add.assert_called_once()
        delay_in_ms, reconnect_func = glib_mock.timeout_add.call_args_list[0].args

        # Assert that the backoff delay increases as expected after each reconnection attempt.
        expected_delay_in_ms = 2**number_of_attempts * 1000
        assert delay_in_ms == expected_delay_in_ms, \
            f"On reconnection attempt number {number_of_attempts} a " \
            f"backoff delay of {expected_delay_in_ms} ms was expected."

        # Simulate GLib running the scheduled reconnection attempt.
        reconnect_func()

        glib_mock.reset_mock()


@pytest.mark.parametrize("is_network_up,is_session_unlocked", [
    (True, False),
    (True, False),
    (False, False)
])
@patch("proton.vpn.app.gtk.services.reconnector.reconnector.random")
@patch("proton.vpn.app.gtk.services.reconnector.reconnector.GLib")
def test_reconnection_is_rescheduled_if_network_is_down_or_session_is_locked(
    glib_mock, random_mock,
    is_network_up, is_session_unlocked,
    vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
):
    """
    The requirements for a reconnection attempt are:
    1. that there is network connectivity and
    2. that the user session is unlocked (a requirement imposed by NM).
    If any of those requirements are not met, then the reconnection should not take place,
    and it should be rescheduled instead. This is what's tested by this test.
    """
    VPNReconnector(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
    )

    glib_mock.timeout_add_seconds.return_value = 1
    random_mock.uniform.return_value = 1  # Get rid of randomness.

    # Simulate VPN drop.
    vpn_monitor.vpn_drop_callback()

    # Make sure a reconnection attempt is scheduled.
    glib_mock.timeout_add.assert_called_once()
    delay_in_ms, reconnect_func = glib_mock.timeout_add.call_args_list[0].args
    assert delay_in_ms == 1000

    # Simulate network up/down.
    network_monitor.is_network_up = is_network_up
    # Simulate session [un]locked
    session_monitor.is_session_unlocked = is_session_unlocked

    # Simulate GLib running the scheduled reconnection attempt.
    reconnect_func()

    # Assert that the reconnection did not happen (as network is down and/or session is locked)
    vpn_connector.connect.assert_not_called()

    # Assert that a new reconnection attempt was scheduled with the expected delay
    assert glib_mock.timeout_add.call_count == 2
    delay_in_ms, reconnect_func = glib_mock.timeout_add.call_args_list[1].args
    assert delay_in_ms == 2000


@patch("proton.vpn.app.gtk.services.reconnector.reconnector.random")
@patch("proton.vpn.app.gtk.services.reconnector.reconnector.GLib")
def test_on_vpn_up_resets_retry_counter_and_removes_pending_scheduled_attempt(
        glib_mock, random_mock,
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
):
    """After the VPN connection has been restored, the retry counter that
    increases the backoff delay should be reset, and if there is a pending
    scheduled reconnection attempt then it should be unscheduled."""
    reconnector = VPNReconnector(
        vpn_connector, vpn_data_refresher, vpn_monitor, network_monitor, session_monitor
    )

    glib_mock.timeout_add_seconds.return_value = 1
    random_mock.uniform.return_value = 1  # Get rid of randomness.

    reconnector.schedule_reconnection()

    glib_mock.timeout_add.assert_called_once()
    delay_in_ms, reconnect_func = glib_mock.timeout_add.call_args_list[0].args

    # Simulate GLib running the scheduled reconnection attempt.
    reconnect_func()

    assert reconnector.retry_counter == 1

    # Schedule a pending reconnection attempt.
    reconnector.schedule_reconnection()

    assert reconnector.is_reconnection_scheduled

    vpn_monitor.vpn_up_callback()  # Simulate VPN up event.

    # Assert that the retry counter is reset
    assert reconnector.retry_counter == 0
    # and the pending scheduled connection has been unscheduled.
    assert not reconnector.is_reconnection_scheduled
