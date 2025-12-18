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
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow
from proton.vpn.app.gtk.widgets.main.tray_icon import TrayIcon

logger = logging.getLogger(__name__)


# See: https://mail.gnome.org/archives/gnome-shell-list/2017-October/msg00034.html
UBUNTU_INDICATOR_EXTENSION = "ubuntu-appindicators@ubuntu.com"
DEFAULT_INDICATOR_EXTENSION = "appindicatorsupport@rgcjonas.gmail.com"

GNOME_SCHEMA = "org.gnome.shell"
KEY_DISABLE_USER_EXT = "disable-user-extensions"

# See: /usr/share/dbus-1/interfaces/org.gnome.Shell.Extensions.xml
# Active: extension is currently running
ACTIVE_STATE = 1.0


class TrayIndicatorNotSupported(Exception):
    """Exception raised when the app indicator cannot be instantiated due to
    missing runtime libraries."""


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
        app_indicator_available=False
    ):
        self._tray = tray_icon
        self._main_window = None
        self.display_disconnect_entry = None
        self.display_connect_entry = None
        self.enable_disconnect_entry = None
        self.enable_connect_entry = None
        self.display_pinned_servers = None

        self._app_indicator_available = app_indicator_available
        self._controller = controller

    def setup(self, main_window: MainWindow):
        """Configure tray if not created yet and register all necessary callbacks.
        If extensions are disabled, a `TrayIndicatorNotSupported` exception is raised.
        """
        if not self._can_tray_be_used():
            raise TrayIndicatorNotSupported("Tray can not be used")

        if self._tray is None:
            self._tray = TrayIcon()
            self._tray.setup()

        self.status_update(self._controller.current_connection_status)
        self._controller.register_connection_status_subscriber(self)
        self._set_main_window(main_window=main_window)

    def _can_tray_be_used(self):
        # If gnome shell is not running then it's another DE and
        # we assume tray works by default.
        if not self._is_gnome_shell_running():
            self._app_indicator_available = True
            logger.warning("Tray icon enabled on an unsupported Desktop Environment")
        else:
            gnome_extensions = self._gnome_shell_list_extensions()
            ubuntu_extension = gnome_extensions.get(UBUNTU_INDICATOR_EXTENSION)
            default_extension = gnome_extensions.get(DEFAULT_INDICATOR_EXTENSION)

            # Since the extension is part of the system we don't care about the
            # user_extension_disabled value.
            enable_for_ubuntu = ubuntu_extension \
                and ubuntu_extension.get("state") == ACTIVE_STATE

            # For the rest we take user_extension_disabled into consideration
            # since it's not installed by default on the system and is dependent
            # on user intention.
            enable_for_default = default_extension \
                and not self._disabled_user_extension() \
                and default_extension.get("state") == ACTIVE_STATE

            if enable_for_ubuntu or enable_for_default:
                self._app_indicator_available = True

        return self._app_indicator_available

    def _is_gnome_shell_running(self, timeout_ms: int = 300) -> bool:
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
                GLib.Variant("(s)", ("org.gnome.Shell",)),
                Gio.DBusCallFlags.NONE,
                timeout_ms,
                None,
            ).unpack()
            return bool(has_owner)
        except GLib.Error:
            logger.exception("Unable to find Gnome Shell")
            return False

    def _gnome_shell_list_extensions(self, timeout_ms: int = 300) -> Optional[dict[str, dict]]:
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            proxy = Gio.DBusProxy.new_sync(
                bus,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.gnome.Shell.Extensions",
                "/org/gnome/Shell/Extensions",
                "org.gnome.Shell.Extensions",
                None,
            )
            value = proxy.call_sync(
                "ListExtensions",
                None,
                Gio.DBusCallFlags.NONE,
                timeout_ms,
                None
            )
            data = value.unpack()
            return data[0] if isinstance(data, tuple) else data
        except GLib.Error:
            logger.exception("Unable to list Gnome extensions")
            return None

    def _disabled_user_extension(self) -> Optional[bool]:
        source = Gio.SettingsSchemaSource.get_default()
        if not source:
            return None

        schema = source.lookup(GNOME_SCHEMA, True)
        if not schema or not schema.has_key(KEY_DISABLE_USER_EXT):
            return None

        settings = Gio.Settings.new_full(schema, None, None)
        return settings.get_boolean(KEY_DISABLE_USER_EXT)

    def _set_main_window(self, main_window: MainWindow):
        """Sets the main window for the tray indicator."""
        self._main_window = main_window
        self._build_menu()

        self._main_window.main_widget.login_widget.connect(
            "user-logged-in", self._on_user_logged_in
        )
        self._main_window.header_bar.menu.connect(
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
        self._tray.add_menu_item("Quick Connect",
                                 self._on_connect_entry_clicked,
                                 self.enable_connect_entry,
                                 self.display_connect_entry)
        self._tray.add_menu_item("Disconnect",
                                 self._on_disconnect_entry_clicked,
                                 self.enable_disconnect_entry,
                                 self.display_disconnect_entry)

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
