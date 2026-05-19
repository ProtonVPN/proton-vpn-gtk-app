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
from pathlib import Path
from typing import List, Optional
from gi.repository import Gdk, GLib, GObject
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.assets import icons
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.connection import states

from proton.vpn.app.gtk.widgets.main.notifications import Notifications


class PortForwardRevealer(Gtk.Revealer):  # pylint: disable=too-few-public-methods
    """The container that has all PF widgets and reveals on demand."""
    def __init__(self,
                 notifications: Notifications,
                 port_forward_widget: Optional["PortForwardWidget"] = None):
        super().__init__()
        self._port_forward_widget = \
            port_forward_widget or PortForwardWidget(notifications)
        self.set_child(self._port_forward_widget)
        safe_signal_connect(
            self._port_forward_widget,
            "update-visibility",
            self._on_update_port_forwarding_visibility
        )

    def on_new_state(self, connection_state: states.State):
        """Proxy method that relays connection state changes to PF widget."""
        self._port_forward_widget.on_new_state(connection_state)

    def _on_update_port_forwarding_visibility(self, _: PortForwardWidget, display_child: bool):
        self.set_reveal_child(display_child)


class PortForwardWidget(Gtk.Box):
    """Widgets handles the display and interactivity to copy por to clipboard."""
    ACTIVE_PORT_LABEL = "Active port:"
    TOOLTIP_LABEL = "Copy port number"

    def __init__(
            self, notifications: Notifications, clipboard: Optional[Gdk.Clipboard] = None,
            forwarded_port: Optional[int] = None
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_name("port-forwarding-widget")
        self._notifications = notifications
        self._clipboard = (
            clipboard or Gdk.Display.get_default().get_clipboard()
        )
        self._current_forwarded_port = forwarded_port
        self._pending_sources: List[int] = []
        self._copied_popover = None
        self._build_ui()

    @GObject.Signal(name="update-visibility", arg_types=(bool,))
    def update_visibility(self, display_child: bool):
        """
        Signal emitted when the UI should be hidden or not.
        :param display_child: whether PF should be displayed or not.
        """

    def _build_ui(self):
        self.set_halign(Gtk.Align.START)

        active_port_pixbuf = icons.get(
            Path("connection-status/active-port.svg"), width=12, height=12)
        active_port_icon = Gtk.Image.new_from_paintable(
            Gdk.Texture.new_for_pixbuf(active_port_pixbuf))
        active_port_icon.set_size_request(
            active_port_pixbuf.get_width(), active_port_pixbuf.get_height())
        active_port_icon.set_valign(Gtk.Align.CENTER)
        active_port_icon.add_css_class("active-port-icon")

        active_port_label = Gtk.Label(label=self.ACTIVE_PORT_LABEL)
        active_port_label.add_css_class("dim-label")

        self._port_forward_label: Gtk.Label = Gtk.Label(label="")
        self._port_forward_label.add_css_class("dim-label")

        copy_pixbuf = icons.get(Path("copy.svg"), width=16, height=16)
        copy_icon = Gtk.Image.new_from_paintable(Gdk.Texture.new_for_pixbuf(copy_pixbuf))
        copy_icon.set_size_request(copy_pixbuf.get_width(), copy_pixbuf.get_height())

        button_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_content.append(active_port_icon)
        button_content.append(active_port_label)
        button_content.append(self._port_forward_label)
        button_content.append(copy_icon)

        self._copy_button = Gtk.Button()
        self._copy_button.add_css_class("flat")
        self._copy_button.set_child(button_content)
        self._copy_button.set_cursor(Gdk.Cursor.new_from_name("pointer", None))
        safe_signal_connect(self._copy_button, "clicked", self._on_button_press)

        self._copied_popover = Gtk.Popover()
        self._copied_popover.set_child(Gtk.Label(label="Copied!"))
        self._copied_popover.set_autohide(False)
        self._copied_popover.set_has_arrow(False)
        self._copied_popover.set_parent(self._copy_button)

        self.append(self._copy_button)

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

    def do_dispose(self):
        """GObject lifecycle hook to release references; may run more
        than once, so cleanup must be idempotent."""
        if self._copied_popover is not None:
            self._copied_popover.unparent()
            self._copied_popover = None

        self._cancel_pending_popdowns()

        Gtk.Box.do_dispose(self)  # pylint: disable=no-member

    def _cancel_pending_popdowns(self):
        """Cancel pending popdown timers. Sources that have already fired
        and self-removed are skipped."""
        default_context = GLib.MainContext.default()
        for source_id in self._pending_sources:
            if default_context.find_source_by_id(source_id) is not None:
                GLib.source_remove(source_id)
        self._pending_sources.clear()

    def _on_popdown_timer(self) -> bool:
        """Hide the popover and remove ourselves from the pending list.
        Returning ``False`` tells GLib to remove this timer source."""
        self._copied_popover.popdown()
        self._pending_sources.clear()
        return False

    def _on_button_press(self, _: "PortForwardWidget"):
        port_to_be_copied_to_clipboard = self._port_forward_label.get_label()
        value = GObject.Value(GObject.TYPE_STRING, port_to_be_copied_to_clipboard)
        self._clipboard.set(value)
        if isinstance(self.get_root(), Gtk.Window):
            self._copied_popover.popup()
            self._cancel_pending_popdowns()
            self._pending_sources.append(
                GLib.timeout_add(1500, self._on_popdown_timer)
            )

    def click_copy_button(self):
        """Simulates a click on the copy button."""
        self._copy_button.emit("clicked")

    def set_port_forward_label(self, new_port: int):
        """Helper method to set port forward label."""
        self._port_forward_label.set_label(str(new_port))
