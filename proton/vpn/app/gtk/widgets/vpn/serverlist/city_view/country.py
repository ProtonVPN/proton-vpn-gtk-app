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

from proton.vpn.session.servers import Country, City, TierEnum
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.city import CityRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.expandable_row import ExpandableRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.utils \
    import get_children, sync_rows_with_model_items
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.secure_core import SecureCoreRow
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
        self._city_row_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._city_row_container.set_spacing(5)
        self._expandable_row.container.append(self._city_row_container)
        self._secure_core_row_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._secure_core_row_container.set_spacing(5)
        self._expandable_row.container.append(self._secure_core_row_container)

    # pylint: disable=too-many-arguments
    def display(
        self, controller: Controller, country: Country, user_tier: int,
        connected_server_id: str = None, expanded: bool = False,
        expanded_groups: set[str] = None
    ):
        """Displays the country row according to the specified parameters.

        Args:
            controller: The controller instance
            country: The country to display
            user_tier: The user's tier level
            connected_server_id: Optional connected server ID
            expanded: Whether the country should be expanded (defaults to False)
            expanded_groups: Optional set of child group labels (lowercase)
                that should be expanded
        """
        expanded_groups = expanded_groups or set()
        self.reset(keep_city_rows=expanded)
        self._controller = controller
        self._country = country
        self._user_tier = user_tier
        self._expanded_groups = expanded_groups
        self._expandable_row.connect_toggle()
        self._expandable_row.row_content.display(
            controller, country, user_tier,
            CountryFlagIcon(country.code), connected_server_id
        )
        if expanded:
            self._expandable_row.set_expanded(True)

    def _on_expand(self) -> None:
        self._add_city_rows(self._expanded_groups)
        self._add_secure_core_row(expanded=SecureCoreRow.LABEL.lower() in self._expanded_groups)

    def _on_collapse(self) -> None:
        self._remove_city_rows()
        self._remove_secure_core_row()

    def reset(self, keep_city_rows: bool = False):
        """Resets the country row to its initial state."""
        self._expandable_row.reset(keep_children=keep_city_rows)

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
        """Expands or collapses the country row (to show/hide its cities)."""
        self._expandable_row.row_content.expanded = value

    def grab_focus(self):  # pylint: disable=arguments-differ
        """See Gtk.Widget.grab_focus()"""
        self._expandable_row.row_content.grab_focus()

    def focus_on_city(self, city_name: str):
        """Focuses on the city in the country."""
        if not self.expanded:
            self.click_toggle_button()

        for city_row in self.city_rows:
            if city_row.label.lower() == city_name.lower():
                city_row.grab_focus()
                return

    @property
    def cities(self) -> List[City]:
        """Returns the list of cities in the country."""
        return self._country.cities

    @property
    def city_rows(self) -> List[CityRow]:
        """Returns the list of city rows currently displayed."""
        return get_children(self._city_row_container)

    @property
    def secure_core_row(self) -> Optional[SecureCoreRow]:
        """Returns the secure core row currently displayed."""
        return self._secure_core_row_container.get_first_child()

    def click_toggle_button(self):
        """Simulates a click on the toggle button to expand/collapse the row."""
        self._expandable_row.row_content.click_toggle_button()

    def _remove_city_rows(self):
        for city_row in self.city_rows:
            self._city_row_container.remove(city_row)
            city_row.reset()

    def _remove_secure_core_row(self):
        """Removes the secure core row from its container."""
        secure_core_row = self.secure_core_row
        if secure_core_row:
            self._secure_core_row_container.remove(secure_core_row)
            secure_core_row.reset(keep_children=False)

    def _add_secure_core_row(self, expanded: bool = False):
        """Adds the single Via Secure Core row when the country has secure core servers."""
        def display_secure_core_row(secure_core_row, secure_core_group):
            secure_core_row.display(
                self._controller, secure_core_group, self._user_tier,
                expanded=expanded
            )

        sync_rows_with_model_items(
            [self._country.secure_core_group] if self._country.secure_core_group else [],
            [self.secure_core_row] if self.secure_core_row else [],
            self._secure_core_row_container,
            SecureCoreRow,
            display_secure_core_row
        )

    def _add_city_rows(self, expanded_cities: set[str] = None):
        """Adds city rows to the country row.

        Args:
            expanded_cities: Optional set of lowercase city names that should be expanded
        """
        expanded_cities = expanded_cities or set()

        cities = self._country.cities
        if self._user_tier == TierEnum.FREE and self._country.free:
            # If the current user has a free account, display first the free cities
            cities = list(chain(self._country.free_cities, self._country.paid_cities))

        def display_city_row(city_row, city):
            city_expanded = city.name.lower() in expanded_cities
            city_row.display(
                self._controller, city, self._user_tier,
                expanded=city_expanded
            )

        sync_rows_with_model_items(
            cities,
            self.city_rows,
            self._city_row_container,
            CityRow,
            display_city_row
        )
