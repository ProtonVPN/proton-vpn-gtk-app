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
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.quick_connect_widget import QuickConnectWidget
from proton.vpn.connection.states import Disconnected, Connected
from tests.unit.utils import process_gtk_events


@pytest.mark.parametrize(
    "connection_state", [(Connected()), (Disconnected())]
)
def test_quick_connect_widget_updates_state_according_to_connection_status_update(connection_state):
    mock_controller = Mock()
    quick_connect_widget = QuickConnectWidget(controller=mock_controller)

    quick_connect_widget.connection_status_update(connection_state)

    process_gtk_events()

    assert quick_connect_widget.connection_state == connection_state.type


def test_quick_connect_widget_connects_to_fastest_server_when_connect_button_is_clicked():
    mock_api = Mock()

    with ThreadPoolExecutor() as thread_pool_executor:
        controller = Controller(thread_pool_executor, mock_api)

        quick_connect_widget = QuickConnectWidget(controller=controller)

        quick_connect_widget.connect_button_click()

        process_gtk_events()

        mock_api.servers.get_fastest_server.assert_called_once()
        mock_api.connection.connect.assert_called_once()
