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
"""
import dbus

from proton.vpn.app.gtk.widgets.main.tray_icon import (
    _DBusMenuService, MenuObject, MenuType
)


def _menu_service(menu_items):
    # Skip dbus.service.Object.__init__: _build_layout needs no bus.
    service = _DBusMenuService.__new__(_DBusMenuService)
    service.menu_items = menu_items
    service.revision = 0
    return service


def test_get_layout_children_are_variant_arrays_per_dbusmenu_spec():
    """GetLayout returns (ia{sv}av): every children array must be `av`.

    Typing them as a(ia{sv}av) makes each child (ia{sv}a(ia{sv}av)), which
    strict hosts such as Waybar >= 0.16 reject as malformed.
    """
    service = _menu_service([
        MenuObject(id=1, type=MenuType.ITEM, label="Show"),
        MenuObject(id=2, type=MenuType.SEPARATOR, label=""),
        MenuObject(id=3, type=MenuType.ITEM, label="Quit"),
    ])

    _, root_props, root_children = service._build_layout(0, [])

    assert root_children.signature == "v"
    assert [child[0] for child in root_children] == [1, 2, 3]
    for child in root_children:
        assert child[2].signature == "v"


def test_get_layout_root_properties_do_not_leak_internal_children_list():
    service = _menu_service([MenuObject(id=1, type=MenuType.ITEM, label="Quit")])

    _, root_props, _ = service._build_layout(0, [])

    assert "children" not in root_props
    assert root_props["children-display"] == "submenu"


def test_get_layout_for_unknown_parent_returns_empty_variant_array():
    service = _menu_service([])

    parent_id, props, children = service._build_layout(42, [])

    assert parent_id == 42
    assert len(props) == 0
    assert children.signature == "v"
