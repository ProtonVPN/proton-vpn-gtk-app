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

from proton.vpn.session.servers import Country, Location, TierEnum

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.utils import (
    FREE_RESCOPE_FLAG,
    upgrade_required_for_row,
    upgrade_required_unless_free_country_row,
    upgrade_required_when_row_not_free,
)


@pytest.mark.parametrize("user_tier, row_is_free, expected", [
    (TierEnum.FREE, True, False),
    (TierEnum.FREE, False, True),
    (TierEnum.PLUS, True, False),
    (TierEnum.PLUS, False, False),
])
def test_upgrade_required_when_row_not_free(user_tier, row_is_free, expected):
    """Current behavior: upgrade is only required when the row itself isn't free."""
    assert upgrade_required_when_row_not_free(user_tier, row_is_free) is expected


def _row(spec, free):
    row = Mock(spec=spec)
    row.free = free
    return row


@pytest.mark.parametrize("user_tier, row, expected", [
    # Non-country rows: always require upgrade for free-tier users, regardless of free.
    (TierEnum.FREE, _row(Location, True), True),
    (TierEnum.FREE, _row(Location, False), True),
    (TierEnum.PLUS, _row(Location, True), False),
    (TierEnum.PLUS, _row(Location, False), False),
    # Country rows are the exception: they keep using the standard per-row-free formula.
    (TierEnum.FREE, _row(Country, True), False),
    (TierEnum.FREE, _row(Country, False), True),
    (TierEnum.PLUS, _row(Country, True), False),
    (TierEnum.PLUS, _row(Country, False), False),
])
def test_upgrade_required_unless_free_country_row(user_tier, row, expected):
    """New behavior: only country rows are directly connectable for free-tier users."""
    assert upgrade_required_unless_free_country_row(user_tier, row) is expected


def test_upgrade_required_for_row_delegates_to_per_row_policy_when_flag_disabled():
    controller = Mock(spec=Controller)
    controller.feature_flags.get.return_value = False
    row = _row(Location, True)

    assert upgrade_required_for_row(controller, TierEnum.FREE, row) is False
    controller.feature_flags.get.assert_called_once_with(FREE_RESCOPE_FLAG)


def test_upgrade_required_for_row_delegates_to_unless_country_policy_when_flag_enabled():
    controller = Mock(spec=Controller)
    controller.feature_flags.get.return_value = True
    row = _row(Location, True)

    assert upgrade_required_for_row(controller, TierEnum.FREE, row) is True
    controller.feature_flags.get.assert_called_once_with(FREE_RESCOPE_FLAG)


def test_upgrade_required_for_row_preserves_country_connectability_when_flag_enabled():
    """Country rows must stay connectable for free-tier users even when the
    FreeRescope flag is enabled"""
    controller = Mock(spec=Controller)
    controller.feature_flags.get.return_value = True
    free_country = _row(Country, True)

    assert upgrade_required_for_row(controller, TierEnum.FREE, free_country) is False
