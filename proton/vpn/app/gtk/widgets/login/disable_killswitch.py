"""
This module defines the login widget, used to authenticate the user.


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
from typing import TYPE_CHECKING, Optional

from gi.repository import GObject

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.main.confirmation_dialog import ConfirmationDialog

if TYPE_CHECKING:
    from proton.vpn.app.gtk.app import MainWindow


class KillSwitchLabel(Gtk.Label):
    """Label objet that already contains some styling and pre-configurations"""
    LABEL_TEXT = "Kill switch is blocking any outgoing connections."

    def __init__(self):
        super().__init__(label=KillSwitchLabel.LABEL_TEXT)
        self.set_wrap(True)
        # set_max_width_chars is required for set_line_wrap to have effect.
        self.set_max_width_chars(20)
        self.set_justify(Gtk.Justification.LEFT)


class DisableKillSwitchButton(Gtk.Button):
    """Custom button that already has styling added to it."""
    BUTTON_LABEL = "Disable"

    def __init__(self):
        super().__init__(label=DisableKillSwitchButton.BUTTON_LABEL)
        self.add_css_class("secondary")
        self.add_css_class("spaced")


class DisableKillSwitchWidget(Gtk.Revealer):
    """This is a revealer that displays a short informational message
    and a button it disable the kill switch.
    """
    DIALOG_TITLE = "Kill Switch Enabled"
    DIALOG_MESSAGE = "Permanent Kill Switch is blocking any outgoing connections "\
        "and preventing your IP to be exposed.\n\n"\
        "Do you want to disable Kill Switch ?"

    def __init__(
        self, main_window: "MainWindow",
        killswitch_label: Optional[KillSwitchLabel] = None,
        killswitch_button: Optional[DisableKillSwitchButton] = None,
    ):
        super().__init__()
        self.set_name("login-kill-switch-revealer")

        self._main_window = main_window

        self.killswitch_label = killswitch_label or KillSwitchLabel()
        self.disable_killswitch_button = killswitch_button or DisableKillSwitchButton()

        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        container.append(self.killswitch_label)
        container.append(self.disable_killswitch_button)

        self.set_child(container)

        safe_signal_connect(
            self.disable_killswitch_button,
            "clicked",
            self._on_button_click
        )

    def _on_button_click(self, _: Gtk.Button):
        dialog = ConfirmationDialog(
            DisableKillSwitchWidget.DIALOG_MESSAGE,
            DisableKillSwitchWidget.DIALOG_TITLE
        )
        dialog.set_transient_for(self._main_window)
        dialog.set_modal(True)

        safe_signal_connect(
            dialog,
            "response",
            self._on_dialog_response
        )
        dialog.present()

    def _on_dialog_response(self, dialog: ConfirmationDialog, response_id: int):
        dialog.destroy()
        if response_id == Gtk.ResponseType.YES:
            self.emit("disable-killswitch")

    @GObject.Signal
    def disable_killswitch(self):
        """Signal emitted when the user confirms to disable kill switch."""
