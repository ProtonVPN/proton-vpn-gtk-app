"""
This module defines the port forwarding widget.


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
from __future__ import annotations
from typing import Optional
from gi.repository import Gdk, GObject
from proton.vpn.app.gtk import Gtk
from proton.vpn.connection import states

from proton.vpn.app.gtk.widgets.main.notifications import Notifications


class PortForwardRevealer(Gtk.Revealer):  # pylint: disable=too-few-public-methods
    """The container that has all PF widgets and reveals on demand."""
    def __init__(self,
                 notifications: Notifications,
                 port_forward_widget: PortForwardWidget = None):
        super().__init__()
        self._port_forward_widget = \
            port_forward_widget or PortForwardWidget(notifications)
        self.set_child(self._port_forward_widget)
        self._port_forward_widget.connect(
            "update-visibility", self._on_update_port_forwarding_visibility
        )

    def on_new_state(self, connection_state: states.State):
        """Proxy method that relays connection state changes to PF widget."""
        self._port_forward_widget.on_new_state(connection_state)

    def _on_update_port_forwarding_visibility(self, _: PortForwardWidget, display_child: bool):
        self.set_reveal_child(display_child)


class PortForwardWidget(Gtk.Button):
    """Widgets handles the display and interactivity to copy por to clipboard."""
    ACTIVE_PORT_LABEL = "Active port:"
    TOOLTIP_LABEL = "Copy port number"

    def __init__(
            self, notifications: Notifications, clipboard: Gdk.Clipboard = None,
            forwarded_port: Optional[int] = None
    ):
        super().__init__()
        self.set_name("port-forwarding-widget")
        self._notifications = notifications
        self._clipboard = clipboard or Gdk.Display.get_default().get_clipboard()
        self._current_forwarded_port = forwarded_port
        self._port_forward_label = None
        self._build_ui()

        cursor = Gdk.Cursor.new_from_name("pointer", None)
        self.set_cursor(cursor)

    @GObject.Signal(name="update-visibility", arg_types=(bool,))
    def update_visibility(self, display_child: bool):
        """
        Signal emitted when the UI should be hidden or not.
        :param display_child: whether PF should be displayed or not.
        """

    def _build_ui(self):
        self.set_halign(Gtk.Align.CENTER)
        self.set_property("margin-top", 10)
        self.set_tooltip_text(self.TOOLTIP_LABEL)

        # Create the label that will contain the static text
        active_port_label = Gtk.Label(label=self.ACTIVE_PORT_LABEL)
        active_port_label.add_css_class("dim-label")

        # Create the label that will contain the active port, so that it can
        # be easily copied to clipboard
        self._port_forward_label = Gtk.Label(label="")
        self._port_forward_label.add_css_class("dim-label")

        # Create the copy icon
        copy_port_to_clipboard_image = Gtk.Image.new_from_icon_name("edit-copy")
        copy_port_to_clipboard_image.add_css_class("dim-label")

        # Create a label box that will contain the port info. This will us to give
        # more breathing room between text and icon.
        label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label_box.append(active_port_label)
        label_box.append(self._port_forward_label)
        label_box.set_spacing(3)

        # This box will contain both the label and the icon,
        # for easier styling manipulation.
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.append(label_box)
        content_box.append(copy_port_to_clipboard_image)
        content_box.set_spacing(10)

        self.set_child(content_box)

        # set up click to copy port to clipboard
        self.connect("clicked", self._on_button_press)

    def on_new_state(self, connection_state: states.State):
        """Receives new connection state and emits a signal
        of whether it should be hidden or not."""
        self._update_visibility(
            connection_state.forwarded_port,
            reveal_child=isinstance(connection_state, states.Connected)
        )

        top_level = self._port_forward_label.get_root()
        is_focus = True

        # We need to check that the top level widget is indeed the main window
        # because when shutting down the app this widget could process events
        # after the main window is already closed.
        if isinstance(top_level, Gtk.Window):
            is_focus = top_level.is_active()

        new_port = connection_state.forwarded_port
        if new_port and (new_port != self._current_forwarded_port):
            if not is_focus:
                self._notifications.show_gnome_notification(
                    title="Port forwarding",
                    description=f"Active port is {new_port}"
                )

        self._current_forwarded_port = new_port

    def _update_visibility(self, forwarded_port: Optional[int], reveal_child: bool):
        if forwarded_port is None:
            self.emit("update-visibility", False)
            return

        self.emit("update-visibility", reveal_child)
        self.set_port_forward_label(forwarded_port)

    def _on_button_press(
        self, _: "PortForwardWidget"
    ):
        port_to_be_copied_to_clipboard = self._port_forward_label.get_label()
        value = GObject.Value(GObject.TYPE_STRING, port_to_be_copied_to_clipboard)
        self._clipboard.set(value)

    def set_port_forward_label(self, new_port: int):
        """Helper method to set port forward label."""
        self._port_forward_label.set_label(str(new_port))
