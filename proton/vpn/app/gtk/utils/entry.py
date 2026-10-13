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

Clear (×) icons for text fields.
"""
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.assets import icons
from proton.vpn.app.gtk.translator import C_
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect

CLEAR_ICON = "cross-symbolic.svg"
# Names the icon that empties a text field.
CLEAR_LABEL = C_("tooltip", "Clear")

_ENABLED = True


def disable_clear_icons() -> None:
    """Make add_clear_icon() and use_clear_icon() leave fields unchanged."""
    global _ENABLED  # pylint: disable=global-statement
    _ENABLED = False


def add_clear_icon(entry: Gtk.Entry) -> None:
    """Show a clear icon in `entry` while it has text. Pressing it empties the field."""
    if not _ENABLED:
        return

    safe_signal_connect(entry, "notify::text", _update_clear_icon)
    safe_signal_connect(entry, "icon-press", _on_icon_press)
    _update_clear_icon(entry)


def _update_clear_icon(entry: Gtk.Entry, *_) -> None:
    if not entry.get_text():
        entry.set_icon_from_gicon(Gtk.EntryIconPosition.SECONDARY, None)
        return
    entry.set_icon_from_gicon(Gtk.EntryIconPosition.SECONDARY, icons.file_icon(CLEAR_ICON))
    entry.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, CLEAR_LABEL)


def _on_icon_press(entry: Gtk.Entry, position: Gtk.EntryIconPosition) -> None:
    if position == Gtk.EntryIconPosition.SECONDARY:
        entry.set_text("")


def use_clear_icon(search_entry: Gtk.SearchEntry) -> None:
    """Show the clear icon on a search field's own clear button.

    The search field already shows the button while it has text and empties
    itself when it's pressed; only the icon changes. The button is the field's
    last child.
    """
    if not _ENABLED:
        return

    clear_button = search_entry.get_last_child()
    if isinstance(clear_button, Gtk.Image):
        clear_button.set_from_gicon(icons.file_icon(CLEAR_ICON))
