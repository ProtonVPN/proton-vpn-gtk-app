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
from proton.vpn.app.gtk import gi
from gi.repository import Gdk  # pylint: disable=C0413 # noqa: E402
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings import GeneralSettings


@pytest.fixture
def mocked_controller_and_connect_app_at_startup():
    controller_mock = Mock(name="controller")

    property_mock = PropertyMock(name="connect_app_at_startup", return_value=None)
    type(controller_mock.app_configuration).connect_at_app_startup = property_mock

    return controller_mock, property_mock


def test_connect_at_app_start_when_setting_is_called_upon_building_ui_elements(mocked_controller_and_connect_app_at_startup):
    controller_mock, connect_at_app_startup_mock = mocked_controller_and_connect_app_at_startup

    general_settings = GeneralSettings(controller_mock, Mock())
    general_settings.build_connect_at_app_startup()

    connect_at_app_startup_mock.assert_called_once()


def test_connect_at_app_start_when_entry_is_set_to_initial_value(mocked_controller_and_connect_app_at_startup):
    controller_mock, connect_at_app_startup_mock = mocked_controller_and_connect_app_at_startup

    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.Gtk.Entry.set_text") as set_text_mock:
        general_settings = GeneralSettings(controller_mock, Mock())
        general_settings.build_connect_at_app_startup()

        set_text_mock.assert_called_once_with("Off")


@pytest.mark.parametrize("raw_new_setting, ui_friendly_new_setting", [(None, "Off"), ("fastest", "Fastest")])
def test_connect_at_app_start_translates_data_types_when_switching_to_and_from_off_setting(raw_new_setting, ui_friendly_new_setting, mocked_controller_and_connect_app_at_startup):
    controller_mock, connect_at_app_startup_mock = mocked_controller_and_connect_app_at_startup

    general_settings = GeneralSettings(controller_mock, Mock())
    general_settings.build_connect_at_app_startup()

    connect_at_app_startup_mock.reset_mock()

    general_settings.connect_at_app_startup_row.interactive_object.set_text(ui_friendly_new_setting)
    general_settings.connect_at_app_startup_row.interactive_object.emit("focus-out-event", Gdk.Event(Gdk.EventType.FOCUS_CHANGE))

    if raw_new_setting is None:
        connect_at_app_startup_mock.assert_called_once_with(raw_new_setting)
    else:
        connect_at_app_startup_mock.assert_called_once_with(raw_new_setting.upper())


@pytest.mark.parametrize("new_setting", ["fastest", "pt", "nl#12"])
def test_connect_at_app_start_when_changing_entry_and_leaving_focus_ensuring_changes_are_saved(new_setting, mocked_controller_and_connect_app_at_startup):
    controller_mock, connect_at_app_startup_mock = mocked_controller_and_connect_app_at_startup

    general_settings = GeneralSettings(controller_mock, Mock())
    general_settings.build_connect_at_app_startup()

    connect_at_app_startup_mock.reset_mock()

    general_settings.connect_at_app_startup_row.interactive_object.set_text(new_setting)
    general_settings.connect_at_app_startup_row.interactive_object.emit("focus-out-event", Gdk.Event(Gdk.EventType.FOCUS_CHANGE))

    connect_at_app_startup_mock.assert_called_once_with(new_setting.upper())


@pytest.fixture
def mocked_controller_and_tray_pinned_servers():
    controller_mock = Mock(name="controller")

    property_mock = PropertyMock(name="tray_pinned_servers", return_value=[])
    type(controller_mock.app_configuration).tray_pinned_servers = property_mock

    return controller_mock, property_mock


def test_tray_pinned_servers_when_setting_is_called_upon_building_ui_elements(mocked_controller_and_tray_pinned_servers):
    controller_mock, tray_pinned_servers_mock = mocked_controller_and_tray_pinned_servers

    general_settings = GeneralSettings(controller_mock, Mock())
    general_settings.build_tray_pinned_servers()

    tray_pinned_servers_mock.assert_called_once()


def test_tray_pinned_servers_when_tray_indicator_is_not_available(mocked_controller_and_tray_pinned_servers):
    controller_mock, tray_pinned_servers_mock = mocked_controller_and_tray_pinned_servers

    general_settings = GeneralSettings(controller_mock)
    general_settings.build_tray_pinned_servers()

    assert general_settings.tray_pinned_servers_row is None


def test_tray_pinned_servers_when_entry_is_set_to_initial_value(mocked_controller_and_tray_pinned_servers):
    controller_mock, tray_pinned_servers_mock = mocked_controller_and_tray_pinned_servers

    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.Gtk.Entry.set_text") as set_text_mock:
        general_settings = GeneralSettings(controller_mock, Mock())
        general_settings.build_tray_pinned_servers()

        set_text_mock.assert_called_once_with('')


@pytest.mark.parametrize("new_setting", [("se, pt#12, CH"), (" pt "), ("nl#12"), ('')])
def test_tray_pinned_servers_when_changing_entry_and_leaving_focus_ensuring_changes_are_saved(new_setting, mocked_controller_and_tray_pinned_servers):
    controller_mock, tray_pinned_servers_mock = mocked_controller_and_tray_pinned_servers

    general_settings = GeneralSettings(controller_mock, Mock())
    general_settings.build_tray_pinned_servers()

    tray_pinned_servers_mock.reset_mock()

    general_settings.tray_pinned_servers_row.interactive_object.set_text(new_setting)
    general_settings.tray_pinned_servers_row.interactive_object.emit("focus-out-event", Gdk.Event(Gdk.EventType.FOCUS_CHANGE))

    if new_setting:
        _new_setting = new_setting.split(",")
        _new_setting = [entry.strip().upper() for entry in _new_setting]
    else:
        _new_setting = []

    tray_pinned_servers_mock.assert_called_once_with(_new_setting)


def test_tray_pinned_servers_when_changing_entry_and_leaving_focus_ensuring_tray_reload_pinned_servers(mocked_controller_and_tray_pinned_servers):
    controller_mock, tray_pinned_servers_mock = mocked_controller_and_tray_pinned_servers

    tray_indicator_mock = Mock()

    general_settings = GeneralSettings(controller_mock, tray_indicator_mock)
    general_settings.build_tray_pinned_servers()

    general_settings.tray_pinned_servers_row.interactive_object.set_text("")
    general_settings.tray_pinned_servers_row.interactive_object.emit("focus-out-event", Gdk.Event(Gdk.EventType.FOCUS_CHANGE))

    tray_indicator_mock.reload_pinned_servers.assert_called_once()

@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.GeneralSettings.build_connect_at_app_startup")
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.GeneralSettings.build_tray_pinned_servers")
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.GeneralSettings.build_anonymous_crash_reports")
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.GeneralSettings.build_beta_upgrade")
def test_beta_upgrade_is_displayed_if_feature_flag_is_enabled(mock_build_beta_upgrade, *_):
    controller_mock = Mock(name="controller")
    controller_mock.feature_flags.get.return_value = True

    general_settings = GeneralSettings(controller_mock, Mock())
    general_settings.build_ui()
    mock_build_beta_upgrade.assert_called_once()
