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
from unittest.mock import Mock, PropertyMock, patch
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import UpgradePlusTag
from proton.vpn.core.settings import NetShield


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.Gdk")
def test_upgrade_plus_tag_displays_url_in_window(gdk_mock):
    gdk_mock.CURRENT_TIME = "mock-time"
    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.Gtk.show_uri_on_window") as show_in_browser:
        plus_tag = UpgradePlusTag()
        plus_tag.clicked()
        show_in_browser.assert_called_once_with(None, plus_tag.URL, gdk_mock.CURRENT_TIME)
