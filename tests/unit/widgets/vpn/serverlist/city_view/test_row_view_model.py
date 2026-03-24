from unittest.mock import Mock

import pytest

from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.row_view_model import RowViewModel


def test_row_view_model_raises_when_toggable_without_tooltips():
    with pytest.raises(ValueError, match="toggle_button_tooltips"):
        RowViewModel(
            name="test", on_connect=Mock(), free=True, under_maintenance=False,
            features=set(), smart_routing=False, toggable=True,
            connect_button_tooltip="Connect", toggle_button_tooltips=None,
        )


def test_row_view_model_accepts_toggable_with_tooltips():
    vm = RowViewModel(
        name="test", on_connect=Mock(), free=True, under_maintenance=False,
        features=set(), smart_routing=False, toggable=True,
        connect_button_tooltip="Connect",
        toggle_button_tooltips=("Show", "Hide"),
    )
    assert vm.toggle_button_tooltips == ("Show", "Hide")


def test_row_view_model_raises_when_tooltips_tuple_has_wrong_length():
    with pytest.raises(ValueError, match="exactly 2"):
        RowViewModel(
            name="test", on_connect=Mock(), free=True, under_maintenance=False,
            features=set(), smart_routing=False, toggable=True,
            connect_button_tooltip="Connect",
            toggle_button_tooltips=("Show",),
        )


def test_row_view_model_raises_when_secure_core_countries_tuple_has_wrong_length():
    with pytest.raises(ValueError, match="exactly 2"):
        RowViewModel(
            name="test", on_connect=Mock(), free=True, under_maintenance=False,
            features=set(), smart_routing=False, toggable=False,
            connect_button_tooltip="Connect",
            secure_core_countries=("Switzerland",),
        )


def test_row_view_model_accepts_non_toggable_without_tooltips():
    vm = RowViewModel(
        name="test", on_connect=Mock(), free=True, under_maintenance=False,
        features=set(), smart_routing=False, toggable=False,
        connect_button_tooltip="Connect", toggle_button_tooltips=None,
    )
    assert vm.toggle_button_tooltips is None
