"""
This module defines the application indicator shown in the system tray.
"""
import gi
from gi.repository import GLib


from proton.vpn import logging
from proton.vpn.app.gtk import Gtk
from proton.vpn.connection import states
from proton.vpn.app.gtk.assets.icons import ICONS_PATH
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow

logger = logging.getLogger(__name__)


def _import_app_indicator():
    """Try to import required runtime libraries to show the app indicator."""
    # pylint: disable=import-outside-toplevel
    # pylint: disable=no-name-in-module
    try:
        gi.require_version("AyatanaAppIndicator3", "0.1")
        from gi.repository import AyatanaAppIndicator3
        return AyatanaAppIndicator3
    except ValueError as error:
        logger.info(f"AyanaAppIndicator3 not found: {error}")

    try:
        # Try to import legacy app indicator if ayatana indicator is not available.
        gi.require_version("AppIndicator3", "0.1")
        from gi.repository import AppIndicator3
        return AppIndicator3
    except ValueError as error:
        logger.info(f"AppiIndicator3 not found: {error}")

    raise TrayIndicatorNotSupported("Runtime libraries required not available.")


class TrayIndicatorNotSupported(Exception):
    """Exception raised when the app indicator cannot be instantiated due to
    missing runtime libraries."""


# pylint: disable=too-few-public-methods too-many-instance-attributes
class TrayIndicator:
    """App indicator shown in the system tray.

    Worth to point out that the `Disconnected` status handling is a bit special,
    since whenever we receive this status we always check if the user is logged
    in or not. This is mainly due to the following reason:
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
        self, controller: Controller,
        main_window: MainWindow, native_indicator=None
    ):
        self._indicator = native_indicator
        if self._indicator is None:
            AppIndicator = _import_app_indicator()  # pylint: disable=invalid-name
            self._indicator = AppIndicator.Indicator.new(
                id="proton-vpn-app",
                icon_name="proton-vpn-sign",
                category=AppIndicator.IndicatorCategory.APPLICATION_STATUS
            )
            self._indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

        self._connect_entry = None
        self._disconnect_entry = None
        self._toggle_entry = None
        self._quit_entry = None
        self._pinned_server_items = []
        self._controller = controller
        self._main_window = main_window

        self._menu = self._build_menu()
        self._indicator.set_menu(self._menu)

        self._main_window.main_widget.login_widget.connect(
            "user-logged-in", self._on_user_logged_in
        )
        self._main_window.header_bar.menu.connect(
            "user-logged-out", self._on_user_logged_out
        )

        self.status_update(self._controller.current_connection_status)
        self._controller.register_connection_status_subscriber(self)

    def status_update(self, connection_status):
        """This method is called whenever the VPN connection status changes."""
        logger.debug(
            f"Tray widget received connection status update: "
            f"{type(connection_status).__name__}."
        )

        update_ui_method = f"_on_connection_{type(connection_status).__name__.lower()}"
        if hasattr(self, update_ui_method):
            GLib.idle_add(getattr(self, update_ui_method))

    @property
    def display_connect_entry(self) -> bool:
        """Returns if the connect button is visible or not."""
        return self._connect_entry.get_property("visible")

    @property
    def display_disconnect_entry(self) -> bool:
        """Returns if the disconnect button is visible or not."""
        return self._disconnect_entry.get_property("visible")

    @property
    def enable_connect_entry(self) -> bool:
        """Returns if connect entry is clickable or not."""
        return self._connect_entry.get_property("sensitive")

    @enable_connect_entry.setter
    def enable_connect_entry(self, newvalue: bool):
        """Sets if connect entry should be clickable or not."""
        self._connect_entry.set_property("sensitive", newvalue)

    @property
    def enable_disconnect_entry(self) -> bool:
        """Returns if disconnect entry is clickable or not."""
        return self._disconnect_entry.get_property("sensitive")

    @enable_disconnect_entry.setter
    def enable_disconnect_entry(self, newvalue: bool):
        """Sets if disconnect entry should be clickable or not."""
        self._disconnect_entry.set_property("sensitive", newvalue)

    def _build_menu(self) -> Gtk.Menu:
        menu = Gtk.Menu()
        if self._controller.user_logged_in:
            self._setup_pinned_server_entries(menu)

        self._setup_connection_handler_entries(menu)
        self._setup_main_window_visibility_toggle_entry(menu)
        self._setup_quit_entry(menu)

        return menu

    def _setup_pinned_server_entries(self, menu: Gtk.Menu):
        if not self._controller.app_configuration.tray_pinned_servers:
            return

        separator = Gtk.SeparatorMenuItem()
        self._pinned_server_items.append(separator)
        menu.prepend(separator)

        for server in reversed(self._controller.app_configuration.tray_pinned_servers):
            servername = str(server).upper()
            server_entry = Gtk.MenuItem(label=f"{servername}")
            server_entry.connect(
                "activate",
                self._on_connect_to_server_entry_clicked, servername
            )
            menu.prepend(server_entry)

            self._pinned_server_items.append(server_entry)

    def _setup_connection_handler_entries(self, menu: Gtk.Menu):
        self._connect_entry = Gtk.MenuItem(label="Quick Connect")
        self._connect_entry.connect("activate", self._on_connect_entry_clicked)
        menu.append(self._connect_entry)

        self._disconnect_entry = Gtk.MenuItem(label="Disconnect")
        self._disconnect_entry.connect("activate", self._on_disconnect_entry_clicked)
        menu.append(self._disconnect_entry)

    def _setup_main_window_visibility_toggle_entry(self, menu: Gtk.Menu):
        self._toggle_entry = Gtk.MenuItem()
        self._toggle_entry.set_label("Show" if not self._main_window.get_visible() else "Hide")
        self._toggle_entry.connect("activate", self._on_toggle_app_visibility_menu_entry_clicked)
        menu.append(self._toggle_entry)

        self._main_window.connect("show", lambda _: self._toggle_entry.set_label("Hide"))
        self._main_window.connect("hide", lambda _: self._toggle_entry.set_label("Show"))
        self._toggle_entry.show()

    def _setup_quit_entry(self, menu: Gtk.Menu):
        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)

        self._quit_entry = Gtk.MenuItem(label="Quit")
        self._quit_entry.connect("activate", self._on_exit_app_menu_entry_clicked)
        menu.append(self._quit_entry)
        self._quit_entry.show()

    def _on_connect_to_server_entry_clicked(
        self, _: Gtk.MenuItem, servername: str
    ):
        logger.info(f"Connect to {servername}", category="ui.tray", event="connect")
        self._controller.connect_to_server(servername)

    def _on_toggle_app_visibility_menu_entry_clicked(self, *_):
        if self._main_window.get_visible():
            self._main_window.hide()
        else:
            self._main_window.show()
            self._main_window.present()

    def _on_exit_app_menu_entry_clicked(self, *_):
        self._main_window.header_bar.menu.quit_button_click()

    def _on_connect_entry_clicked(self, _):
        logger.info("Connect to fastest server", category="ui.tray", event="connect")
        self._controller.connect_to_fastest_server()

    def _on_disconnect_entry_clicked(self, _):
        logger.info("Disconnect from VPN", category="ui.tray", event="disconnect")
        self._controller.disconnect()

    def _on_user_logged_in(self, *_):
        self._connect_entry.show()
        self._disconnect_entry.hide()
        self._setup_pinned_server_entries(self._menu)
        self._set_visibility_for_pinned_servers(True)

    def _on_user_logged_out(self, *_):
        self._connect_entry.hide()
        self._disconnect_entry.hide()
        self._remove_pinned_servers()

    def _on_connection_disconnected(self):
        self.enable_connect_entry = True
        self._indicator.set_icon_full(
            self.DISCONNECTED_ICON,
            self.DISCONNECTED_ICON_DESCRIPTION
        )

        if self._controller.user_logged_in:
            self._connect_entry.show()
            self._disconnect_entry.hide()
            self._set_visibility_for_pinned_servers(True)

    def _on_connection_connecting(self):
        self.enable_connect_entry = False

    def _on_connection_connected(self):
        self.enable_disconnect_entry = True
        self._connect_entry.hide()
        self._disconnect_entry.show()
        self._indicator.set_icon_full(
            self.CONNECTED_ICON,
            self.CONNECTED_ICON_DESCRIPTION
        )

    def _set_visibility_for_pinned_servers(self, newvalue: bool):
        for server_item in self._pinned_server_items:
            server_item.set_property("visible", newvalue)

    def _remove_pinned_servers(self):
        for server_item in self._pinned_server_items:
            self._menu.remove(server_item)

        self._pinned_server_items = []

    def _on_connection_disconnecting(self):
        self.enable_disconnect_entry = False

    def _on_connection_error(self):
        self._connect_entry.show()
        self._disconnect_entry.hide()
        self._indicator.set_icon_full(
            self.ERROR_ICON,
            self.ERROR_ICON_DESCRIPTION
        )

    def activate_toggle_app_visibility_menu_entry(self):
        """Triggers the activation/click of the Show/Hide menu entry."""
        self._toggle_entry.emit("activate")

    def activate_quit_menu_entry(self):
        """Triggers the activation/click of the Quit menu entry."""
        self._quit_entry.emit("activate")

    def active_connect_entry(self):
        """Clicks the connect button.
        """
        self._connect_entry.emit("activate")

    def activate_top_most_pinned_server_entry(self):
        """Clicks the topmost pinned server button.
        """
        self._menu.get_children()[0].emit("activate")

    def activate_disconnect_entry(self):
        """Clicks the disconnect button.
        """
        self._disconnect_entry.emit("activate")
