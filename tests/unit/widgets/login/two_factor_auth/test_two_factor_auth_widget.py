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

import pytest
from unittest.mock import Mock

from proton.vpn.app.gtk.widgets.login.two_factor_auth.two_factor_auth_widget import TwoFactorAuthWidget
from tests.unit.testing_utils import process_gtk_events


def test_two_factor_auth_widget_forwards_two_factor_auth_successful_signal_when_received_from_two_factor_auth_stack():
    controller_mock = Mock()
    controller_mock.fido2_available = True
    two_factor_auth_successful_callback = Mock()

    two_factor_auth_widget = TwoFactorAuthWidget(controller_mock, Mock(), Mock())
    two_factor_auth_widget.connect("two-factor-auth-successful", two_factor_auth_successful_callback)
    two_factor_auth_widget.two_factor_auth_stack.emit("two-factor-auth-successful")

    process_gtk_events()

    two_factor_auth_successful_callback.assert_called_once()
