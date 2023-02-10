"""
Error messenger module.
"""
from gi.repository import GLib
from proton.vpn.app.gtk import Gtk


class ErrorMessenger:
    """The error messenger object serves the purpose of wrapping all
    types of messages whenever an error occurs."""

    def __init__(
        self, main_window: Gtk.ApplicationWindow,
        notification_bar: Gtk.Revealer,
    ):
        self._main_window = main_window
        self._notification_bar = notification_bar
        self.error_dialogs = []  # only for testing purposes

    def show_error_dialog(self, message: str, title: str):
        """Show an error dialog to the user."""
        GLib.idle_add(
            self._generate_and_show_dialog, title, message
        )

    def _generate_and_show_dialog(self, title: str, message: str):
        """Generates and displays a pop-up dialog to the user, blocking
        the rest of the UI."""
        error_dialog = Gtk.MessageDialog(
            transient_for=self._main_window,
            flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        self.error_dialogs.append(error_dialog)
        error_dialog.format_secondary_text(message)
        error_dialog.run()
        error_dialog.destroy()
        self.error_dialogs.remove(error_dialog)

    def show_error_bar(self, error_message: str):
        """Shows the error within a notification bar."""
        GLib.idle_add(
            self._notification_bar.show_error_message,
            error_message
        )
