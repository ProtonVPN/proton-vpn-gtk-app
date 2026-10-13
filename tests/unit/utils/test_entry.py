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



Tests for the clear icons added to text fields.
"""
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.utils.entry import CLEAR_ICON, add_clear_icon, use_clear_icon

SECONDARY = Gtk.EntryIconPosition.SECONDARY


def _icon_file_name(gicon) -> str:
    return gicon.get_file().get_basename() if gicon else ""


def test_clear_icon_is_hidden_while_the_field_is_empty():
    entry = Gtk.Entry()
    add_clear_icon(entry)

    assert entry.get_icon_gicon(SECONDARY) is None


def test_clear_icon_is_shown_once_the_field_has_text():
    entry = Gtk.Entry()
    add_clear_icon(entry)

    entry.set_text("user")

    assert _icon_file_name(entry.get_icon_gicon(SECONDARY)) == CLEAR_ICON


def test_clear_icon_is_shown_for_a_field_that_starts_with_text():
    entry = Gtk.Entry(text="1.1.1.1")
    add_clear_icon(entry)

    assert _icon_file_name(entry.get_icon_gicon(SECONDARY)) == CLEAR_ICON


def test_pressing_the_clear_icon_empties_the_field_and_hides_the_icon():
    entry = Gtk.Entry(text="user")
    add_clear_icon(entry)

    entry.emit("icon-press", SECONDARY)

    assert entry.get_text() == ""
    assert entry.get_icon_gicon(SECONDARY) is None


def test_search_field_clear_button_shows_the_clear_icon():
    search = Gtk.SearchEntry()
    use_clear_icon(search)

    assert _icon_file_name(search.get_last_child().get_gicon()) == CLEAR_ICON
