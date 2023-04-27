"""
Notification bar used to show error messages.


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
from __future__ import annotations

from enum import Enum

from gi.repository import GLib

from proton.vpn.app.gtk import Gtk


class NotificationType(Enum):
    """Types of notification messages"""
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"


class NotificationBar(Gtk.Revealer):
    """
    Notification bar widget used to show non-blocking error messages to the
    user for a brief period of time before they automatically disappear.
    """
    HIDE_NOTIFICATION_AFTER_MS = 10000

    def __init__(self):
        super().__init__()
        self._clear_error_message_src_id = None
        self._notification_label = Gtk.Label()
        self._notification_label.set_line_wrap(True)
        self._notf_label_style_context = self._notification_label.\
            get_style_context()
        # set_max_width_chars is required for set_line_wrap to have effect.
        self._notification_label.set_max_width_chars(1)
        self._notification_label.set_justify(Gtk.Justification.CENTER)
        self.add(self._notification_label)

    @property
    def current_message(self):
        """Returns the notification message being shown."""
        return self._notification_label.get_label()

    def show_info_message(self, message: str, hide_after_ms: int = None):
        """
        Shows the specified info message to the user for a limited amount of time.
        :param message: message to be shown.
        :param hide_after_ms: number of ms after which the error message will be hidden.
        The default value is NotificationBar.HIDE_NOTIFICATION_AFTER_MS.
        """
        self._show_notification(message, NotificationType.INFO, hide_after_ms)

    def show_error_message(self, message: str, hide_after_ms: int = None):
        """
        Shows the specified error message to the user for a limited amount of time.
        :param message: error message to be shown.
        :param hide_after_ms: number of ms after which the error message will be hidden.
        The default value is NotificationBar.HIDE_NOTIFICATION_AFTER_MS.
        """
        self._show_notification(message, NotificationType.ERROR, hide_after_ms)

    def show_success_message(self, message: str, hide_after_ms: int = None):
        """
        Shows the specified success message to the user for a limited amount of time.
        :param message: success message to be shown.
        :param hide_after_ms: number of ms after which the error message will be hidden.
        The default value is NotificationBar.HIDE_NOTIFICATION_AFTER_MS.
        """
        self._show_notification(message, NotificationType.SUCCESS, hide_after_ms)

    def clear(self):
        """Hides and clears the revealer."""
        self._clear_error_message()

    def _clear_error_message(self):
        self.set_reveal_child(False)
        self._notification_label.set_label("")
        self._notf_label_style_context.remove_class(NotificationType.SUCCESS.value)
        self._notf_label_style_context.remove_class(NotificationType.INFO.value)
        self._notf_label_style_context.remove_class(NotificationType.ERROR.value)
        if self._clear_error_message_src_id:
            self._clear_error_message_src_id = None

        # We need to return False so that this function is only called once:
        # https://lazka.github.io/pgi-docs/#GLib-2.0/functions.html#GLib.timeout_add
        return False

    def _show_notification(
        self, message: str, notification_type: NotificationType,
        hide_after_ms: int = None
    ):
        hide_after_ms = hide_after_ms or NotificationBar.HIDE_NOTIFICATION_AFTER_MS

        if self._clear_error_message_src_id:
            # Remove the source that will clear the previous error message,
            # otherwise, it might remove the error message soon after it's added.
            GLib.source_remove(self._clear_error_message_src_id)
            self._clear_error_message_src_id = None

        self._notification_label.set_label(message)

        if notification_type == NotificationType.ERROR:
            self._notf_label_style_context.remove_class(NotificationType.SUCCESS.value)
            self._notf_label_style_context.remove_class(NotificationType.INFO.value)
        elif notification_type == NotificationType.SUCCESS:
            self._notf_label_style_context.remove_class(NotificationType.INFO.value)
            self._notf_label_style_context.remove_class(NotificationType.ERROR.value)
        else:
            self._notf_label_style_context.remove_class(NotificationType.ERROR.value)
            self._notf_label_style_context.remove_class(NotificationType.SUCCESS.value)

        self._notf_label_style_context.add_class(notification_type.value)
        self.set_reveal_child(True)

        self._clear_error_message_src_id = GLib.timeout_add(
            hide_after_ms, self._clear_error_message,
        )
