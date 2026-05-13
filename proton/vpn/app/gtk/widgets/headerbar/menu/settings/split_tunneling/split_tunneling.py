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
from types import ModuleType
from typing import Callable, Optional


from gi.repository import Gtk

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import \
    ConflictableToggleWidget, ReactiveSetting
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app import \
    AppBasedSplitTunnelingSettings
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.mode import \
    SplitTunnelingModeSetting
from proton.vpn.core.settings.split_tunneling import SplitTunnelingMode

SPLIT_TUNNELING_TOGGLE_SETTING_NAME = "settings.features.split_tunneling.enabled"


class SplitTunnelingSettings(Gtk.Box):
    """Container that holds all settings
    related to split tunneling
    """
    def __init__(
        self,
        controller: Controller,
        split_tunneling_mode: Optional[SplitTunnelingModeSetting] = None,
        split_tunneling_apps: Optional[AppBasedSplitTunnelingSettings] = None,
        split_tunneling_ips: Optional[IpBasedSplitTunnelingSettings] = None,
        gtk: Optional[ModuleType] = None,
    ):  # pylint: disable=too-many-arguments
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self.gtk = gtk or Gtk

        self._settings = None

        self._split_tunneling_mode = split_tunneling_mode\
            or SplitTunnelingModeSetting(controller=self._controller)
        self._split_tunneling_apps = split_tunneling_apps\
            or AppBasedSplitTunnelingSettings(
                controller=self._controller,
                mode=self._split_tunneling_mode.mode,
                gtk=self.gtk
            )
        self._split_tunneling_ips = split_tunneling_ips\
            or IpBasedSplitTunnelingSettings(controller=self._controller, gtk=self.gtk)

        self.append(self._split_tunneling_mode)
        self.append(self._split_tunneling_apps)
        self.append(self._split_tunneling_ips)

        safe_signal_connect(self._split_tunneling_mode, "mode-switched", self._on_mode_switched)

    @staticmethod
    def build(
        controller: Controller,
        split_tunneling_mode: Optional[SplitTunnelingModeSetting] = None,
        split_tunneling_apps: Optional[AppBasedSplitTunnelingSettings] = None,
        split_tunneling_ips: Optional[IpBasedSplitTunnelingSettings] = None,
        gtk: Optional[ModuleType] = None,
    ) -> SplitTunnelingSettings:
        """A quicker way of building this object.

        Args:
            controller (Controller)
            split_tunneling_mode (SplitTunnelingModeSetting, optional): Defaults to None.
            split_tunneling_apps (AppBasedSplitTunnelingSettings, optional): Defaults to None.
            split_tunneling_ips (IpBasedSplitTunnelingSettings, optional): Defaults to None.
            gtk (Gtk, optional): Defaults to None.

        Returns:
            SplitTunnelingSettings
        """
        settings_container = SplitTunnelingSettings(
            controller, split_tunneling_mode,
            split_tunneling_apps, split_tunneling_ips, gtk
        )

        return settings_container

    def _on_mode_switched(self, _: SplitTunnelingModeSetting, mode_changed: SplitTunnelingMode):
        self._split_tunneling_apps.update_list_on_new_mode(mode_changed)


class SplitTunnelingToggle(ConflictableToggleWidget, ReactiveSetting):
    """Contains the split tunneling widget.
    """
    TITLE = "Split tunneling"
    DESCRIPTION = "Customize your connection by deciding "\
        "which apps are protected by VPN."
    TOOLTIP_MESSAGE = "To change split tunneling settings, please disconnect the VPN first."

    def __init__(
            self,
            controller: Controller,
            settings_container: Optional[SplitTunnelingSettings] = None,
            setting_name: str = SPLIT_TUNNELING_TOGGLE_SETTING_NAME,
            do_set: Optional[Callable] = None,
            do_revert: Optional[Callable] = None,
            enabled: Optional[bool] = None,
            gtk: ModuleType = Gtk,
            conflict_resolver: Optional[Callable] = None
    ):  # pylint: disable=too-many-arguments
        super().__init__(
            controller=controller,
            title=self.TITLE,
            setting_name=setting_name,
            description=self.DESCRIPTION,
            do_set=do_set or self._do_set,
            do_revert=do_revert or self._do_revert,
            requires_subscription=True,
            enabled=enabled,
            conflict_resolver=conflict_resolver,
            disable_on_active_connection=True,
            display_tooltip_only_on_active_connection=True
        )
        self._controller = controller
        self.gtk = gtk
        self.revealer: Optional[Gtk.Revealer] = None
        self._settings_container = settings_container
        self._revealer_built = False
        self.set_tooltip(self.TOOLTIP_MESSAGE)

    # pylint: disable=R0801
    @staticmethod
    def build(controller: Controller) -> SplitTunnelingToggle:
        """Shortcut method to initialize widget."""
        widget = SplitTunnelingToggle(controller)
        widget.build_revealer()

        return widget

    def build_revealer(self):
        """Builds the revealer"""
        self.revealer = self.gtk.Revealer()
        self.attach(self.revealer, 0, 2, 2, 1)

        if self._enabled is None:
            self._enabled = self.get_setting()

        if not self._enabled:
            return

        self._build_and_add_split_tunneling_settings()
        self.revealer.set_reveal_child(True)

    def _do_set(self, _toggle, new_value: bool):
        self.save_setting(new_value)
        self.revealer.set_reveal_child(new_value)

        # Only build list if we enabled the toggle
        # and the container was not yet created
        if new_value and not self._settings_container:
            self._build_and_add_split_tunneling_settings()

    def _do_revert(self, _toggle):
        self.switch.set_active(False)

    def _build_and_add_split_tunneling_settings(self):
        self._settings_container = SplitTunnelingSettings(
                controller=self._controller, gtk=self.gtk
            )
        self.revealer.set_child(self._settings_container)

    def on_settings_changed(self, settings):
        if self.overridden_by_upgrade_tag:
            return
        split_tunneling = settings.features.split_tunneling
        if self.switch.get_active() != split_tunneling.enabled:
            self.switch.set_active(split_tunneling.enabled)


class IpBasedSplitTunnelingSettings(Gtk.Box):
    """Object for building the split tunneling settings based on IP
    """
    def __init__(  # pylint: disable=too-many-arguments
        self,
        controller: Controller,
        setting_path_name: str = "settings.features.split_tunneling.config.ip_ranges",
        gtk: ModuleType = Gtk
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self._settings_path_name = setting_path_name
        self.gtk = gtk

    def build(self):
        """Used to build UI.
        """
