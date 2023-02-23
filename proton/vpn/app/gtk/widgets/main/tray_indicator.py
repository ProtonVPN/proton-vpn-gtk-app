"""
This module defines the application indicator shown in the system tray.
"""
from collections import namedtuple
import gi
from gi.repository import GLib


from proton.vpn import logging
from proton.vpn.app.gtk import Gtk
from proton.vpn.connection import states
from proton.vpn.app.gtk.assets.icons import ICONS_PATH
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow

logger = logging.getLogger(__name__)

IconType = namedtuple("IconType", ["file_path", "description"])


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


# pylint: disable=too-few-public-methods
class TrayIndicator:
    """App indicator shown in the system tray."""

    def __init__(self, controller: Controller, main_window: MainWindow):
        AppIndicator = _import_app_indicator()  # pylint: disable=invalid-name
        self._controller = controller
        self._main_window = main_window
        self._indicator = AppIndicator.Indicator.new(
            id="proton-vpn-app",
            icon_name="proton-vpn-sign",
            category=AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )
        self._indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self._menu = self._build_menu()
        self._indicator.set_menu(self._menu)
        self.icons = {
            state: IconType(
                str(ICONS_PATH / f"vpn-{state.__name__.lower()}.svg"),
                f"VPN {state.__name__.lower()}"
            ) for state in [states.Disconnected, states.Connected, states.Error]
        }

        self.status_update(self._controller.current_connection_status)
        self._controller.register_connection_status_subscriber(self)

    def status_update(self, connection_status):
        """This method is called whenever the VPN connection status changes."""
        logger.debug(
            f"Tray widget received connection status update: "
            f"{connection_status.state.name}."
        )
        icon_type = self.icons.get(type(connection_status))
        if not icon_type:
            return

        def update_icon(_icon_type):
            self._indicator.set_icon_full(
                _icon_type.file_path,
                _icon_type.description
            )

        GLib.idle_add(update_icon, icon_type)

    def _build_menu(self) -> Gtk.Menu:
        menu = Gtk.Menu()

        toggle_entry = Gtk.MenuItem()
        toggle_entry.set_label("Show" if not self._main_window.get_visible() else "Hide")
        toggle_entry.connect("activate", self._on_toggle_app_visibility_menu_entry_clicked)
        menu.append(toggle_entry)
        self._main_window.connect("show", lambda _: toggle_entry.set_label("Hide"))
        self._main_window.connect("hide", lambda _: toggle_entry.set_label("Show"))
        toggle_entry.show()

        quit_entry = Gtk.MenuItem(label="Quit")
        quit_entry.connect("activate", self._on_exit_app_menu_entry_clicked)
        menu.append(quit_entry)
        quit_entry.show()

        return menu

    def _on_toggle_app_visibility_menu_entry_clicked(self, *_):
        if self._main_window.get_visible():
            self._main_window.hide()
        else:
            self._main_window.show()
            self._main_window.present()

    def _on_exit_app_menu_entry_clicked(self, *_):
        self._main_window.header_bar.menu.quit_button_click()

    def activate_toggle_app_visibility_menu_entry(self):
        """Triggers the activation/click of the Show/Hide menu entry."""
        self._menu.get_children()[0].emit("activate")

    def activate_quit_menu_entry(self):
        """Triggers the activation/click of the Quit menu entry."""
        self._menu.get_children()[1].emit("activate")

    def get_icon_description(self) -> str:
        """Gets the description for the icon.
        """
        return self._indicator.get_icon_desc()
