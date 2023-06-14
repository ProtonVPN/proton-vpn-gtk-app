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
import time
from unittest.mock import Mock, patch
from threading import Event

import pytest
from proton.vpn.session.client_config import ClientConfig

from proton.vpn.session.servers import ServerList

from proton.vpn.app.gtk.services import VPNDataRefresher
from proton.vpn.app.gtk.widgets.vpn import VPNWidget
from proton.vpn.connection.states import Connected

from tests.unit.testing_utils import process_gtk_events

PLUS_TIER = 2
FREE_TIER = 0


@pytest.fixture
def server_list():
    return ServerList.from_dict({
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "AR#1",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "AR",
                "Tier": PLUS_TIER,
            },
            {
                "ID": 2,
                "Name": "AR#2",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "AR",
                "Tier": PLUS_TIER,
            },
        ],
        "MaxTier": PLUS_TIER
    })


@pytest.fixture
def client_config():
    return ClientConfig.default()


def test_load_enables_vpn_data_refresher_and_displays_widget_when_data_is_ready(
        server_list, client_config
):
    controller_mock = Mock()
    api_mock = Mock()
    controller_mock.vpn_data_refresher = VPNDataRefresher(
        thread_pool_executor=Mock(),
        proton_vpn_api=api_mock
    )
    controller_mock.user_tier = PLUS_TIER
    api_mock.client_config.seconds_until_expiration = 10

    vpn_widget = VPNWidget(controller=controller_mock, main_window=Mock())
    with patch.object(vpn_widget, "display"):
        vpn_widget.load()

        # Simulate vpn-data-ready signal from VPNDataRefresher.
        controller_mock.vpn_data_refresher.emit("vpn-data-ready", server_list, client_config)

        process_gtk_events()

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
    vpn_widget = VPNWidget(controller=controller_mock, main_window=Mock())

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
    vpn_widget = VPNWidget(controller=Mock(), main_window=Mock())

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
    controller_mock = Mock()
    controller_mock.is_connection_active = True

    vpn_widget = VPNWidget(controller=controller_mock, main_window=Mock())
    vpn_widget.unload()

    controller_mock.disconnect.assert_called_once()  # (1)
    controller_mock.unregister_connection_status_subscriber.assert_called_once_with(vpn_widget)  # (2)
    controller_mock.reconnector.disable.assert_called_once()  # (3)
    controller_mock.vpn_data_refresher.disable.assert_called_once()  # (4)
