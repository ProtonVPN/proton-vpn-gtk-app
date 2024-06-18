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

from proton.vpn.app.gtk import Gtk


class Spinner(Gtk.Spinner):
    """Spinner with some default configurations.
    Upon being shown it automatically starts spinning.
    """
    def __init__(self, size: int = 50):
        super().__init__()
        self.set_property("height-request", size)

        self.connect("show", self._on_show_spinner)

    def _on_show_spinner(self, *_):
        self.start()
        super().show()


class BaseLoadingContainerWidget(Gtk.Box):
    """Used mainly to standardize and styling, to reduce boilerplate code.
    """
    def __init__(self, orientation: Gtk.Orientation = Gtk.Orientation.VERTICAL):
        super().__init__(orientation=orientation)
        self.set_spacing(25)


class DefaultLoadingWidget(BaseLoadingContainerWidget):
    """Helper class to be used when only a label is needed
    to be displayed with a spinner."""
    def __init__(self, label: str):
        super().__init__()
        self._label = Gtk.Label.new(label)
        self._spinner = Spinner()

        self.pack_start(self._label, expand=False, fill=False, padding=0)
        self.pack_start(self._spinner, expand=False, fill=False, padding=0)

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
        display_loading_status: Gtk.Widget = None
    ):
        super().__init__()

        self._label = Gtk.Label.new(label)
        self._cancel_button = cancel_button
        self._cancel_button.get_style_context().add_class("danger")
        self._cancel_button.set_halign(Gtk.Align.CENTER)

        if not display_loading_status:
            self._display_loading_status = Spinner()
        else:
            self._display_loading_status = display_loading_status

        self.pack_start(self._label, expand=False, fill=False, padding=0)
        self.pack_start(self._display_loading_status, expand=False, fill=False, padding=0)
        self.pack_start(self._cancel_button, expand=False, fill=False, padding=0)

    def get_label(self) -> str:
        """Returns the label of the object"""
        return self._label.get_label()


class OverlayWidget(Gtk.Box):
    """Loading widget responsible for displaying loading status
    to the user."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._centered_container = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self._centered_container.show()

        self._centered_container.set_valign(Gtk.Align.CENTER)

        self.pack_start(self._centered_container, expand=True, fill=True, padding=0)
        # Adding the background class (which is a GTK class) gives the default
        # background color to this widget. This is needed as otherwise the widget
        # background is transparent, but the intended use of this widget is to
        # hide other widgets while an action is ongoing.
        self.get_style_context().add_class("background")
        self.set_no_show_all(True)

    def show(self, widget: Gtk.Widget):  # pylint: disable=arguments-differ
        """Shows the loading screen to the user."""
        self._centered_container.pack_start(widget, expand=False, fill=False, padding=0)
        widget.show_all()
        super().show()

    def hide(self):  # pylint: disable=arguments-differ
        """Hides the loading widget from the user."""
        # https://lazka.github.io/pgi-docs/Gtk-3.0/classes/Container.html#Gtk.Container.remove
        children = self._centered_container.get_children()
        if children:
            children[0].destroy()

        super().hide()
