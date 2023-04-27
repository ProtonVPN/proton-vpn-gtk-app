"""
Error messenger module.


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
from gi.repository import GLib
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar


class Notifications:
    """It wraps all types of notifications to be shown by the app."""

    def __init__(
        self, main_window: Gtk.ApplicationWindow,
        notification_bar: NotificationBar,
    ):
        self._main_window = main_window
        self.notification_bar = notification_bar
        self.error_dialog = None

    def show_error_dialog(self, message: str, title: str):
        """Show an error dialog to the user."""
        GLib.idle_add(
            self._generate_and_show_dialog, title, message
        )

    def _generate_and_show_dialog(self, title: str, message: str):
        """Generates and displays a pop-up dialog to the user, blocking
        the rest of the UI."""
        if self.error_dialog:
            self.error_dialog.destroy()
            self.error_dialog = None

        self.error_dialog = Gtk.MessageDialog(
            transient_for=self._main_window,
            flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )

        self.error_dialog.set_modal(True)
        self.error_dialog.format_secondary_text(message)
        # .run() blocks code execution until a button on the dialog is clicked,
        # so followed code will only be run after the .run() method has returned.
        self.error_dialog.run()
        self.error_dialog.destroy()

    def show_error_message(self, message: str):
        """Shows the error message in the notification bar."""
        GLib.idle_add(
            self.notification_bar.show_error_message,
            message
        )

    def show_success_message(self, message: str):
        """Shows a success message in the notification bar."""
        GLib.idle_add(
            self.notification_bar.show_success_message,
            message
        )

    def hide_message(self):
        """Hides the revealed content."""
        GLib.idle_add(
            self.notification_bar.clear
        )
