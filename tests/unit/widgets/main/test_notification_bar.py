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

from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from tests.unit.utils import process_gtk_events


def test_notification_bar_shows_error_message_and_hides_it_automatically():
    notification_bar = NotificationBar()
    notification_bar.show_error_message("My error message.", hide_after_ms=100)
    assert notification_bar.current_message == "My error message."
    time.sleep(0.2)
    process_gtk_events()
    assert notification_bar.current_message == ""
