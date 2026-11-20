"""
Tests for the regions of the world map.


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
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from proton.vpn.app.gtk.widgets.vpn.world_map.regions import (
    ConnectedServer, RegionStatus, build_regions, us_state_of
)

US_STATES = {"TX": "Texas", "NY": "New York", "WY": "Wyoming"}


def server(name, free=False, under_maintenance=False):
    return SimpleNamespace(name=name, free=free, under_maintenance=under_maintenance)


def country(code, servers, free=False, under_maintenance=False):
    return SimpleNamespace(
        code=code, free=free, under_maintenance=under_maintenance,
        locations=[SimpleNamespace(servers=servers)]
    )


def build(countries, upgrade_required=lambda row: False, connected=None):
    return build_regions(
        countries,
        country_name=lambda code: f"name of {code}",
        us_state_names=US_STATES,
        upgrade_required=upgrade_required,
        connect_country=lambda code: ("country", code),
        connect_servers=lambda servers: ("servers", [s.name for s in servers]),
        connected=connected,
    )


@pytest.mark.parametrize("name, state", [
    ("US-TX#12", "TX"),
    ("US-NY#1", "NY"),
    ("US-FREE#3", None),  # free servers are not located in a state
    ("CH-US#1", None),    # secure core server
    ("US#4", None),
    ("FR#1", None),
])
def test_us_state_of_a_server(name, state):
    assert us_state_of(name) == state


def test_country_regions():
    regions = build([
        country("FR", [server("FR#1")]),
        country("SE", [server("SE#1")], under_maintenance=True),
        country("JP", [server("JP#1")]),
    ], upgrade_required=lambda row: row.code == "JP" if hasattr(row, "code") else False)

    assert regions["FR"].status is RegionStatus.AVAILABLE
    assert regions["FR"].name == "name of FR"
    assert regions["FR"].on_connect == ("country", "FR")
    assert regions["SE"].status is RegionStatus.MAINTENANCE
    assert regions["JP"].status is RegionStatus.UPGRADE_REQUIRED


def test_connected_country():
    regions = build(
        [country("FR", [server("FR#1")]), country("SE", [server("SE#1")])],
        connected=ConnectedServer("FR", "FR#1"),
    )

    assert regions["FR"].status is RegionStatus.CONNECTED
    assert regions["SE"].status is RegionStatus.AVAILABLE


def test_no_state_regions_without_us_servers():
    regions = build([country("FR", [server("FR#1")])])

    assert not [key for key in regions if key.startswith("US-")]


def test_us_states_with_servers_connect_to_their_fastest_server():
    regions = build([country("US", [server("US-TX#1"), server("US-TX#2"), server("US-NY#1")])])

    assert regions["US-TX"].status is RegionStatus.AVAILABLE
    assert regions["US-TX"].name == "Texas"
    assert regions["US-TX"].us_state == "TX"
    assert regions["US-TX"].country_code == "US"
    assert regions["US-TX"].on_connect == ("servers", ["US-TX#1", "US-TX#2"])
    assert regions["US-NY"].on_connect == ("servers", ["US-NY#1"])


def test_us_states_without_servers():
    regions = build([country("US", [server("US-TX#1")])])

    assert regions["US-WY"].status is RegionStatus.NO_SERVER
    assert regions["US-WY"].on_connect is None


def test_us_servers_that_are_not_in_a_state_do_not_create_a_state():
    regions = build([country("US", [server("US-TX#1"), server("US-FREE#1"), server("CH-US#1")])])

    assert {key for key in regions if key.startswith("US-")} == {"US-TX", "US-NY", "US-WY"}


def test_us_state_under_maintenance_only_when_all_its_servers_are():
    regions = build([country("US", [
        server("US-TX#1", under_maintenance=True), server("US-TX#2"),
        server("US-NY#1", under_maintenance=True),
    ])])

    assert regions["US-TX"].status is RegionStatus.AVAILABLE
    assert regions["US-NY"].status is RegionStatus.MAINTENANCE


def test_us_state_upgrade_required_is_decided_from_its_own_servers():
    seen = []

    def upgrade_required(row):
        seen.append(row)
        return not row.free

    regions = build(
        [country("US", [server("US-TX#1", free=True), server("US-NY#1")], free=True)],
        upgrade_required=upgrade_required,
    )

    assert regions["US"].status is RegionStatus.AVAILABLE
    assert regions["US-TX"].status is RegionStatus.AVAILABLE
    assert regions["US-NY"].status is RegionStatus.UPGRADE_REQUIRED


def test_only_the_connected_us_state_is_highlighted():
    regions = build(
        [country("US", [server("US-TX#1"), server("US-NY#1")])],
        connected=ConnectedServer("US", "US-TX#1"),
    )

    assert regions["US"].status is RegionStatus.CONNECTED
    assert regions["US-TX"].status is RegionStatus.CONNECTED
    assert regions["US-NY"].status is RegionStatus.AVAILABLE


def test_all_us_states_are_highlighted_when_connected_to_a_us_server_outside_a_state():
    regions = build(
        [country("US", [server("US-TX#1"), server("US-NY#1"), server("US-FREE#1")])],
        connected=ConnectedServer("US", "US-FREE#1"),
    )

    assert regions["US-TX"].status is RegionStatus.CONNECTED
    assert regions["US-NY"].status is RegionStatus.CONNECTED


def test_connection_to_another_country_does_not_highlight_us_states():
    regions = build(
        [country("US", [server("US-TX#1")]), country("FR", [server("FR#1")])],
        connected=ConnectedServer("FR", "FR#1"),
    )

    assert regions["US-TX"].status is RegionStatus.AVAILABLE
