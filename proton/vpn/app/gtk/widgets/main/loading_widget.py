"""
This module defines the Loading widget. This widget is responsible for displaying
the loading screen.


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

from typing import Optional, Union
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect


class Spinner(Gtk.Spinner):
    """Spinner with some default configurations.
    Upon being shown it automatically starts spinning.
    """
    def __init__(self, size: int = 50):
        super().__init__()
        self.set_property("height-request", size)
        safe_signal_connect(self, "realize", self._on_realize)

    def _on_realize(self, _: Gtk.Widget):
        """Starts spinning when the widget is realized."""
        self.start()


class BaseLoadingContainerWidget(Gtk.Box):
    """Used mainly to standardize and styling, to reduce boilerplate code.
    """
    def __init__(self, orientation: Gtk.Orientation = Gtk.Orientation.VERTICAL):
        super().__init__(orientation=orientation)
        self.set_spacing(25)
        self.set_valign(Gtk.Align.CENTER)
        self.set_vexpand(True)


class DefaultLoadingWidget(BaseLoadingContainerWidget):
    """Helper class to be used when only a label is needed
    to be displayed with a spinner."""
    def __init__(self, label: str):
        super().__init__()
        self._label = Gtk.Label.new(label)
        self._label.set_wrap(True)
        self._label.set_max_width_chars(1)
        self._label.set_hexpand(True)
        self._label.set_justify(Gtk.Justification.CENTER)
        self._label.add_css_class("default-loading-widget-label")
        self._label.set_valign(Gtk.Align.CENTER)
        self._label.set_vexpand(True)
        self._spinner = Spinner()

        self.append(self._label)
        self.append(self._spinner)

    def get_label(self) -> str:
        """Returns the label of the object"""
        return self._label.get_label()


class LoadingConnectionWidget(BaseLoadingContainerWidget):
    """When establishing connections, this widget is used to display status,
    hide the main vpn widget and display a cancel connection button.
    """
    def __init__(
        self, label: str,
        cancel_button: Gtk.Button,
        display_loading_status: Optional[Gtk.Widget] = None
    ):
        super().__init__()

        self._label = Gtk.Label.new(label)
        self._cancel_button = cancel_button
        self._cancel_button.add_css_class("danger")
        self._cancel_button.set_halign(Gtk.Align.CENTER)

        self._display_loading_status: Union[Spinner, Gtk.Widget]
        if not display_loading_status:
            self._display_loading_status = Spinner()
            self._display_loading_status.start()
        else:
            self._display_loading_status = display_loading_status

        self.append(self._label)
        self.append(self._display_loading_status)
        self.append(self._cancel_button)

    def get_label(self) -> str:
        """Returns the label shown while the connection is being established."""
        return self._label.get_label()

    def set_label(self, label: str):
        """Sets the label shown while the connection is being established."""
        return self._label.set_label(label)


class OverlayWidget(Gtk.Box):
    """Loading widget responsible for displaying loading status
    to the user."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._centered_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)

        self._centered_container.set_valign(Gtk.Align.CENTER)

        self.append(self._centered_container)
        # Adding the background class (which is a GTK class) gives the default
        # background color to this widget. This is needed as otherwise the widget
        # background is transparent, but the intended use of this widget is to
        # hide other widgets while an action is ongoing.
        self.add_css_class("background")
        self.set_visible(False)

    def show(self, widget: Gtk.Widget):  # pylint: disable=arguments-differ
        """Shows the loading screen to the user."""
        self._remove_children_if_any()
        self._centered_container.append(widget)
        super().set_visible(True)

    def show_message(self, message: str):
        """Shows a message using DefaultLoadingWidget"""
        self.show(DefaultLoadingWidget(message))

    def hide(self):  # pylint: disable=arguments-differ
        """Hides the loading widget from the user."""
        self._remove_children_if_any()
        super().set_visible(False)

    def _remove_children_if_any(self):
        first_child = self._centered_container.get_first_child()
        if first_child:
            self._centered_container.remove(first_child)
