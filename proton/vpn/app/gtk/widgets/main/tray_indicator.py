"""
This module defines the application indicator shown in the system tray.


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
from typing import Optional
from gi.repository import GLib, Gio

from proton.vpn import logging
from proton.vpn.connection import states
from proton.vpn.app.gtk.assets.icons import ICONS_PATH
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow
from proton.vpn.app.gtk.widgets.main.tray_icon import TrayIcon, SNW_BUS_NAME

logger = logging.getLogger(__name__)


class TrayIndicatorNotSupported(Exception):
    """Exception raised when the app indicator cannot be instantiated due to
    missing runtime libraries."""


# pylint: disable=too-few-public-methods
class TrayAvailabilityDetection:
    """Handles checking for tray availability"""
    def is_tray_available(self, timeout_ms: int = 300) -> bool:
        """Return True if the StatusNotifierWatcher D-Bus service is running.

        The SNI watcher (org.kde.StatusNotifierWatcher) is registered on the
        session bus by whichever component provides system-tray support: the
        ubuntu-appindicators / appindicatorsupport GNOME extension host, KDE's
        plasma-workspace, XFCE's statusnotifier plugin, etc.  Its presence is
        therefore a direct, DE-agnostic signal that AppIndicators will work.
        """
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            dbus = Gio.DBusProxy.new_sync(
                bus,
                Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES,
                None,
                "org.freedesktop.DBus",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus",
                None,
            )
            (has_owner,) = dbus.call_sync(
                "NameHasOwner",
                GLib.Variant("(s)", (SNW_BUS_NAME,)),
                Gio.DBusCallFlags.NONE,
                timeout_ms,
                None,
            ).unpack()
            return bool(has_owner)
        except GLib.Error:
            logger.exception("Unable to check for StatusNotifierWatcher")
            return False


# pylint: disable=too-few-public-methods too-many-instance-attributes
class TrayIndicator:
    """App indicator shown in the system tray.

    It's worth pointing out that the `Disconnected` status handling is a bit special,
    as whenever we receive this status we need to check if the user is logged
    in. This is due to the following reason:
        - When a user starts the app and is not logged in, the `TrayIndicator`
        receives the status Disconnnected`.
        By default it shows the connect entry and hides the disconnect
        entry, but since we are not logged in we should not display any of those,
        thus before displaying the buttons we check if user is logged in or not,
        see `_on_connection_disconnected` for implementation details.
    """
    DISCONNECTED_ICON = str(
        ICONS_PATH / f"state-{states.Disconnected.__name__.lower()}.svg"
    )
    DISCONNECTED_ICON_DESCRIPTION = str(
        f"VPN {states.Disconnected.__name__.lower()}"
    )
    CONNECTED_ICON = str(
        ICONS_PATH / f"state-{states.Connected.__name__.lower()}.svg"
    )
    CONNECTED_ICON_DESCRIPTION = str(
        f"VPN {states.Connected.__name__.lower()}"
    )
    ERROR_ICON = str(
        ICONS_PATH / f"state-{states.Error.__name__.lower()}.svg"
    )
    ERROR_ICON_DESCRIPTION = str(
        f"VPN {states.Error.__name__.lower()}"
    )

    def __init__(
        self,
        controller: Controller,
        tray_icon=None,
        tray_availability_detection=TrayAvailabilityDetection()
    ):
        self._tray = tray_icon
        self._main_window: Optional[MainWindow] = None
        self.display_disconnect_entry = None
        self.display_connect_entry = None
        self.enable_disconnect_entry = None
        self.enable_connect_entry = None
        self.display_pinned_servers = None
        self._tray_availability_detection = tray_availability_detection
        self._controller = controller

    def setup(self, main_window: MainWindow):
        """Configure tray if not created yet and register all necessary callbacks.
        If extensions are disabled, a `TrayIndicatorNotSupported` exception is raised.
        """
        if not self._tray_availability_detection.is_tray_available():
            raise TrayIndicatorNotSupported("Tray can not be used")

        if self._tray is None:
            self._tray = TrayIcon()
            self._tray.setup()
            logger.info("Tray enabled")

        self.status_update(self._controller.current_connection_status)
        self._controller.register_connection_status_subscriber(self)
        self._set_main_window(main_window=main_window)

    def is_setup(self) -> bool:
        """Returns whether this instance was already setup or not"""
        return bool(self._tray)

    def _set_main_window(self, main_window: MainWindow):
        """Sets the main window for the tray indicator."""
        self._main_window = main_window
        self._build_menu()

        safe_signal_connect(
            self._main_window,
            "notify::visible", self._on_main_window_visibility_changed
        )

        safe_signal_connect(
            self._main_window.main_widget.login_widget,
            "user-logged-in", self._on_user_logged_in
        )
        safe_signal_connect(
            self._main_window.header_bar.menu,
            "user-logged-out", self._on_user_logged_out
        )

    def status_update(self, connection_status):
        """This method is called whenever the VPN connection status changes."""
        logger.debug(
            f"Tray widget received connection status update: "
            f"{type(connection_status).__name__}."
        )

        update_ui_method = f"_on_connection_{type(connection_status).__name__.lower()}"
        if hasattr(self, update_ui_method):
            GLib.idle_add(getattr(self, update_ui_method))

    def reload_pinned_servers(self):
        """Reloads pinned servers.
            Useful to use when the list is changed from the outside.
        """
        self._update()

    def _build_menu(self):
        self._tray.menu_items.clear()

        self._setup_connection_handler_entries()
        if self._tray.menu_items:
            self._tray.add_menu_separator()

        if self._controller.user_logged_in:
            self.display_pinned_servers = True
            self._setup_pinned_server_entries()

        self._setup_main_window_visibility_toggle_entry()
        self._tray.add_menu_separator()
        self._setup_quit_entry()

        self._tray.update_menu()

    def _setup_pinned_server_entries(self):
        tray_pinned_servers = self._controller.get_app_configuration().tray_pinned_servers
        if not tray_pinned_servers or not self.display_pinned_servers:
            return

        for server in tray_pinned_servers:
            servername = str(server).upper()
            self._tray.add_menu_item(
                label=f"{servername}",
                callback=lambda server=servername: self._on_connect_to_pinned_entry_clicked(server))

        self._tray.add_menu_separator()

    def _setup_connection_handler_entries(self):
        if self.display_connect_entry:
            self._tray.add_menu_item(
                "Connect",
                self._on_connect_entry_clicked,
                self.enable_connect_entry,
            )
        if self.display_disconnect_entry:
            self._tray.add_menu_item(
                "Disconnect",
                self._on_disconnect_entry_clicked,
                self.enable_disconnect_entry,
            )

    def _setup_main_window_visibility_toggle_entry(self):
        toggle_label = "Show" if not self._main_window.get_visible() else "Hide"
        self._tray.add_menu_item(toggle_label,
                                 self._on_toggle_app_visibility_menu_entry_clicked)

    def _setup_quit_entry(self):
        self._tray.add_menu_item("Quit", self._on_exit_app_menu_entry_clicked)

    def _update(self):
        self._build_menu()

    def _on_connect_to_pinned_entry_clicked(self, servername: str):
        logger.info(f"Connect to {servername}", category="ui.tray", event="connect")
        future = self._controller.connect_from_tray(servername)
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.

    def _on_toggle_app_visibility_menu_entry_clicked(self, *_):
        if self._main_window.get_visible():
            self._main_window.set_visible(False)
        else:
            self._main_window.set_visible(True)
            self._main_window.present()
        self._update()

    def _on_main_window_visibility_changed(self, *_):
        self._update()

    def _on_exit_app_menu_entry_clicked(self, *_):
        self._main_window.header_bar.menu.quit_button_click()

    def _on_connect_entry_clicked(self):
        logger.info("Connect to fastest server", category="ui.tray", event="connect")
        future = self._controller.connect_to_fastest_server()
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.

    def _on_disconnect_entry_clicked(self):
        logger.info("Disconnect from VPN", category="ui.tray", event="disconnect")
        future = self._controller.disconnect()
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.

    def _on_user_logged_in(self, *_):
        self.display_disconnect_entry = False
        self.display_connect_entry = True
        self.display_pinned_servers = True
        self.reload_pinned_servers()

    def _on_user_logged_out(self, *_):
        self.display_disconnect_entry = False
        self.display_connect_entry = False
        self.display_pinned_servers = False
        self._update()

    def _on_connection_disconnected(self):
        self.enable_connect_entry = True
        self._tray.change_icon(self.DISCONNECTED_ICON,
                               self.DISCONNECTED_ICON_DESCRIPTION)
        if not self._controller.user_logged_in:
            self._update()
            return

        self.display_disconnect_entry = False
        self.display_connect_entry = True
        self._update()

    def _on_connection_connecting(self):
        self.enable_connect_entry = False
        self.enable_disconnect_entry = True
        self._update()

    def _on_connection_connected(self):
        self.enable_disconnect_entry = True
        self.display_disconnect_entry = True
        self.display_connect_entry = False
        self._tray.change_icon(self.CONNECTED_ICON,
                               self.CONNECTED_ICON_DESCRIPTION)
        self._update()

    def _on_connection_disconnecting(self):
        self.enable_disconnect_entry = False
        self.enable_connect_entry = True
        self._update()

    def _on_connection_error(self):
        self.display_disconnect_entry = False
        self.display_connect_entry = True
        self._tray.change_icon(self.ERROR_ICON,
                               self.ERROR_ICON_DESCRIPTION)
        self._update()

    def activate_toggle_app_visibility_menu_entry(self):
        """Triggers the activation/click of the Show/Hide menu entry."""
        self._on_toggle_app_visibility_menu_entry_clicked()

    def activate_quit_menu_entry(self):
        """Triggers the activation/click of the Quit menu entry."""
        self._on_exit_app_menu_entry_clicked()

    def active_connect_entry(self):
        """Clicks the connect button."""
        self._on_connect_entry_clicked()

    @property
    def top_most_pinned_server_label(self):
        """Returns the topmost pinned server button."""
        pinned_servers = self._controller.get_app_configuration().tray_pinned_servers
        if not pinned_servers:
            return None

        return pinned_servers[0]

    def activate_top_most_pinned_server_entry(self):
        """Clicks the topmost pinned server button."""
        top_server_name = self.top_most_pinned_server_label
        for item in self._tray.menu_items:
            if item.label == top_server_name and item.callback:
                item.callback()
                break

    def activate_disconnect_entry(self):
        """Clicks the disconnect button."""
        self._on_disconnect_entry_clicked()
