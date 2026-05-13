"""
General settings module.


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
from typing import TYPE_CHECKING, Optional, Callable
from gi.repository import Gtk, GLib, Gio
from proton.vpn import logging
from proton.vpn.connection import states
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    BaseCategoryContainer, ToggleWidget, EntryWidget,
)
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access import \
    EarlyAccessWidget
if TYPE_CHECKING:
    from proton.vpn.app.gtk.widgets.main.tray_indicator import TrayIndicator

_PROTOCOL_GROUPS = ("generic", "protun")

logger = logging.getLogger(__name__)


class TrayPinnedServersWidget(EntryWidget):
    """Custom widget that holds the pinned servers to tray setting."""
    TRAY_PINNED_SERVERS_LABEL = "Pinned tray connections"
    TRAY_PINNED_SERVERS_DESCRIPTION = "Access preferred connections from system tray."\
        " Enter country or server codes, separated by commas, to quickly connect "\
        "(e.g.: NL#42, JP, US, IT#01)."
    SETTING_NAME = "app_configuration.tray_pinned_servers"

    def __init__(self, controller: Controller, tray_indicator: Optional["TrayIndicator"] = None):
        super().__init__(
            controller=controller,
            title=self.TRAY_PINNED_SERVERS_LABEL,
            description=self.TRAY_PINNED_SERVERS_DESCRIPTION,
            setting_name=self.SETTING_NAME,
            callback=self._save_and_reload_pinned_servers
        )
        self._controller = controller
        self._tray_indicator = tray_indicator

    def _save_and_reload_pinned_servers(self, entry: Gtk.Entry, *_):
        self.save_setting(entry.get_text())
        if self._tray_indicator:
            self._tray_indicator.reload_pinned_servers()

    def get_setting(self):
        """Shortcut property that sets the new setting and stores to disk."""
        tray_pinned_servers = self._controller.get_setting_attr(self.SETTING_NAME)
        return ', '.join(tray_pinned_servers)

    def save_setting(self, new_value: str):  # noqa: F811
        """Returns if the the upgrade tag has overridden original interactive
        object."""
        server_list = []

        for pinned_server in new_value.split(","):
            cleaned_pinned_server = pinned_server.strip().upper()

            if cleaned_pinned_server:
                server_list.append(cleaned_pinned_server)

        self._controller.save_setting_attr(self.SETTING_NAME, server_list)


def default_file_browser(packet_capture_widget: "PacketCaptureWidget"):
    """
    Returns a callback function for opening a file browser dialog to select
    the packet capture directory. The callback is only returned if
    Gtk.FileDialog is available (GTK >= 4.10); otherwise, returns None.
    """
    if not hasattr(Gtk, "FileDialog"):
        return None  # Gtk.FileDialog is only available in GTK >= 4.10

    def _on_browse_response(dialog, result):
        try:
            gfile = dialog.select_folder_finish(result)
            if gfile:
                path = gfile.get_path()
                if path:
                    packet_capture_widget.entry.set_text(path)
                    packet_capture_widget.save_setting(path)
        except GLib.Error as err:
            if err.matches(Gtk.DialogError.quark(), Gtk.DialogError.DISMISSED):
                pass  # user cancelled
            else:
                raise

    def _on_browse_clicked(_button):
        # Guarded by the hasattr check in _build_ui; only reachable on GTK >= 4.10.
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Select packet capture directory")
        dialog.set_accept_label("_Select")
        current_path = packet_capture_widget.entry.get_text().strip()
        if current_path:
            dialog.set_initial_folder(Gio.File.new_for_path(current_path))
        dialog.select_folder(packet_capture_widget.get_root(), None, _on_browse_response)

    return _on_browse_clicked


class PacketCaptureWidget(EntryWidget):
    """Packet capture settings row: start/stop toggle, file path entry, and browse button."""
    LABEL = "Create a troubleshooting file"
    DESCRIPTION = (
        "Captures a specific issue you're facing when using Proton VPN "
        "to get help from our customer support team.\n\n"
        "Warning: This file is a recording of all your internet activity during "
        "the capture session."
    )

    SETTING_NAME = "settings.packet_capture.directory_path"

    def __init__(self,
                 controller: Controller,
                 file_browser:
                     Callable[["PacketCaptureWidget"],
                              Optional[Callable]] = default_file_browser):
        self._on_browse_clicked = file_browser(self)

        super().__init__(controller=controller, title=self.LABEL,
                         description=self.DESCRIPTION,
                         setting_name=self.SETTING_NAME,
                         callback=self._on_focus_outside_entry)
        self._capturing = False
        self.connect("realize", self._on_realize)
        self.connect("unrealize", self._on_unrealize)

    def _on_focus_outside_entry(self, entry: Gtk.Entry, *_):
        self.save_setting(entry.get_text())

    def _build_ui(self):
        # Row 0: setting label + start/stop button (right-aligned, like other toggles)
        self.attach(self.label, 0, 0, 1, 1)

        self._start_stop_button = Gtk.Button(label="Start")
        self._start_stop_button.set_sensitive(self._controller.is_connection_active)
        self._start_stop_button.connect("clicked", self._on_start_stop_clicked)
        self._start_stop_button.set_hexpand(True)
        self._start_stop_button.set_halign(Gtk.Align.END)
        self.attach(self._start_stop_button, 1, 0, 1, 1)

        # Row 1: description
        if self.description:
            self.attach(self.description, 0, 1, 2, 1)

        # Row 2: directory path entry + browse button spanning both columns
        file_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.entry.set_hexpand(True)
        file_row.append(self.entry)

        if self._on_browse_clicked is not None:
            browse_button = Gtk.Button(label="Browse…")
            browse_button.connect("clicked", self._on_browse_clicked)
            file_row.append(browse_button)

        file_row.set_hexpand(True)
        self.attach(file_row, 0, 2, 2, 1)

    def _on_realize(self, _widget):
        self._controller.register_connection_status_subscriber(self)

    def _on_unrealize(self, _widget):
        if self._capturing:
            self._controller.executor.submit(
                self._controller.current_connection.stop_packet_capture
            ).add_done_callback(lambda f: GLib.idle_add(self._set_capturing, False))
        self._controller.unregister_connection_status_subscriber(self)

    def status_update(self, connection_state):
        """Called from the async thread when the VPN connection state changes."""
        GLib.idle_add(self._on_connection_state_changed, connection_state)

    def _on_connection_state_changed(self, connection_state):
        is_connected = isinstance(connection_state, states.Connected)
        self._start_stop_button.set_sensitive(is_connected)
        if not is_connected and self._capturing:
            self._set_capturing(False)

    def _on_start_stop_clicked(self, _button):
        if self._capturing:
            self._controller.executor.submit(
                self._controller.current_connection.stop_packet_capture
            ).add_done_callback(lambda f: GLib.idle_add(self._set_capturing, False))
        else:
            self._controller.executor.submit(
                self._controller.current_connection.start_packet_capture
            ).add_done_callback(lambda f: GLib.idle_add(self._set_capturing, True))

    def _set_capturing(self, capturing: bool):
        self._capturing = capturing

        self._start_stop_button.set_label("Stop" if capturing else "Start")
        if capturing:
            self._start_stop_button.add_css_class("destructive-action")
        else:
            self._start_stop_button.remove_css_class("destructive-action")

    @property
    def capturing(self) -> bool:
        """Returns whether packet capture is currently active."""
        return self._capturing


class GeneralSettings(BaseCategoryContainer):  # pylint: disable=too-many-instance-attributes
    """General settings are grouped under this class."""
    CATEGORY_NAME = "General"
    CONNECT_AT_APP_STARTUP_LABEL = "Auto connect"
    CONNECT_AT_APP_STARTUP_DESCRIPTION = "You will be connected to a server as "\
        "soon as Proton VPN app starts. Replace it with a country ISO code "\
        "(e.g.: US for United States), a server (e.g.: NL#42)"\
        " or Fastest for quick connection. Default value: Off."
    START_APP_MINIMIZED_LABEL = "Start app minimized"
    START_APP_MINIMIZED_DESCRIPTION = "When enabled, the app starts minimized "\
        "to the tray."
    ANONYMOUS_CRASH_REPORTS_LABEL = "Share anonymous crash reports"
    ANONYMOUS_CRASH_REPORTS_DESCRIPTION = "Crash reports help us fix bugs, detect firewalls, "\
        "and avoid VPN blocks.\n\nThese statistics do not contain your IP address, and they "\
        "cannot be used to identify you. We'll never share them with third parties."

    def __init__(
        self, controller: Controller,
        tray_indicator: Optional["TrayIndicator"] = None,
    ):
        super().__init__(self.CATEGORY_NAME)
        self._controller = controller
        self._tray_indicator = tray_indicator
        self._connect_at_startup_entry = None
        self._start_app_minimized_toggle = None
        self._anonymous_crash_reports_toggle = None
        self._packet_capture_widget: Optional[PacketCaptureWidget] = None

    def on_settings_changed(self, settings):
        """Update packet capture widget visibility when the protocol changes."""
        if self._packet_capture_widget is not None:
            self._packet_capture_widget.set_visible(
                self._protocol_supports_packet_capture(settings.protocol)
            )

    def _protocol_supports_packet_capture(self, protocol: str) -> bool:
        for group in _PROTOCOL_GROUPS:
            for cls in self._controller.get_available_protocols(group):
                if str(cls.protocol) == protocol:
                    return cls.supports_packet_capture()
        return False

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.build_connect_at_app_startup()

        if self._tray_indicator:
            self.build_start_app_minimized()
            self.build_tray_pinned_servers()

        self.build_anonymous_crash_reports()
        self.build_packet_capture()
        self.build_beta_upgrade()

    def build_connect_at_app_startup(self):
        """Builds and adds the `connect_at_app_startup` setting to the widget."""
        def _format_and_save_autoconnect_field(entry: Gtk.Entry, entry_widget: EntryWidget, *_):
            new_value: Optional[str] = entry.get_text().strip().upper()
            if new_value == "OFF":
                new_value = None

            entry_widget.save_setting(new_value)

        self._connect_at_startup_entry = EntryWidget(
            controller=self._controller,
            title=self.CONNECT_AT_APP_STARTUP_LABEL,
            description=self.CONNECT_AT_APP_STARTUP_DESCRIPTION,
            setting_name="app_configuration.connect_at_app_startup",
            callback=_format_and_save_autoconnect_field
        )
        self.append(self._connect_at_startup_entry)

    def build_start_app_minimized(self):
        """Builds and adds the `start_app_minimized` setting to the widget."""
        self._start_app_minimized_toggle = ToggleWidget(
            controller=self._controller,
            title=self.START_APP_MINIMIZED_LABEL,
            description=self.START_APP_MINIMIZED_DESCRIPTION,
            setting_name="app_configuration.start_app_minimized"
        )
        self.append(self._start_app_minimized_toggle)

    def build_tray_pinned_servers(self):
        """Builds and adds the `tray_pinned_servers` setting to the widget."""
        self.append(TrayPinnedServersWidget(
            controller=self._controller, tray_indicator=self._tray_indicator
        ))

    def build_anonymous_crash_reports(self):
        """Builds and adds the `anonymous_crash_reports` setting to the widget."""
        self._anonymous_crash_reports_toggle = ToggleWidget(
            controller=self._controller,
            title=self.ANONYMOUS_CRASH_REPORTS_LABEL,
            description=self.ANONYMOUS_CRASH_REPORTS_DESCRIPTION,
            setting_name="settings.anonymous_crash_reports"
        )
        self.append(self._anonymous_crash_reports_toggle)

    def build_packet_capture(self):
        """Builds and adds the `packet_capture` file path setting to the widget."""
        widget = PacketCaptureWidget(self._controller)
        current_protocol = self._controller.get_settings().protocol
        widget.set_visible(self._protocol_supports_packet_capture(current_protocol))
        self._packet_capture_widget = widget
        self.append(widget)

    def build_beta_upgrade(self):
        """Builds and adds the `Early Access` setting to the widget."""
        early_access = EarlyAccessWidget(self._controller)

        if not early_access.can_early_access_be_displayed():
            return

        self.append(early_access)
