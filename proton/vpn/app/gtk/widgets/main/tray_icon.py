"""
GTK4 Tray Icon Module - Easy to integrate StatusNotifierItem + DBusMenu

This module provides a simple API to add a system tray icon with context menu
to any GTK4 application with minimal code changes.

License: MIT
Author: Matteo Benedetto <me@enne2.net>
Copyright © 2025 Matteo Benedetto

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Usage:
    from trayer import TrayIcon

    # In your GTK4 app:
    tray = TrayIcon(
        app_id="com.example.myapp",
        title="My App",
        icon_name="application-x-executable"
    )

    # Add menu items
    tray.add_menu_item("Show", callback=show_window)
    tray.add_menu_item("Quit", callback=quit_app)

    # Setup (call before app.run())
    tray.setup()
"""
from typing import Callable
from enum import Enum
from dataclasses import dataclass
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
from proton.vpn.app.gtk.util import APPLICATION_ID
from proton.vpn import logging

logger = logging.getLogger(__name__)

# Tray icon configuration
TRAY_TITLE = "Proton VPN"
TRAY_ICON_NAME = "proton-vpn-sign"
TRAY_ICON_DESCRIPTION = ""

# StatusNotifierItem specification
SNI_INTERFACE = "org.kde.StatusNotifierItem"
SNI_PATH = "/StatusNotifierItem"

# DBusMenu specification
DBUSMENU_INTERFACE = "com.canonical.dbusmenu"
DBUSMENU_PATH = "/MenuBar"

# StatusNotifierWatcher
SNW_BUS_NAME = "org.kde.StatusNotifierWatcher"
SNW_OBJECT_PATH = "/StatusNotifierWatcher"
SNW_INTERFACE = "org.kde.StatusNotifierWatcher"


class StatusNotifierItemProperty(Enum):
    """Contains the type of data that a status notifier can have."""
    STATUS = "Status"
    CATEGORY = "Category"
    ID = "Id"
    TITLE = "Title"
    ICON_NAME = "IconName"
    MENU = "Menu"
    ITEM_IS_MENU = "ItemIsMenu"
    ICON_ACCESSIBLE_DESCRIPTION = "IconAccessibleDesc"


class MenuType(Enum):
    """Enum for menu types that are used in the menu."""
    ITEM = "standard"
    SEPARATOR = "separator"


@dataclass
class MenuObject:
    """Object that represents an entry in tray menu."""
    id: int  # pylint: disable=invalid-name
    type: MenuType
    label: str = None
    callback: Callable = None
    enabled: bool = True
    visible: bool = True

    def to_dbus(self) -> dbus.Dictionary:
        """Converts and returns the object to dbus friendly format."""
        return dbus.Dictionary({
            "type": dbus.String(self.type.value),
            "label": dbus.String(self.label),
            "enabled": dbus.Boolean(self.enabled),
            "visible": dbus.Boolean(self.visible)
        }, signature="sv")


class _DBusMenuService(dbus.service.Object):
    """Internal DBusMenu implementation

    This export the objects across Dbus
    https://dbus.freedesktop.org/doc/dbus-python/dbus.service.html?highlight=dbus%20service#dbus.service.Object
    """

    def __init__(self, bus, menu_items: list[MenuObject]):
        self.bus = bus
        self.menu_items = menu_items
        self.revision = 0
        super().__init__(bus, DBUSMENU_PATH)

    def _build_menu_structure(self):
        """Build menu structure from menu_items list"""

        structure = {
            0: {"children": []}  # Root menu item is always first item in the menu
        }

        for item in self.menu_items:
            structure[item.id] = item.to_dbus()
            structure[0]["children"].append(item.id)

        return structure

    def _build_layout(
        self, parent_id, properties, menu: list[dict[int, dbus.Dictionary]] = None
    ):
        """Build layout for GetLayout."""

        if menu is None:
            menu = self._build_menu_structure()

        if parent_id not in menu:
            return (
                dbus.Int32(parent_id),
                dbus.Dictionary({}, signature="sv"),
                dbus.Array([], signature="(ia{sv}av)")
            )

        item: dbus.Dictionary = menu[parent_id]

        children = dbus.Array([], signature="(ia{sv}av)")
        if "children" in item:
            for child_id in item["children"]:
                child_layout = self._build_layout(child_id, properties, menu)
                child_id_dbus = child_layout[0]
                child_props = child_layout[1] \
                    if child_layout[1] else dbus.Dictionary({}, signature="sv")
                child_children = child_layout[2] \
                    if child_layout[2] else dbus.Array([], signature="(ia{sv}av)")
                children.append(
                    dbus.Struct(
                        (child_id_dbus, child_props, child_children),
                        signature="(ia{sv}av)"
                    )
                )

        return (dbus.Int32(parent_id), item, children)

    @dbus.service.method(
        dbus_interface=DBUSMENU_INTERFACE,
        in_signature="iias",
        out_signature="u(ia{sv}av)"
    )
    def GetLayout(self, parent_id, _recursion_depth, property_names):  # pylint: disable=unused-argument, line-too-long, invalid-name # noqa: E501
        """Get menu layout"""
        layout = self._build_layout(parent_id, property_names)
        return (dbus.UInt32(self.revision), layout)

    @dbus.service.method(
        dbus_interface=DBUSMENU_INTERFACE,
        in_signature="aias",
        out_signature="a(ia{sv})"
    )
    def GetGroupProperties(self, ids, _property_names):  # pylint: disable=unused-argument, line-too-long, invalid-name # noqa: E501
        """Get properties for multiple items"""
        menu = self._build_menu_structure()
        result = dbus.Array([], signature="(ia{sv})")

        for item_id in ids:
            if item_id in menu:
                item: dbus.Dictionary = menu[item_id]

                result.append((dbus.Int32(item_id), item))

        return result

    @dbus.service.method(
        dbus_interface=DBUSMENU_INTERFACE,
        in_signature="isvu",
        out_signature=""
    )
    def Event(self, item_id, event_type, _data, _timestamp):  # pylint: disable=unused-argument, line-too-long, invalid-name # noqa: E501
        """Handle menu item clicks"""
        if event_type != "clicked":
            return

        item = [
            item for item in self.menu_items
            if item.id == item_id
            and item.type != MenuType.SEPARATOR.value
            and item.callback
        ]

        if item:
            GLib.idle_add(item.pop().callback)

    @dbus.service.signal(dbus_interface=DBUSMENU_INTERFACE, signature="ui")
    def LayoutUpdated(self, _revision, _parent):  # pylint: disable=unused-argument, invalid-name # noqa: E501
        """Update menu structure"""

    def update_menu(self):
        """Update menu structure"""
        self.revision += 1
        self.LayoutUpdated(self.revision, 0)


class _StatusNotifierItem(dbus.service.Object):
    """Internal StatusNotifierItem implementation"""

    def __init__(self, tray_icon, bus, object_path):
        self.tray = tray_icon
        self.bus = bus

        # Generate unique bus name
        self.bus_name_str = f"org.kde.StatusNotifierItem-{tray_icon.app_id}-{id(self)}"
        self.bus_name = dbus.service.BusName(self.bus_name_str, bus)

        super().__init__(self.bus_name, object_path)

        # Create DBusMenu
        self.menu = _DBusMenuService(bus, tray_icon.menu_items)

        # Register with watcher
        self._register_to_watcher()

    def _register_to_watcher(self):
        """Register with StatusNotifierWatcher"""
        try:
            watcher = self.bus.get_object(SNW_BUS_NAME, SNW_OBJECT_PATH)
            watcher.RegisterStatusNotifierItem(
                self.bus_name_str,
                dbus_interface=SNW_INTERFACE
            )
        except dbus.exceptions.DBusException:
            # Silent fail, will still work on some DEs,
            # see https://specifications.freedesktop.org/status-notifier-item-spec/status-notifier-item-spec-latest.html#registration  # pylint: disable=line-too-long # noqa: E501
            logger.warning(
                "Failed to register to StatusNotifierWatcher",
                category="TRAY_ICON",
                event="STATUS_NOTIFIER_WATCHER_REGISTRATION_FAILED",
            )

    @dbus.service.method(
        dbus_interface="org.freedesktop.DBus.Properties",
        in_signature="ss", out_signature="v"
    )
    def Get(self, interface: str, prop: str):  # pylint: disable=invalid-name
        """Get property"""
        if interface != SNI_INTERFACE:
            # Return an empty DBus string variant instead of None so the
            # dbus library can encode a valid value (None cannot be encoded).
            return dbus.String("")

        available_options = {
            StatusNotifierItemProperty.STATUS.value: dbus.String(self.tray.status),
            StatusNotifierItemProperty.CATEGORY.value: dbus.String("ApplicationStatus"),
            StatusNotifierItemProperty.ID.value: dbus.String(self.tray.app_id),
            StatusNotifierItemProperty.TITLE.value: dbus.String(self.tray.title),
            StatusNotifierItemProperty.ICON_NAME.value: dbus.String(self.tray.icon_name),
            StatusNotifierItemProperty.MENU.value: dbus.ObjectPath(DBUSMENU_PATH),
            StatusNotifierItemProperty.ITEM_IS_MENU.value: dbus.Boolean(True),
            StatusNotifierItemProperty.ICON_ACCESSIBLE_DESCRIPTION.value: dbus.String(
                self.tray.icon_desc
            ),
        }

        # Unknown property: return empty DBus string variant to avoid
        # "Don't know which D-Bus type to use to encode type NoneType" errors.
        return available_options.get(prop, "")

    @dbus.service.method(
        dbus_interface="org.freedesktop.DBus.Properties",
        in_signature="s",
        out_signature="a{sv}"
    )
    def GetAll(self, interface: str) -> dbus.Dictionary:  # pylint: disable=invalid-name
        """Get all properties"""
        if interface != SNI_INTERFACE:
            return {}

        return {
            StatusNotifierItemProperty.STATUS.value: dbus.String(self.tray.status),
            StatusNotifierItemProperty.CATEGORY.value: dbus.String("ApplicationStatus"),
            StatusNotifierItemProperty.ID.value: dbus.String(self.tray.app_id),
            StatusNotifierItemProperty.TITLE.value: dbus.String(self.tray.title),
            StatusNotifierItemProperty.ICON_NAME.value: dbus.String(self.tray.icon_name),
            StatusNotifierItemProperty.MENU.value: dbus.ObjectPath(DBUSMENU_PATH),
            StatusNotifierItemProperty.ITEM_IS_MENU.value: dbus.Boolean(True),
            StatusNotifierItemProperty.ICON_ACCESSIBLE_DESCRIPTION.value: dbus.String(
                self.tray.icon_desc
            )
        }

    @dbus.service.method(dbus_interface=SNI_INTERFACE, in_signature="ii", out_signature="")
    def Activate(self, _x_pos, _y_pos):  # pylint: disable=unused-argument, invalid-name, line-too-long # noqa: E501
        """Activate on click"""
        if self.tray.on_left_click:
            GLib.idle_add(self.tray.on_left_click)

    @dbus.service.signal(dbus_interface=SNI_INTERFACE, signature="")
    def NewIcon(self):  # pylint: disable=invalid-name
        """New icon"""

    def change_icon(self, icon_name, icon_desc):
        """Change icon"""
        self.tray.icon_name = icon_name
        self.tray.icon_desc = icon_desc
        self.NewIcon()


class TrayIcon:  # pylint: disable=too-many-instance-attributes
    """
    Easy-to-use tray icon with context menu for GTK4 apps

    Example:
        tray = TrayIcon(
            app_id="com.example.myapp",
            title="My Application",
            icon_name="application-x-executable"
        )

        tray.set_left_click(lambda: print("Clicked!"))
        tray.add_menu_item("Show", callback=show_window)
        tray.add_menu_separator()
        tray.add_menu_item("Quit", callback=quit_app)

        tray.setup()  # Call before app.run()
    """

    def __init__(
        self,
        app_id=APPLICATION_ID,
        title=TRAY_TITLE,
        icon_name=TRAY_ICON_NAME,
        icon_desc=TRAY_ICON_DESCRIPTION
    ):
        """
        Initialize tray icon

        Args:
            app_id: Application ID (e.g., "com.example.myapp")
            title: Tray icon tooltip/title
            icon_name: Icon name from theme (e.g., "application-x-executable")
        """
        self.app_id = app_id
        self.title = title
        self.icon_name = icon_name
        self.icon_desc = icon_desc
        self.status = "Active"

        self.menu_items = []
        self.on_left_click = None
        self.on_middle_click = None

        self._sni = None
        self._bus = None

    def set_left_click(self, callback):
        """
        Set callback for left-click on tray icon

        Args:
            callback: Function to call (no arguments)
        """
        self.on_left_click = callback

    def add_menu_item(self, label, callback, enabled=True, visible=True):
        """
        Add a menu item

        Args:
            label: Text to display
            callback: Function to call when clicked (no arguments)
            enabled: Whether item is clickable
            visible: Whether item is shown
        """
        self.menu_items.append(
            MenuObject(
                type=MenuType.ITEM,
                id=self._generate_menu_id(),
                label=label,
                callback=callback,
                enabled=enabled,
                visible=visible
            )
        )

    def add_menu_separator(self):
        """Add a separator line to the menu"""
        self.menu_items.append(
            MenuObject(
                type=MenuType.SEPARATOR,
                id=self._generate_menu_id(),
                label=""
            )
        )

    def _generate_menu_id(self):
        """Generate an used to identify the item in the menu."""
        return len(self.menu_items) + 1 if len(self.menu_items) > 0 else 1

    def setup(self):
        """
        Setup the tray icon

        IMPORTANT: Call this BEFORE app.run() in your GTK4 application!

        Example:
            app = MyGtkApp()
            tray = TrayIcon(...)
            tray.setup()
            app.run()
        """
        # Initialize D-Bus
        self._bus = dbus.SessionBus()

        # Create StatusNotifierItem which register itself to the StatusNotifierWatcher
        self._sni = _StatusNotifierItem(self, self._bus, SNI_PATH)

    def change_icon(self, icon_name, icon_desc):
        """
        Change the tray icon

        Args:
            icon_name: New icon name from theme
        """
        if self._sni:
            self._sni.change_icon(icon_name, icon_desc)

    def update_menu(self):
        """
        Update menu after adding/removing items dynamically

        Call this after modifying menu_items to refresh the menu
        """
        if self._sni:
            self._sni.menu.update_menu()
