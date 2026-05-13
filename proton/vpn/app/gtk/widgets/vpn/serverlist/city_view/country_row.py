"""
This module defines the country rows displayed in the server list widget.


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

from itertools import chain
from typing import List, Optional

from proton.vpn.session.servers import Country, Location, TierEnum
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.location_row import LocationRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.expandable_row import ExpandableRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.row_view_model import RowViewModel
from proton.vpn.app.gtk.utils.assertions import runtime_assert
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.utils \
    import make_connect_callback, sync_rows_with_model_items
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.secure_core_row import SecureCoreRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import CountryFlagIcon


# pylint: disable=too-many-instance-attributes
class CountryRow(Gtk.Box):
    """Row representing a country in the server list widget."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._country: Optional[Country] = None
        self._controller = None
        self._user_tier = None
        self._expanded_groups: set[str] = set()
        self._expandable_row = ExpandableRow(
            on_expand=self._on_expand,
            on_collapse=self._on_collapse,
        )
        self.append(self._expandable_row)
        self._location_row_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._location_row_container.set_spacing(5)
        self._expandable_row.container.append(self._location_row_container)
        self._secure_core_row_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._secure_core_row_container.set_spacing(5)
        self._expandable_row.container.append(self._secure_core_row_container)

        self._location_rows: List[LocationRow] = []
        self._secure_core_row: Optional[SecureCoreRow] = None

    # pylint: disable=too-many-arguments
    def display(
        self, controller: Controller, country: Country, user_tier: int,
        expanded: bool = False, expanded_groups: Optional[set[str]] = None
    ):
        """Displays the country row according to the specified parameters.

        Args:
            controller: The controller instance
            country: The country to display
            user_tier: The user's tier level
            expanded: Whether the country should be expanded (defaults to False)
            expanded_groups: Optional set of child group labels (lowercase)
                that should be expanded
        """
        expanded_groups = expanded_groups or set()
        self.reset(keep_location_rows=expanded)
        self._controller = controller
        self._country = country
        self._user_tier = user_tier
        self._expanded_groups = expanded_groups
        self._expandable_row.connect_toggle()
        upgrade_required = user_tier == TierEnum.FREE and not country.free

        row_data = RowViewModel(
            name=country.name,
            on_connect=make_connect_callback(controller, country.servers, user_tier),
            free=country.free,
            under_maintenance=country.under_maintenance and not upgrade_required,
            features=country.features,
            smart_routing=country.smart_routing,
            toggable=True,
            upgrade_required=upgrade_required,
            icon_factory=lambda c=country: CountryFlagIcon(c.code),
            connect_button_tooltip=(
                f"Upgrade to connect to {country.name}"
                if upgrade_required else
                f"Connect to {country.name}"
            ),
            toggle_button_tooltips=(
                f"Show all locations from {country.name}",
                f"Hide all locations from {country.name}",
            ),
        )
        self._expandable_row.row_content.display(row_data)
        if expanded:
            self._expandable_row.set_expanded(True)

    def _on_expand(self) -> None:
        self._add_location_rows(self._expanded_groups)
        self._add_secure_core_row(expanded=SecureCoreRow.LABEL.lower() in self._expanded_groups)

    def _on_collapse(self) -> None:
        self._remove_location_rows()
        self._remove_secure_core_row()

    def reset(self, keep_location_rows: bool = False):
        """Resets the country row to its initial state."""
        self._expandable_row.reset(keep_children=keep_location_rows)

    @property
    def country_name(self):
        """Returns this row's country name."""
        return self._country.name

    @property
    def country_code(self):
        """Returns this row's country code"""
        return self._country.code

    @property
    def expanded(self):
        """Returns whether the row is currently expanded or not."""
        return self._expandable_row.row_content.expanded

    @expanded.setter
    def expanded(self, value: bool):
        """Expands or collapses the country row (to show/hide its locations)."""
        self._expandable_row.row_content.expanded = value

    def grab_focus(self):  # pylint: disable=arguments-differ
        """See Gtk.Widget.grab_focus()"""
        self._expandable_row.row_content.grab_focus()

    def focus_on_location(self, location_name: str):
        """Focuses on the location in the country."""
        if not self.expanded:
            self.click_toggle_button()

        for location_row in self.location_rows:
            if location_row.label.lower() == location_name.lower():
                location_row.grab_focus()
                return

    @property
    def locations(self) -> List[Location]:
        """Returns the list of locations in the country."""
        runtime_assert(self._country is not None, "Country is not set")
        return self._country.locations

    @property
    def location_rows(self) -> List[LocationRow]:
        """Returns the list of location rows currently displayed."""
        return list(self._location_rows)

    @property
    def secure_core_row(self) -> Optional[SecureCoreRow]:
        """Returns the secure core row currently displayed."""
        return self._secure_core_row

    def click_toggle_button(self):
        """Simulates a click on the toggle button to expand/collapse the row."""
        self._expandable_row.row_content.click_toggle_button()

    def _remove_location_rows(self):
        while self._location_rows:
            location_row = self._location_rows.pop()
            self._location_row_container.remove(location_row)
            location_row.reset()

    def _remove_secure_core_row(self):
        """Removes the secure core row from its container."""
        if self._secure_core_row is not None:
            self._secure_core_row_container.remove(self._secure_core_row)
            self._secure_core_row.reset(keep_children=False)
            self._secure_core_row = None

    def _add_secure_core_row(self, expanded: bool = False):
        """Adds the single Via Secure Core row when the country has secure core servers."""
        runtime_assert(self._country is not None, "Country is not set")

        if not self._country.secure_core_group:
            self._remove_secure_core_row()
            return

        if self._secure_core_row is None:
            self._secure_core_row = SecureCoreRow()
            self._secure_core_row_container.append(self._secure_core_row)

        self._secure_core_row.display(
            self._controller, self._country.secure_core_group, self._user_tier,
            expanded=expanded
        )

    def _add_location_rows(self, expanded_locations: Optional[set[str]] = None):
        """Adds location rows to the country row.

        Args:
            expanded_locations: Optional set of lowercase location names that should be expanded
        """
        expanded_locations = expanded_locations or set()
        runtime_assert(self._country is not None, "Country is not set")

        locations = self._country.locations
        if self._user_tier == TierEnum.FREE and self._country.free:
            # If the current user has a free account, display first the free locations
            locations = list(chain(self._country.free_locations, self._country.paid_locations))

        def display_location_row(location_row, location):
            location_expanded = location.name.lower() in expanded_locations
            location_row.display(
                self._controller, location, self._user_tier, expanded=location_expanded
            )

        sync_rows_with_model_items(
            locations,
            self._location_rows,
            self._location_row_container,
            LocationRow,
            display_location_row
        )
