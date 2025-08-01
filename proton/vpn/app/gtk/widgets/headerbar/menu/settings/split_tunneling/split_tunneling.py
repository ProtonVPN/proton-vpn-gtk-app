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
from typing import Callable, Any


from gi.repository import Gtk

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import \
    ConflictableToggleWidget, ReactiveSetting
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app import \
    AppBasedSplitTunnelingSettings


class SplitTunnelingSettings(Gtk.Box):
    """Container that holds all settings
    related to split tunneling
    """
    def __init__(
        self,
        controller: Controller,
        split_tunneling_mode: SplitTunnelingMode = None,
        split_tunneling_apps: AppBasedSplitTunnelingSettings = None,
        split_tunneling_ips: IpBasedSplitTunnelingSettings = None,
        gtk: Gtk = None,
    ):  # pylint: disable=too-many-arguments
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self.gtk = gtk or Gtk

        self._settings = None

        self._split_tunneling_mode = split_tunneling_mode\
            or SplitTunnelingMode(controller=self._controller, gtk=self.gtk)
        self._split_tunneling_apps = split_tunneling_apps\
            or AppBasedSplitTunnelingSettings(controller=self._controller, gtk=self.gtk)
        self._split_tunneling_ips = split_tunneling_ips\
            or IpBasedSplitTunnelingSettings(controller=self._controller, gtk=self.gtk)

        self.add(self._split_tunneling_mode)
        self.add(self._split_tunneling_apps)
        self.add(self._split_tunneling_ips)

    @staticmethod
    def build(
        controller: Controller,
        split_tunneling_mode: SplitTunnelingMode = None,
        split_tunneling_apps: AppBasedSplitTunnelingSettings = None,
        split_tunneling_ips: IpBasedSplitTunnelingSettings = None,
        gtk: Gtk = None,
    ) -> SplitTunnelingSettings:
        """A quicker way of building this object.

        Args:
            controller (Controller)
            split_tunneling_mode (SplitTunnelingMode, optional): Defaults to None.
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
        settings_container.build_ui()

        return settings_container

    def build_ui(self):
        """Builds all UI related children.
        """
        self._split_tunneling_mode.build()
        self._split_tunneling_apps.build()
        self._split_tunneling_ips.build()


class SplitTunnelingToggle(ConflictableToggleWidget, ReactiveSetting):
    """Contains the split tunneling widget.
    """
    TITLE = "Split Tunneling"
    DESCRIPTION = "Customize your connection by deciding "\
        "which apps are protected by VPN..\n\n"\
        "Split Tunneling settings can only be changed when VPN is disconnected."

    def __init__(
            self,
            controller: Controller,
            settings_container: SplitTunnelingSettings = None,
            setting_name: str = "settings.features.split_tunneling.enabled",
            do_set: Callable = None,
            do_revert: Callable = None,
            enabled: bool = None,
            gtk: Gtk = Gtk,
            conflict_resolver: Callable[[str, Any], str] = None
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
            disable_on_active_connection=True
        )
        self._controller = controller
        self.gtk = gtk
        self.revealer = None
        self._settings_container = settings_container
        self._revealer_built = False

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
            self.show_all()

    def _do_revert(self, _toggle):
        self.switch.set_active(False)

    def _build_and_add_split_tunneling_settings(self):
        self._settings_container = SplitTunnelingSettings(
                controller=self._controller, gtk=self.gtk
            )
        self.revealer.add(self._settings_container)

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
        gtk: Gtk = Gtk
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self._settings_path_name = setting_path_name
        self.gtk = gtk

    def build(self):
        """Used to build UI.
        """


class SplitTunnelingMode(Gtk.Box):
    """Object for building UI based on excluding or including split tunneling.
    """
    def __init__(
            self,
            controller: Controller,
            setting_path_name: str = "settings.features.split_tunneling.config.mode",
            gtk: Gtk = Gtk
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self._setting_path_name = setting_path_name
        self.gtk = gtk

    def build(self):
        """Used to build UI.
        """
