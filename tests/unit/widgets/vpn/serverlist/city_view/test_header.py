from unittest.mock import Mock

import pytest

from proton.vpn.session.servers import City, Country, LogicalServer, ServerFeatureEnum, TierEnum
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.header import ServerLocationHeader
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import P2PIcon, SmartRoutingIcon, TORIcon


def test_header_displays_country_name_when_server_group_is_a_country():
    """Test that the header displays the country name when displaying a country."""
    header = ServerLocationHeader()
    header.display(
        controller=Mock(spec=Controller),
        server_group=Country(code="US", servers=[]),
        user_tier=TierEnum.PLUS
    )

    assert header.label == "United States"


def test_header_displays_city_name_when_server_group_is_a_city():
    """Test that the header displays the city name when displaying a city."""
    header = ServerLocationHeader()
    header.display(
        controller=Mock(spec=Controller),
        server_group=City(name="Tokyo", servers=[]),
        user_tier=TierEnum.PLUS
    )

    assert header.label == "Tokyo"


def test_header_displays_server_name_when_server_group_is_a_single_server():
    """Test that the header displays the server name when displaying a server."""
    header = ServerLocationHeader()
    server = LogicalServer({
        "ID": 1,
        "Name": "US#1",
        "Status": 1,
        "Load": 50,
        "Servers": [{"Status": 1}],
        "ExitCountry": "US",
        "City": "New York",
        "Tier": TierEnum.PLUS,
    })
    header.display(
        controller=Mock(spec=Controller),
        server_group=server,
        user_tier=TierEnum.PLUS
    )

    assert header.label == "US#1"


@pytest.mark.parametrize("server_group", [
    Country(code="US", servers=[]),
    City(name="Tokyo", servers=[]),
])
def test_header_displays_toggle_button_when_server_group_is_toggleable(server_group):
    """Test that the toggle button is visible when displaying a country or city."""
    header = ServerLocationHeader()
    header.display(
        controller=Mock(spec=Controller),
        server_group=server_group,
        user_tier=TierEnum.PLUS
    )

    assert header.toggle_button.get_visible()


def test_header_does_not_display_toggle_button_when_server_group_is_a_single_server():
    """Test that the toggle button is not visible when displaying a server."""
    header = ServerLocationHeader()
    server = LogicalServer({
        "ID": 1,
        "Name": "US#1",
        "Status": 1,
        "Load": 50,
        "Servers": [{"Status": 1}],
        "ExitCountry": "US",
        "City": "New York",
        "Tier": TierEnum.PLUS,
    })
    header.display(
        controller=Mock(spec=Controller),
        server_group=server,
        user_tier=TierEnum.PLUS
    )

    assert not header.toggle_button.get_visible()


def test_header_displays_upgrade_required_link_button_to_free_users_on_non_free_server_groups():
    """Test that the upgrade required link button is visible for free users when country is not free."""
    header = ServerLocationHeader()
    # Create a country with only PLUS tier servers (not free)
    plus_server = LogicalServer({
        "ID": 1,
        "Name": "US#1",
        "Status": 1,
        "Load": 50,
        "Servers": [{"Status": 1}],
        "ExitCountry": "US",
        "City": "New York",
        "Tier": TierEnum.PLUS,
    })
    country = Country(code="US", servers=[plus_server])
    header.display(
        controller=Mock(spec=Controller),
        server_group=country,
        user_tier=TierEnum.FREE  # Free user
    )

    assert header.upgrade_required_link_button.get_visible()
    assert not header.connect_button.get_visible()


def test_header_displays_connect_button_to_paid_users_on_paid_server_groups():
    header = ServerLocationHeader()
    plus_server = LogicalServer({
        "ID": 1,
        "Name": "US#1",
        "Status": 1,
        "Load": 50,
        "Servers": [{"Status": 1}],
        "ExitCountry": "US",
        "City": "New York",
        "Tier": TierEnum.PLUS,
    })
    header.display(
        controller=Mock(spec=Controller),
        server_group=plus_server,
        user_tier=TierEnum.PLUS  # Paid user
    )

    assert not header.upgrade_required_link_button.get_visible()
    assert header.connect_button.get_visible()


def test_header_displays_server_load_when_server_group_is_a_single_server():
    """Test that the server load is visible and displays the correct load value when displaying a server."""
    header = ServerLocationHeader()
    server = LogicalServer({
        "ID": 1,
        "Name": "US#1",
        "Status": 1,
        "Load": 75,
        "Servers": [{"Status": 1}],
        "ExitCountry": "US",
        "City": "New York",
        "Tier": TierEnum.PLUS,
    })
    header.display(
        controller=Mock(spec=Controller),
        server_group=server,
        user_tier=TierEnum.PLUS
    )

    assert header.server_load == "75%"


@pytest.mark.parametrize("server_group_factory", [
    lambda server: Country(code="IS", servers=[server]),
    lambda server: City(name="Reykjavik", servers=[server]),
    lambda server: server,
])
def test_header_displays_server_features_for_all_server_groups(server_group_factory):
    """Test that server features (P2P, TOR, Smart Routing) are displayed for all server group types."""
    # Create a server that has P2P and TOR features, and smart routing
    server_with_features = LogicalServer({
        "ID": 1,
        "Name": "IS#1",
        "Status": 1,
        "Load": 50,
        "Servers": [{"Status": 1}],
        "Features": 6,  # 2 (TOR) + 4 (P2P)
        "ExitCountry": "IS",
        "City": "Reykjavik",
        "Tier": TierEnum.PLUS,
        "HostCountry": "US"  # Enables smart routing
    })

    server_group = server_group_factory(server_with_features)
    header = ServerLocationHeader()
    header.display(
        controller=Mock(spec=Controller),
        server_group=server_group,
        user_tier=TierEnum.PLUS
    )

    # Verify that the expected feature icons are displayed (P2P, TOR, SmartRouting)
    feature_icons = header.get_feature_icons()
    assert len(feature_icons) == 3

    # Check that each expected icon type is present
    icon_types = [type(icon) for icon in feature_icons]
    assert SmartRoutingIcon in icon_types
    assert P2PIcon in icon_types
    assert TORIcon in icon_types