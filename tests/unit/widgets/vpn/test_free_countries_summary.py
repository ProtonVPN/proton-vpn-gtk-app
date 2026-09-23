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
from unittest.mock import Mock

import pytest

from proton.vpn.app.gtk.widgets.vpn.free_countries_summary import (
    FreeCountriesSummary,
    free_country_codes,
)

from tests.unit.testing_utils import free_server_list


def _row(free_countries=(), paid_countries=()):
    controller_mock = Mock()
    controller_mock.server_list = free_server_list(free_countries, paid_countries)
    return FreeCountriesSummary(controller_mock), controller_mock


def _listed_countries(row):
    """The country names currently listed in the popover, in display order."""
    names = []
    entry = row.popover.countries_grid.get_first_child()
    while entry is not None:
        names.append(entry.get_last_child().get_text())
        entry = entry.get_next_sibling()
    return names


def test_free_country_codes_only_returns_countries_with_free_servers():
    server_list = free_server_list(["JP", "NL"], paid_countries=["AR", "CH"])

    assert free_country_codes(server_list) == ["JP", "NL"]


def test_free_country_codes_sorts_by_country_name_rather_than_code():
    # By code this would be CH, JP, US; by name it's Japan, Switzerland,
    # United States.
    server_list = free_server_list(["CH", "JP", "US"])

    assert free_country_codes(server_list) == ["JP", "CH", "US"]


def test_free_country_codes_deduplicates_countries_with_several_free_servers():
    server_list = free_server_list(["CH", "CH", "JP"])

    assert free_country_codes(server_list) == ["JP", "CH"]


def test_free_country_codes_does_not_reorder_the_shared_server_list():
    """The server list is shared with the server list widget, which sorts it for
    its own display, so reading the free countries must not disturb it.
    """
    server_list = free_server_list(["US", "DE", "JP"], paid_countries=["AR"])
    order_before = [server.name for server in server_list]

    free_country_codes(server_list)

    assert [server.name for server in server_list] == order_before


@pytest.mark.parametrize("server_list", [None, []])
def test_free_country_codes_without_a_server_list(server_list):
    assert free_country_codes(server_list) == []


@pytest.mark.parametrize("free_countries, expected_label", [
    (["JP", "NL", "US", "CH"], "+1"),
    (["JP", "NL", "US", "CH", "DE", "PL", "RO", "MX"], "+5"),
])
def test_extra_count_label_counts_the_countries_the_icon_does_not_depict(
    free_countries, expected_label
):
    row, _ = _row(free_countries)

    row.refresh()

    assert row.extra_count_label.get_visible() is True
    assert row.extra_count_label.get_label() == expected_label


@pytest.mark.parametrize("free_countries", [[], ["JP"], ["JP", "NL"], ["JP", "NL", "US"]])
def test_extra_count_label_is_hidden_when_the_icon_depicts_every_country(free_countries):
    row, _ = _row(free_countries)

    row.refresh()

    assert row.extra_count_label.get_visible() is False


def test_popover_lists_every_free_country_sorted_by_name():
    row, _ = _row(["US", "JP", "NL"], paid_countries=["AR"])

    row.refresh()

    assert _listed_countries(row) == ["Japan", "Netherlands", "United States"]


def test_popover_lays_the_locations_out_three_per_row():
    """Three fixed columns, so the list can't collapse into one tall column
    that overflows the popover.
    """
    row, _ = _row(["US", "JP", "PL", "NL", "RO", "MX", "SG", "CA", "NO", "CH"])

    row.refresh()

    grid = row.popover.countries_grid
    entries_per_row = {}
    entry = grid.get_first_child()
    while entry is not None:
        row_index = grid.query_child(entry)[1]
        entries_per_row[row_index] = entries_per_row.get(row_index, 0) + 1
        entry = entry.get_next_sibling()

    assert [entries_per_row[index] for index in sorted(entries_per_row)] == [3, 3, 3, 1]


def test_popover_counts_the_free_countries():
    row, _ = _row(["US", "JP", "NL"])

    row.refresh()

    assert row.popover.count_label.get_label() == "Free server locations (3)"


def test_popover_lists_nothing_without_a_server_list():
    row, controller_mock = _row()
    controller_mock.server_list = None

    row.refresh()

    assert _listed_countries(row) == []
    assert row.popover.count_label.get_label() == "Free server locations (0)"


def test_refreshing_again_does_not_duplicate_the_listed_countries():
    """refresh() runs on every disconnected update, with the same countries
    each time, so it has to replace the list rather than add to it.
    """
    row, _ = _row(["JP", "NL"])

    row.refresh()
    row.refresh()

    assert _listed_countries(row) == ["Japan", "Netherlands"]


def test_unknown_country_code_is_listed_with_its_code():
    """An unrecognised code has no localized name, so it's listed as itself."""
    row, _ = _row(["ZZ", "JP"])

    row.refresh()

    assert _listed_countries(row) == ["Japan", "ZZ"]
