"""
Copyright (c) 2026 Proton AG

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


Demo factories for the loading overlay that covers the window while an action
is in progress.
"""
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo.framing import framed_like_app
from proton.vpn.app.gtk.demo.registry import register_demo
from proton.vpn.app.gtk.widgets.main.loading_widget import (
    DefaultLoadingWidget,
    LoadingConnectionWidget,
    OverlayWidget,
)


def _overlay(content: Gtk.Widget) -> Gtk.Widget:
    overlay = OverlayWidget()
    overlay.show(content)
    return framed_like_app(overlay, fill_height=True)


@register_demo("loading", label="message")
def loading_message() -> Gtk.Widget:
    """The overlay with a message and a spinner (e.g. waiting for a security key)."""
    return _overlay(DefaultLoadingWidget(
        "If your security key has a button or a gold disc, tap it now."
    ))


@register_demo("loading", label="connecting")
def loading_connecting() -> Gtk.Widget:
    """The overlay while connecting, with a button to cancel."""
    return _overlay(LoadingConnectionWidget(
        "Connecting to Switzerland...", Gtk.Button(label="Cancel Connection")
    ))
