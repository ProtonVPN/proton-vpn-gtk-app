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
from threading import Event
from unittest.mock import Mock, patch, call
import time

import pytest
from proton.session.exceptions import (
    ProtonError, ProtonAPINotAvailable,
    ProtonAPINotReachable,
)
from proton.vpn.app.gtk.services import VPNDataRefresher

from tests.unit.testing_utils import process_gtk_events, DummyThreadPoolExecutor


def test_enable_enables_server_list_and_client_config_refreshers_if_the_vpn_session_is_already_loaded():
    api_mock = Mock()
    client_config_refresher_mock = Mock()
    server_list_refresher_mock = Mock()
    certificate_refresher_mock = Mock()
    refresher = VPNDataRefresher(
        executor=DummyThreadPoolExecutor(),
        proton_vpn_api=api_mock,
        client_config_refresher=client_config_refresher_mock,
        server_list_refresher=server_list_refresher_mock,
        certificate_refresher=certificate_refresher_mock
    )

    api_mock.vpn_session_loaded = True

    refresher.enable()

    client_config_refresher_mock.enable.assert_called_once()
    server_list_refresher_mock.enable.assert_called_once()
    certificate_refresher_mock.enable.assert_called_once()


def test_enable_refreshes_vpn_session_if_not_loaded_and_then_enables_server_list_and_client_config_refreshers():
    api_mock = Mock()
    client_config_refresher_mock = Mock()
    server_list_refresher_mock = Mock()
    certiticate_refresher_mock = Mock()
    refresher = VPNDataRefresher(
        executor=DummyThreadPoolExecutor(),
        proton_vpn_api=api_mock,
        client_config_refresher=client_config_refresher_mock,
        server_list_refresher=server_list_refresher_mock,
        certificate_refresher=certiticate_refresher_mock
    )

    api_mock.vpn_session_loaded = False

    refresher.enable()

    # The client config and server list refreshers are not enabled.
    client_config_refresher_mock.enable.assert_not_called()
    server_list_refresher_mock.enable.assert_not_called()
    certiticate_refresher_mock.enable.assert_not_called()

    # The session is refreshed
    api_mock.fetch_session_data.assert_called_once()

    process_gtk_events()

    # And only then the client config and server list refreshers are enabled.
    client_config_refresher_mock.enable.assert_called_once()
    server_list_refresher_mock.enable.assert_called_once()
    certiticate_refresher_mock.enable.assert_called_once()
