"""
Regions of the world map: availability and connection action of each country
and US state.

This module does not depend on Gtk, so that it can be tested in isolation.


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
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from itertools import chain
from typing import Callable, Dict, Iterable, List, Mapping, NamedTuple, Optional

# Names of the US servers located in a given state: "US-TX#12" -> "TX".
US_STATE_SERVER_NAME = re.compile(r"^US-([A-Z]{2})#\d+$")


class RegionStatus(Enum):
    """What the user can do with a region."""
    AVAILABLE = "available"
    CONNECTED = "connected"
    UPGRADE_REQUIRED = "upgrade-required"
    MAINTENANCE = "maintenance"
    NO_SERVER = "no-server"  # US state in which Proton has no server.


@dataclass(frozen=True)
class Region:
    """
    A country or a US state of the map.

    Attributes:
        key: "UK" for a country, "US-TX" for a US state.
        country_code: code of the country the region belongs to.
        name: localized country name, or US state name.
        status: what the user can do with the region.
        on_connect: connects to the fastest server of the region.
        us_state: postal code of the state, for a US state.
    """
    key: str
    country_code: str
    name: str
    status: RegionStatus
    on_connect: Optional[Callable[[], None]] = None
    us_state: Optional[str] = None


class ConnectedServer(NamedTuple):
    """The server the VPN is currently connected to."""
    country_code: str
    name: str


@dataclass(frozen=True)
class _ServerGroup:
    """Servers located in a US state, seen as a row of the server list."""
    servers: List
    free: bool
    under_maintenance: bool


def us_state_of(server_name: str) -> Optional[str]:
    """Returns the US state a server is located in, from its name (e.g. "US-TX#12")."""
    match = US_STATE_SERVER_NAME.match(server_name)
    return match.group(1) if match else None


def _status(
    connected: bool, upgrade_required: bool, under_maintenance: bool
) -> RegionStatus:
    if connected:
        return RegionStatus.CONNECTED
    if upgrade_required:
        return RegionStatus.UPGRADE_REQUIRED
    if under_maintenance:
        return RegionStatus.MAINTENANCE
    return RegionStatus.AVAILABLE


# pylint: disable=too-many-arguments,too-many-locals
def build_regions(
    countries: Iterable,
    *,
    country_name: Callable[[str], str],
    us_state_names: Mapping[str, str],
    upgrade_required: Callable[[object], bool],
    connect_country: Callable[[str], Callable[[], None]],
    connect_servers: Callable[[List], Callable[[], None]],
    connected: Optional[ConnectedServer] = None,
) -> Dict[str, Region]:
    """
    Builds the regions of the map from the countries of the server list.

    Args:
        countries: ``Country`` objects, grouped by location.
        country_name: returns the localized name of a country given its code.
        us_state_names: US state names, by postal code.
        upgrade_required: whether a server list row (country or group of servers)
            requires an upgrade for the user.
        connect_country: returns the callback connecting to a country.
        connect_servers: returns the callback connecting to the fastest of some servers.
        connected: server the VPN is connected to, if any.

    Returns:
        The regions by key. US states without servers are present with the
        ``NO_SERVER`` status, unless the US are not in the server list.
    """
    regions: Dict[str, Region] = {}
    for country in countries:
        country_connected = bool(connected and connected.country_code == country.code)
        regions[country.code] = Region(
            key=country.code,
            country_code=country.code,
            name=country_name(country.code),
            status=_status(
                country_connected, upgrade_required(country), country.under_maintenance
            ),
            on_connect=connect_country(country.code),
        )
        if country.code != "US":
            continue

        connected_state = us_state_of(connected.name) if country_connected else None
        servers_by_state: Dict[str, List] = {}
        for server in chain.from_iterable(loc.servers for loc in country.locations):
            state = us_state_of(server.name)
            if state:
                servers_by_state.setdefault(state, []).append(server)

        for state, name in us_state_names.items():
            servers = servers_by_state.get(state)
            if not servers:
                regions[f"US-{state}"] = Region(
                    key=f"US-{state}", country_code="US", name=name,
                    status=RegionStatus.NO_SERVER, us_state=state
                )
                continue
            group = _ServerGroup(
                servers=servers,
                free=any(s.free for s in servers),
                under_maintenance=all(s.under_maintenance for s in servers),
            )
            regions[f"US-{state}"] = Region(
                key=f"US-{state}", country_code="US", name=name, us_state=state,
                status=_status(
                    country_connected and connected_state in (None, state),
                    upgrade_required(group), group.under_maintenance
                ),
                on_connect=connect_servers(servers),
            )
    return regions
