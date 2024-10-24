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

from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from tests.unit.testing_utils import process_gtk_events


ERROR_MESSAGE = "Error message to be displayed"
ERROR_TITLE = "Error title to be displayed"


@patch("proton.vpn.app.gtk.widgets.main.notifications.Gtk")
def test_show_error_dialog_shows_error_in_popup_window(gtk_mock):
    dialog_mock = Mock()
    gtk_mock.MessageDialog.return_value = dialog_mock
    notifications = Notifications(Mock(), Mock())

    notifications.show_error_dialog(ERROR_MESSAGE, ERROR_TITLE)
    process_gtk_events()

    dialog_mock.format_secondary_markup.assert_called_once()
    dialog_mock.run.assert_called_once()
    dialog_mock.destroy.assert_called_once()


@patch("proton.vpn.app.gtk.widgets.main.notifications.Gtk")
def test_show_error_dialog_closes_previous_dialog_if_existing(gtk_mock):
    first_dialog_mock = Mock()
    second_dialog_mock = Mock()
    gtk_mock.MessageDialog.return_value = second_dialog_mock
    notifications = Notifications(Mock(), Mock())

    # Simulate an existing dialog being shown.
    notifications.error_dialog = first_dialog_mock

    notifications.show_error_dialog(ERROR_MESSAGE, ERROR_TITLE)

    process_gtk_events()

    first_dialog_mock.destroy.assert_called_once()
    second_dialog_mock.destroy.assert_called_once()


@patch("proton.vpn.app.gtk.widgets.main.notifications.GLib")
def test_show_error_displays_error_message_in_app_notification_bar(glib_mock):
    notification_bar_mock = Mock()

    notifications = Notifications(Mock(), notification_bar_mock)

    notifications.show_error_message(ERROR_MESSAGE)
    process_gtk_events()

    glib_mock.idle_add.assert_called_once_with(
        notification_bar_mock.show_error_message, ERROR_MESSAGE
    )


@patch("proton.vpn.app.gtk.widgets.main.notifications.GLib")
def test_show_success_message_displays_success_message_in_app_notification_bar(glib_mock):
    notification_bar_mock = Mock()

    notifications = Notifications(Mock(), notification_bar_mock)

    notifications.show_success_message("Success message")
    process_gtk_events()

    glib_mock.idle_add.assert_called_once_with(
        notification_bar_mock.show_success_message, "Success message"
    )
