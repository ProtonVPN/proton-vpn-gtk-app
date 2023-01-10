"""
Notification bar used to show error messages.
"""
from __future__ import annotations
from gi.repository import GLib

from proton.vpn.app.gtk import Gtk


class NotificationBar(Gtk.Revealer):
    """
    Notification bar widget used to show non-blocking error messages to the
    user for a brief period of time before they automatically disappear.
    """
    HIDE_NOTIFICATION_AFTER_MS = 5000

    def __init__(self):
        super().__init__()
        self._clear_error_message_src_id = None
        self._error_message_label = Gtk.Label()
        self._error_message_label.set_line_wrap(True)
        # set_max_width_chars is required for set_line_wrap to have effect.
        self._error_message_label.set_max_width_chars(1)
        self.add(self._error_message_label)

    @property
    def error_message(self):
        """Returns the error message being shown. This property was added for
        testing purposes."""
        return self._error_message_label.get_label()

    def show_error_message(self, error_message: str, hide_after_ms: int = None):
        """
        Shows the specified error message to the user for a brief period of time.
        :param error_message: error message to be show.
        :param hide_after_ms: number of ms after which the error message will be hidden.
        The default value is NotificationBar.HIDE_NOTIFICATION_AFTER_MS.
        """
        hide_after_ms = hide_after_ms or NotificationBar.HIDE_NOTIFICATION_AFTER_MS
        if self._clear_error_message_src_id:
            # Remove the source that will clear the previous error message,
            # otherwise, it might remove the error message soon after it's added.
            GLib.source_remove(self._clear_error_message_src_id)
            self._clear_error_message_src_id = None

        self._error_message_label.set_label(error_message)
        self.set_reveal_child(True)

        def clear_error_message(*_):
            self._clear_error_message()
            self._clear_error_message_src_id = None
            # We need to return False so that this function is only called once:
            # https://lazka.github.io/pgi-docs/#GLib-2.0/functions.html#GLib.timeout_add
            return False

        self._clear_error_message_src_id = GLib.timeout_add(hide_after_ms, clear_error_message)

    def _clear_error_message(self):
        """Hides the error message being shown, if any."""
        self._error_message_label.set_label("")
        self.set_reveal_child(False)
