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


class PortForwardRevealer(Gtk.Revealer):  # pylint: disable=too-few-public-methods
    """The container that has all PF widgets and reveals on demand."""
    def __init__(self, port_forward_widget: PortForwardWidget = None):
        super().__init__()
        self._port_forward_widget = port_forward_widget or PortForwardWidget()
        self.add(self._port_forward_widget)
        self._port_forward_widget.connect(
            "update-visibility", self._on_update_port_forwarding_visibility
        )

    def on_new_state(self, connection_state: states.State):
        """Proxy method that relays connection state changes to PF widget."""
        self._port_forward_widget.on_new_state(connection_state)

    def _on_update_port_forwarding_visibility(self, _: PortForwardWidget, display_child: bool):
        self.set_reveal_child(display_child)


class PortForwardWidget(Gtk.EventBox):
    """Widgets handles the display and interactivity to copy por to clipboard."""
    ACTIVE_PORT_LABEL = "Active port:"
    TOOLTIP_LABEL = "Copy port number"

    def __init__(self, clipboard: Gtk.Clipboard = None):
        super().__init__()
        self.set_name("port-forwarding-widget")
        self._clipboard = clipboard or Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._port_forward_label = None
        self._build_ui()

        # We need to connect this signal to on `realize` because there is no window
        # since the object hasn't been shown yet. Thus we only change the mouse pointer
        # once we actually want to display PortForwardWidget.
        self.connect(
            "realize",
            lambda _: self.get_window().set_cursor(  # noqa: E501 # pylint: disable=line-too-long # nosemgrep: python.lang.correctness.return-in-init.return-in-init
                Gdk.Cursor.new_from_name(
                    Gdk.Display.get_default(),
                    "pointer"
                )
            )
        )
        self.set_state(Gtk.StateType.NORMAL)

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
        active_port_label.get_style_context().add_class("dim-label")

        # Create the label that will contain the active port, so that it can
        # be easily copied to clipboard
        self._port_forward_label = Gtk.Label(label="")
        self._port_forward_label.get_style_context().add_class("dim-label")

        # Create the copy icon
        copy_port_to_clipboard_image = Gtk.Image.new_from_icon_name("edit-copy", 1)
        copy_port_to_clipboard_image.get_style_context().add_class("dim-label")

        # Create a label box that will contain the port info. This will us to give
        # more breathing room between text and icon.
        label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label_box.add(active_port_label)
        label_box.add(self._port_forward_label)
        label_box.set_spacing(3)

        # This box will contain both the label and the icon,
        # for easier styling manipulation.
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.add(label_box)
        content_box.add(copy_port_to_clipboard_image)
        content_box.set_spacing(10)

        # Since EventBox derives from Gtk.Bin, it only allows to have one child,
        # which we've previously created and is added here.
        self.add(content_box)

        # We connect all necessary signals, since we want to:
        # 1) React when the user hovers over the box, by changing the mouse icon
        # 2) Allow to react on click so it provides a visual feedback
        self.connect(
            "button-press-event", self._on_button_press
        )
        self.connect(
            "button-release-event", self._on_button_release
        )
        self.connect(
            "enter-notify-event", self._on_enter_port_forwarding_box
        )
        self.connect(
            "leave-notify-event", self._on_leave_port_forwarding_box
        )

        self.show_all()

    def on_new_state(self, connection_state: states.State):
        """Receives new connection state and emits a signal
        of wether it should be hidden or not."""
        self._update_visibility(
            connection_state.forwarded_port,
            reveal_child=isinstance(connection_state, states.Connected)
        )

    def _update_visibility(self, forwarded_port: Optional[int], reveal_child: bool):
        if forwarded_port is None:
            self.emit("update-visibility", False)
            return

        self.emit("update-visibility", reveal_child)
        self.set_port_forward_label(forwarded_port)

    def _on_button_press(
        self, _: "PortForwardWidget", __: Gdk.EventButton
    ):
        port_to_be_copied_to_clipboard = self._port_forward_label.get_label()
        encoded_string = port_to_be_copied_to_clipboard.encode("utf-8")
        number_of_bytes_in_the_string = len(encoded_string)

        self._clipboard.set_text(
            port_to_be_copied_to_clipboard,
            number_of_bytes_in_the_string
        )
        self.set_state(Gtk.StateType.ACTIVE)

    def _on_button_release(
        self, _: "PortForwardWidget", __: Gdk.EventButton
    ):
        self.set_state(Gtk.StateType.PRELIGHT)

    def _on_enter_port_forwarding_box(self, _: "PortForwardWidget", __: Gdk.EventButton):
        self.set_state(Gtk.StateType.PRELIGHT)

    def _on_leave_port_forwarding_box(self, _: "PortForwardWidget", __: Gdk.EventButton):
        self.set_state(Gtk.StateType.NORMAL)

    def set_port_forward_label(self, new_port: int):
        """Helper method to set port forward label."""
        self._port_forward_label.set_label(str(new_port))
