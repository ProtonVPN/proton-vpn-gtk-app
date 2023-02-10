from unittest.mock import Mock, patch

from proton.vpn.app.gtk.widgets.main.error_messenger import ErrorMessenger
from tests.unit.utils import process_gtk_events


ERROR_MESSAGE = "Error message to be displayed"
ERROR_TITLE = "Error title to be displayed"


@patch("proton.vpn.app.gtk.widgets.main.error_messenger.Gtk")
def test_show_error_with_dialog(gtk_mock):
    dialog_mock = Mock()
    gtk_mock.MessageDialog.return_value = dialog_mock
    error_messenger = ErrorMessenger(Mock(), Mock())

    error_messenger.show_error_dialog(ERROR_MESSAGE, ERROR_TITLE)
    process_gtk_events()

    dialog_mock.format_secondary_text.assert_called_once()
    dialog_mock.run.assert_called_once()
    dialog_mock.destroy.assert_called_once()


@patch("proton.vpn.app.gtk.widgets.main.error_messenger.GLib")
def test_show_error_with_notification_bar(glib_mock):
    notification_bar_mock = Mock()
    show_error_message_mock = Mock()
    notification_bar_mock.show_error_message = show_error_message_mock

    error_messenger = ErrorMessenger(Mock(), notification_bar_mock)

    error_messenger.show_error_bar(ERROR_MESSAGE)
    process_gtk_events()

    glib_mock.idle_add.assert_called_once_with(
        show_error_message_mock, ERROR_MESSAGE
    )
