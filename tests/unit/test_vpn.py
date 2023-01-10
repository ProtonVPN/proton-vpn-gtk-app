import time
from concurrent.futures import Future
from unittest.mock import Mock, patch
from threading import Event

import pytest

from proton.vpn.servers.list import ServerList
from proton.vpn.core_api.client_config import DEFAULT_CLIENT_CONFIG, ClientConfig

from proton.vpn.app.gtk.services import VPNDataRefresher
from proton.vpn.app.gtk.widgets.vpn import VPNWidget
from proton.vpn.core_api.exceptions import VPNConnectionFoundAtLogout
from proton.vpn.connection.states import Disconnected, Connected, StateContext, Error

from tests.unit.utils import process_gtk_events

PLUS_TIER = 2
FREE_TIER = 0


@pytest.fixture
def server_list():
    return ServerList(apidata={
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "AR#1",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "AR",
                "Tier": PLUS_TIER,
            },
            {
                "ID": 2,
                "Name": "AR#2",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "AR",
                "Tier": PLUS_TIER,
            },
        ],
        "LogicalsUpdateTimestamp": time.time(),
        "LoadsUpdateTimestamp": time.time()
    })


@pytest.fixture
def client_config():
    return ClientConfig.from_dict(DEFAULT_CLIENT_CONFIG)


@pytest.fixture
def controller_mocking_successful_logout():
    controller_mock = Mock()

    logout_future = Future()
    logout_future.set_result(None)

    controller_mock.logout.return_value = logout_future
    controller_mock.is_connection_active = False
    controller_mock.current_connection_status = Disconnected(StateContext(event=None, connection=None))

    return controller_mock


def test_successful_logout(controller_mocking_successful_logout, server_list):
    vpn_widget = VPNWidget(
        controller=controller_mocking_successful_logout,
    )

    vpn_widget.display(user_tier=PLUS_TIER, server_list=server_list)
    vpn_widget.logout_button_click()

    process_gtk_events()

    controller_mocking_successful_logout.logout.assert_called_once()


@pytest.fixture
def controller_mocking_successful_logout_with_current_connection(server_list):
    controller_mock = Mock()
    vpnconnection_mock = Mock()
    vpnconnection_mock.server_id = server_list[0].id

    logout_future_raises_exception = Future()
    logout_future_raises_exception.set_exception(VPNConnectionFoundAtLogout("test"))

    logout_future_success = Future()
    logout_future_success.set_result(None)

    controller_mock.logout.side_effect = [logout_future_raises_exception, logout_future_success]
    controller_mock.is_connection_active = True
    controller_mock.current_connection_status = Connected(StateContext(event=None, connection=vpnconnection_mock))

    return controller_mock


def test_successful_logout_with_current_connection(
        controller_mocking_successful_logout_with_current_connection,
        server_list
):
    vpn_widget = VPNWidget(
        controller=controller_mocking_successful_logout_with_current_connection
    )
    vpn_widget.display(user_tier=PLUS_TIER, server_list=server_list)

    vpn_widget.logout_button_click()

    process_gtk_events()

    controller_mocking_successful_logout_with_current_connection.logout.assert_called_once()

    vpn_widget.close_dialog(end_current_connection=True)

    # Simulate VPN disconnection.
    vpn_widget.status_update(Disconnected())

    process_gtk_events()

    controller_mocking_successful_logout_with_current_connection.disconnect.assert_called_once()
    assert controller_mocking_successful_logout_with_current_connection.logout.call_count == 2


def test_load_enables_vpn_data_refresher_and_displays_widget_when_data_is_ready(
        server_list, client_config
):
    controller_mock = Mock()
    controller_mock.vpn_data_refresher = VPNDataRefresher(
        thread_pool_executor=Mock(),
        proton_vpn_api=Mock()
    )

    vpn_widget = VPNWidget(controller_mock)
    with patch.object(vpn_widget, "display"):
        vpn_widget.load(user_tier=PLUS_TIER)

        # Simulate vpn-data-ready signal from VPNDataRefresher.
        controller_mock.vpn_data_refresher.emit("vpn-data-ready", server_list, client_config)

        process_gtk_events()

        assert vpn_widget.user_tier == PLUS_TIER
        vpn_widget.display.assert_called_with(PLUS_TIER, server_list)


def test_display_initializes_widget(server_list):
    """
    The display method is called once the VPN widget and its childs are ready
    to be displayed, meaning that all required data has been downloaded from
    Proton's REST API.
    The display method should:
     1. update connection state subscribers with the current VPN connection state,
     2. register the VPN widget itself to future VPN connection state updates,
     3. enable the reconnector and finally
     4. emit the vpn-widget-ready signal.
    """
    controller_mock = Mock()
    vpn_widget = VPNWidget(controller_mock)

    # Mock connection status subscribers
    connection_status_subscriber = Mock()
    vpn_widget.connection_status_subscribers.clear()
    vpn_widget.connection_status_subscribers.append(connection_status_subscriber)

    vpn_widget_ready_event = Event()
    vpn_widget.connect("vpn-widget-ready", lambda *_: vpn_widget_ready_event.set())

    vpn_widget.display(user_tier=PLUS_TIER, server_list=server_list)

    process_gtk_events()

    assert connection_status_subscriber.connection_status_update.called_once  # (1)
    assert controller_mock.register_connection_status_subscriber.called_once_with(vpn_widget)  # (2)
    assert controller_mock.reconnector.enable.called_once  # (3)
    assert vpn_widget_ready_event.wait(timeout=0), "vpn-data-ready signal was not sent."  # (4)


def test_vpn_widget_notifies_child_widgets_on_connection_status_update():
    vpn_widget = VPNWidget(controller=Mock())

    # Mock connection status subscribers
    connection_status_subscriber = Mock()
    vpn_widget.connection_status_subscribers.clear()
    vpn_widget.connection_status_subscribers.append(connection_status_subscriber)

    state = Connected()
    vpn_widget.status_update(state)

    process_gtk_events()

    connection_status_subscriber.connection_status_update.assert_called_once_with(state)


def test_unload_resets_widget_state():
    """
    The `unload()` method is called on the "unrealize" event and its goal
    is to reset the widget state. Currently, it does the following things:
    1. disconnects if there is an active VPN connection,
    2. unregisters from connection status updates,
    3. disables the reconnector and
    4. disables the VPN data refresher
    """
    mock_controller = Mock()
    mock_controller.is_connection_active = True

    vpn_widget = VPNWidget(controller=mock_controller)
    vpn_widget.unload()

    mock_controller.disconnect.assert_called_once()  # (1)
    mock_controller.unregister_connection_status_subscriber.assert_called_once_with(vpn_widget)  # (2)
    mock_controller.reconnector.disable.assert_called_once()  # (3)
    mock_controller.vpn_data_refresher.disable.assert_called_once()  # (4)
