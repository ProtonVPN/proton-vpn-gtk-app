from unittest.mock import Mock, patch

from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from tests.unit.utils import process_gtk_events


ERROR_MESSAGE = "Error message to be displayed"
ERROR_TITLE = "Error title to be displayed"


@patch("proton.vpn.app.gtk.widgets.main.notifications.Gtk")
def test_show_error_dialog_shows_error_in_popup_window(gtk_mock):
    dialog_mock = Mock()
    gtk_mock.MessageDialog.return_value = dialog_mock
    notifications = Notifications(Mock(), Mock())

    notifications.show_error_dialog(ERROR_MESSAGE, ERROR_TITLE)
    process_gtk_events()

    dialog_mock.format_secondary_text.assert_called_once()
    dialog_mock.run.assert_called_once()
    dialog_mock.destroy.assert_called_once()


@patch("proton.vpn.app.gtk.widgets.main.notifications.Gtk")
def test_show_error_dialog_closes_previous_dialog_if_existing(gtk_mock):
    first_dialog_mock = Mock()
    second_dialog_mock = Mock()
    gtk_mock.MessageDialog.side_effect = [first_dialog_mock, second_dialog_mock]
    notifications = Notifications(Mock(), Mock())

    notifications.show_error_dialog(ERROR_MESSAGE, ERROR_TITLE)
    process_gtk_events()
    first_dialog_mock.destroy.assert_called_once()
    notifications.show_error_dialog(ERROR_MESSAGE, ERROR_TITLE)
    process_gtk_events()

    # The `run()` method block the event loop from continuing, meaning that
    # in a real scenario, if a second dialog is to be displayed while the first
    # one is being displayed, the first dialog should be destroyed only once.
    # first_dialog_mock but during unit tests the `run()` method 
    # does not block the event loop, thus destroying the first dialog twice.
    assert first_dialog_mock.destroy.call_count == 2
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
