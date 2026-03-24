from unittest.mock import Mock

import pytest

from proton.vpn.session.servers import ServerFeatureEnum, TierEnum
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.row_content import RowContent
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.row_view_model import RowViewModel
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import P2PIcon, SmartRoutingIcon, TORIcon


def _row_data(**kwargs) -> RowViewModel:
    """Helper to build a RowViewModel with sensible defaults."""
    defaults = dict(
        name="test",
        on_connect=Mock(),
        free=True,
        under_maintenance=False,
        features=set(),
        smart_routing=False,
        toggable=True,
        connect_button_tooltip="Connect to test",
        upgrade_required=False,
        toggle_button_tooltips=("Show all servers from test", "Hide all servers from test"),
    )
    defaults.update(kwargs)
    return RowViewModel(**defaults)


def test_header_displays_country_name_when_server_group_is_a_country():
    header = RowContent()
    header.display(row_data=_row_data(name="United States"))
    assert header.label == "United States"


def test_header_displays_city_name_when_server_group_is_a_city():
    header = RowContent()
    header.display(row_data=_row_data(name="Tokyo"))
    assert header.label == "Tokyo"


def test_header_displays_server_name_when_server_group_is_a_single_server():
    header = RowContent()
    header.display(row_data=_row_data(name="US#1", toggable=False, load=50))
    assert header.label == "US#1"


def test_header_displays_toggle_button_when_server_group_is_toggleable():
    header = RowContent()
    header.display(row_data=_row_data(toggable=True))
    assert header.toggle_button.get_visible()


def test_header_does_not_display_toggle_button_when_server_group_is_a_single_server():
    header = RowContent()
    header.display(row_data=_row_data(toggable=False, load=50))
    assert not header.toggle_button.get_visible()


def test_header_displays_upgrade_required_link_button_to_free_users_on_non_free_server_groups():
    header = RowContent()
    header.display(row_data=_row_data(upgrade_required=True))
    assert header.upgrade_required_link_button.get_visible()
    assert not header.connect_button.get_visible()


def test_header_displays_connect_button_to_paid_users_on_paid_server_groups():
    header = RowContent()
    header.display(row_data=_row_data(upgrade_required=False, toggable=False, load=50))
    assert not header.upgrade_required_link_button.get_visible()
    assert header.connect_button.get_visible()


def test_header_displays_server_load_when_server_group_is_a_single_server():
    header = RowContent()
    header.display(row_data=_row_data(toggable=False, load=75))
    assert header.server_load == "75%"


def test_header_displays_server_features():
    header = RowContent()
    header.display(row_data=_row_data(
        features={ServerFeatureEnum.P2P, ServerFeatureEnum.TOR},
        smart_routing=True,
    ))

    feature_icons = header.get_feature_icons()
    assert len(feature_icons) == 3
    icon_types = [type(icon) for icon in feature_icons]
    assert SmartRoutingIcon in icon_types
    assert P2PIcon in icon_types
    assert TORIcon in icon_types
