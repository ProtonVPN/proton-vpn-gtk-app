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


def test_row_content_displays_country_name_when_server_group_is_a_country():
    row_content = RowContent()
    row_content.display(row_data=_row_data(name="United States"))
    assert row_content.label == "United States"


def test_row_content_displays_city_name_when_server_group_is_a_city():
    row_content = RowContent()
    row_content.display(row_data=_row_data(name="Tokyo"))
    assert row_content.label == "Tokyo"


def test_row_content_displays_server_name_when_server_group_is_a_single_server():
    row_content = RowContent()
    row_content.display(row_data=_row_data(name="US#1", toggable=False, load=50))
    assert row_content.label == "US#1"


def test_row_content_displays_toggle_button_when_server_group_is_toggleable():
    row_content = RowContent()
    row_content.display(row_data=_row_data(toggable=True))
    assert row_content.toggle_button.get_visible()


def test_row_content_does_not_display_toggle_button_when_server_group_is_a_single_server():
    row_content = RowContent()
    row_content.display(row_data=_row_data(toggable=False, load=50))
    assert row_content.toggle_button.get_opacity() == 0
    assert not row_content.toggle_button.get_sensitive()


def test_row_content_displays_upgrade_required_link_button_to_free_users_on_non_free_server_groups():
    row_content = RowContent()
    row_content.display(row_data=_row_data(upgrade_required=True))
    assert row_content.action_text == "Upgrade"


def test_row_content_displays_connect_button_to_paid_users_on_paid_server_groups():
    row_content = RowContent()
    row_content.display(row_data=_row_data(upgrade_required=False, toggable=False, load=50))
    assert row_content.action_text == "Connect"


def test_row_content_displays_server_load_when_server_group_is_a_single_server():
    row_content = RowContent()
    row_content.display(row_data=_row_data(toggable=False, load=75))
    assert row_content.server_load == "75%"


def test_row_content_hides_details_and_shows_maintenance_icon_when_under_maintenance():
    row_content = RowContent()
    row_content.display(row_data=_row_data(under_maintenance=True))
    assert row_content.under_maintenance_icon.get_visible()
    assert not row_content.details_visible  # no connect/upgrade button for maintenance rows


def test_row_content_dims_row_when_under_maintenance():
    row_content = RowContent()
    row_content.display(row_data=_row_data(under_maintenance=True))
    assert row_content.has_css_class("dimmed")


def test_row_content_dims_row_when_upgrade_required():
    row_content = RowContent()
    row_content.display(row_data=_row_data(upgrade_required=True))
    assert row_content.has_css_class("dimmed")


def test_row_content_connect_button_calls_on_connect_callback_when_clicked():
    on_connect = Mock()
    row_content = RowContent()
    row_content.display(row_data=_row_data(toggable=False, load=50, on_connect=on_connect))
    row_content.click_action_button()
    on_connect.assert_called_once()


def test_row_content_is_not_dimmed_when_neither_under_maintenance_nor_upgrade_required():
    row_content = RowContent()
    row_content.display(row_data=_row_data(under_maintenance=False, upgrade_required=False))
    assert not row_content.has_css_class("dimmed")
    assert row_content.label_sensitive


def test_row_content_label_sensitive_is_false_when_dimmed():
    row_content = RowContent()
    row_content.display(row_data=_row_data(under_maintenance=True))
    assert not row_content.label_sensitive


def test_row_content_dimmed_class_cleared_on_reset():
    row_content = RowContent()
    row_content.display(row_data=_row_data(under_maintenance=True))
    assert row_content.has_css_class("dimmed")
    row_content.display(row_data=_row_data(under_maintenance=False))
    assert not row_content.has_css_class("dimmed")


def test_row_content_displays_server_features():
    row_content = RowContent()
    row_content.display(row_data=_row_data(
        features={ServerFeatureEnum.P2P, ServerFeatureEnum.TOR},
        smart_routing=True,
    ))

    feature_icons = row_content.get_feature_icons()
    assert len(feature_icons) == 3
    icon_types = [type(icon) for icon in feature_icons]
    assert SmartRoutingIcon in icon_types
    assert P2PIcon in icon_types
    assert TORIcon in icon_types
