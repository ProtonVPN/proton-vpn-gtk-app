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
