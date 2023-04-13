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

from proton.vpn.app.gtk.services.reconnector.session_monitor import (
    SessionMonitor, BUS_NAME,
    SESSION_INTERFACE, UNLOCK_SIGNAL
)


PATH_NAME = "/some/random/bus/object/path"


def test_enable_hooks_login1_unlock_signal():
    bus_mock = Mock()
    callback_mock = Mock()
    session_monitor = SessionMonitor(bus_mock, PATH_NAME)
    session_monitor.session_unlocked_callback = callback_mock

    session_monitor.enable()

    bus_mock.add_signal_receiver.assert_called_once_with(
        handler_function=callback_mock,
        signal_name=UNLOCK_SIGNAL,
        dbus_interface=SESSION_INTERFACE,
        bus_name=BUS_NAME,
        path=PATH_NAME
    )


def test_enable_raises_runtime_error_if_callback_is_not_set():
    bus_mock = Mock()
    session_monitor = SessionMonitor(bus_mock, PATH_NAME)

    with pytest.raises(RuntimeError):
        session_monitor.enable()


@patch("proton.vpn.app.gtk.services.reconnector.session_monitor.dbus")
def test_enable_raises_runtime_error_if_there_is_not_an_active_session(dbus_mock):
    bus_mock = Mock()
    callback_mock = Mock()
    properties_proxy_mock = Mock()
    session_monitor = SessionMonitor(bus_mock)
    session_monitor.session_unlocked_callback = callback_mock

    properties_proxy_mock.GetAll.return_value = {"ActiveSession": []}
    dbus_mock.Interface.return_value = properties_proxy_mock

    with pytest.raises(RuntimeError):
        session_monitor.enable()


def test_disable_unhooks_login1_signal():
    bus_mock = Mock()
    signal_receiver_mock = Mock()

    bus_mock.add_signal_receiver.return_value = signal_receiver_mock

    session_monitor = SessionMonitor(bus_mock, PATH_NAME)
    session_monitor.set_signal_receiver(signal_receiver_mock)

    session_monitor.disable()

    signal_receiver_mock.remove.assert_called_once()


def test_disable_does_not_unhook_from_login1_signal_if_it_was_not_hooked_before():
    bus_mock = Mock()
    signal_receiver_mock = Mock()
    signal_receiver_mock.return_value = None

    session_monitor = SessionMonitor(bus_mock, PATH_NAME)
    bus_mock.add_signal_receiver.return_value = signal_receiver_mock

    session_monitor.disable()
    assert not signal_receiver_mock.remove.call_count
