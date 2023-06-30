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
from gi.repository import GLib

from unittest.mock import Mock, patch

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow
from tests.unit.testing_utils import process_gtk_events


class HeaderBarMock(Gtk.HeaderBar):
    def __init__(self):
        super().__init__()
        self.menu = Mock()


@pytest.fixture
def main_window():
    return MainWindow(
        application=None,
        controller=Mock(),
        notifications=Mock(),
        header_bar=HeaderBarMock(),
        main_widget=Gtk.Label(label="Main widget")
    )


@pytest.fixture
def dummy_app(main_window):
    def show_window(app):
        app.add_window(main_window)
        main_window.show()
        process_gtk_events()

    app = Gtk.Application()
    app.connect("activate", show_window)
    return app


def test_close_button_triggers_quit_menu_entry_when_tray_indicator_is_not_used(dummy_app, main_window):
    main_window.configure_close_button_behaviour(tray_indicator_enabled=False)

    main_window.connect("show", lambda _: main_window.close())
    
    GLib.timeout_add(interval=50, function=dummy_app.quit)
    process_gtk_events()

    dummy_app.run()
    process_gtk_events()

    main_window.header_bar.menu.quit_button_click.assert_called_once()


def test_close_button_hides_window_when_tray_indicator_is_used(dummy_app, main_window):
    main_window.configure_close_button_behaviour(tray_indicator_enabled=True)

    main_window.connect("show", lambda _: main_window.close())
    GLib.timeout_add(interval=50, function=dummy_app.quit)
    process_gtk_events()

    with patch.object(main_window, "hide"):
        dummy_app.run()
        process_gtk_events()

        main_window.hide.assert_called_once()
