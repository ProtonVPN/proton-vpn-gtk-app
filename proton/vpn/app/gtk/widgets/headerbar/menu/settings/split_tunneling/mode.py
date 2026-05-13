"""
Copyright (c) 2025 Proton AG

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
from dataclasses import dataclass
from typing import ClassVar, List

from gi.repository import Gtk, GObject

from proton.vpn.core.settings.split_tunneling import SplitTunnelingMode
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import \
    SettingName, SettingDescription


@dataclass
class ModeData:
    """Dataclass that contains display mode information."""
    title: str
    description: str
    mode: SplitTunnelingMode


EXCLUDE_MODE = ModeData(
    title="Exclude mode",
    description="Allow selected apps to connect "
    "without VPN protection.",
    mode=SplitTunnelingMode.EXCLUDE
)

INCLUDE_MODE = ModeData(
    title="Include mode",
    description="Only selected apps connect with "
    "VPN protection. All other traffic is unprotected.",
    mode=SplitTunnelingMode.INCLUDE,
)


class ModeRadioButton(Gtk.Box):
    """Custom radio button for mode selection"""
    # Class-level group storage
    _radio_buttons: ClassVar[List[Gtk.CheckButton]] = []

    def __init__(self, mode_data: ModeData):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        self.mode = mode_data.mode

        self._radio_button = Gtk.CheckButton()

        if not self._radio_buttons:
            self._radio_buttons.append(self._radio_button)
        else:
            self._radio_button.set_group(self._radio_buttons[0])

        self._radio_button.set_halign(Gtk.Align.START)
        self._radio_button.set_valign(Gtk.Align.START)
        self._radio_button.set_margin_top(2)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        self._title_label = SettingName(mode_data.title, bold=True)

        self._description_label = SettingDescription(mode_data.description)

        text_box.append(self._title_label)
        text_box.append(self._description_label)

        self.append(self._radio_button)
        self.append(text_box)

        self.add_css_class("setting-item")
        self.set_margin_top(8)
        self.set_margin_bottom(8)

        safe_signal_connect(self._radio_button, "toggled", self._on_radio_toggled)

    def _on_radio_toggled(self, _):
        self.emit("toggled", self.mode)

    @GObject.Signal(name="toggled", arg_types=(object,))
    def toggled(self, widget: SplitTunnelingMode):
        """Signal that the radio button was toggled.

        Args:
            widget (SplitTunnelingMode): widget that was toggled.
        """

    def get_active(self) -> bool:
        """Get the active state of the radio button"""
        return self._radio_button.get_active()

    def set_active(self, newvalue: bool):
        """Set the active state of the radio button"""
        self._radio_button.set_active(newvalue)


SETTINGS_PATH_NAME = "settings.features.split_tunneling.mode"


class SplitTunnelingModeSetting(Gtk.Box):
    """Object for building UI based on excluding or including split tunneling.
    """
    def __init__(
            self,
            controller: Controller,
            setting_path_name: str = SETTINGS_PATH_NAME,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._controller = controller
        self._setting_path_name = setting_path_name

        self._exclude_radio = None
        self._include_radio = None
        self.mode = self._get_setting()
        self.build()

    def build(self):
        """Used to build UI.
        """
        self._exclude_radio = ModeRadioButton(mode_data=EXCLUDE_MODE)
        self._include_radio = ModeRadioButton(mode_data=INCLUDE_MODE)

        self.append(self._exclude_radio)
        self.append(self._include_radio)

        self._update_selection()

        safe_signal_connect(self._exclude_radio, "toggled", self._on_mode_changed)
        safe_signal_connect(self._include_radio, "toggled", self._on_mode_changed)

    @GObject.Signal(name="mode-switched", arg_types=(object,))
    def mode_switched(self, mode_changed: SplitTunnelingMode):
        """When the toggle is switched, the mode it switched to is sent
        to the subscribers.

        Args:
            mode_changed (SplitTunnelingMode): mode that was changed to.
        """

    def _on_mode_changed(self, radio_button: ModeRadioButton, mode: SplitTunnelingMode):
        """Handle mode selection change"""
        if radio_button.get_active():
            self._save_setting(mode)
            self.mode = mode
            self.emit("mode-switched", mode)

    def _update_selection(self):
        """Update radio button selection based on current setting"""
        current_mode_exclude = self.mode == SplitTunnelingMode.EXCLUDE
        self._exclude_radio.set_active(current_mode_exclude)
        self._include_radio.set_active(not current_mode_exclude)

    def _get_setting(self) -> SplitTunnelingMode:
        """Get current mode setting"""
        return self._controller.get_setting_attr(self._setting_path_name)

    def _save_setting(self, mode: SplitTunnelingMode):
        """Save mode setting"""
        self._controller.save_setting_attr(self._setting_path_name, mode)

    def get_exclude_radio_button(self):
        """Get the exclude radio button."""
        return self._exclude_radio

    def get_include_radio_button(self):
        """Get the include radio button."""
        return self._include_radio
