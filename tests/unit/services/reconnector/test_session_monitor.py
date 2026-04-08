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
from unittest.mock import Mock, PropertyMock
import pytest

from proton.vpn.app.gtk.services.reconnector.login_session_service import LoginSessionService
from proton.vpn.app.gtk.services.reconnector.session_monitor import SessionMonitor


def test_enable_hooks_session_unlocked_signal():
    login_session_service_mock = Mock(LoginSessionService)
    callback_mock = Mock()
    session_monitor = SessionMonitor(login_session_service_mock)
    session_monitor.session_unlocked_callback = callback_mock

    session_monitor.enable()

    login_session_service_mock.add_session_unlocked_signal_receiver.assert_called_once_with(
        callback_mock
    )


def test_enable_raises_runtime_error_if_callback_is_not_set():
    session_monitor = SessionMonitor(Mock(LoginSessionService))

    with pytest.raises(RuntimeError):
        session_monitor.enable()


def test_enable_ignores_dbus_unavailable_error():
    login_session_service_mock = Mock(LoginSessionService)
    login_session_service_mock.add_session_unlocked_signal_receiver.side_effect = (
        LoginSessionService.DBusUnavailableError
    )
    session_monitor = SessionMonitor(login_session_service_mock)
    session_monitor.session_unlocked_callback = Mock()

    session_monitor.enable()

    assert session_monitor._signal_receiver is None


def test_is_session_unlocked_returns_true_if_dbus_is_unavailable():
    login_session_service_mock = Mock(LoginSessionService)
    type(login_session_service_mock).is_session_unlocked = PropertyMock(
        side_effect=LoginSessionService.DBusUnavailableError
    )
    session_monitor = SessionMonitor(login_session_service_mock)

    assert session_monitor.is_session_unlocked is True


def test_is_session_unlocked_returns_false_if_session_is_locked():
    login_session_service_mock = Mock(LoginSessionService)
    type(login_session_service_mock).is_session_unlocked = PropertyMock(return_value=False)
    session_monitor = SessionMonitor(login_session_service_mock)

    assert session_monitor.is_session_unlocked is False


def test_disable_unhooks_session_unlocked_signal():
    signal_receiver_mock = Mock()
    session_monitor = SessionMonitor(Mock(LoginSessionService))
    session_monitor.set_signal_receiver(signal_receiver_mock)

    session_monitor.disable()

    signal_receiver_mock.remove.assert_called_once()


def test_disable_does_not_unhook_if_not_previously_enabled():
    signal_receiver_mock = Mock()
    session_monitor = SessionMonitor(Mock(LoginSessionService))

    session_monitor.disable()

    signal_receiver_mock.remove.assert_not_called()
