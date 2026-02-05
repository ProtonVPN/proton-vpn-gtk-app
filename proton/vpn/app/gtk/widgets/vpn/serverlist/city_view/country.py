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
from typing import List, Optional, Tuple

from proton.vpn import logging
from proton.vpn.session.servers import Country, City, TierEnum
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.city import CityRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.header import ServerLocationHeader
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import CountryFlagIcon

logger = logging.getLogger(__name__)


# pylint: disable=duplicate-code
class CountryRow(Gtk.Box):
    """Row representing a country in the server list widget."""
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._country: Optional[Country] = None
        self._header = ServerLocationHeader()
        self.append(self._header)
        self._children_revealer = Gtk.Revealer()
        self._children_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._children_container.set_spacing(5)
        self._children_container.set_margin_top(5)
        self._children_revealer.set_child(self._children_container)
        self.append(self._children_revealer)
        self._controller = None
        self._user_tier = None
        self._connected_signals: List[Tuple[int, Gtk.Widget]] = []

    def display(
        self, controller: Controller, country: Country, user_tier: int,
        connected_server_id: str = None
    ):
        """Displays the country row according to the specified parameters."""
        self.reset()
        self._controller = controller
        self._country = country
        self._user_tier = user_tier

        signal_id = self._header.connect(
            "toggle-children", self._on_toggle_children
        )
        self._connected_signals.append((signal_id, self._header))

        self._header.display(
            controller, country, user_tier,
            CountryFlagIcon(country.code), connected_server_id
        )

    def _on_toggle_children(self, header: ServerLocationHeader):
        self._remove_city_rows()
        if header.expanded:
            self._add_city_rows()
        self._children_revealer.set_reveal_child(
            header.expanded
        )

    def reset(self):
        """Resets the country row to its initial state."""
        for signal_id, widget in self._connected_signals:
            widget.disconnect(signal_id)
        self._connected_signals.clear()

        self._header.reset()
        self._remove_city_rows()

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
        return self._header.expanded

    @expanded.setter
    def expanded(self, value: bool):
        """Expands or collapses the country row (to show/hide its cities)."""
        self._header.expanded = value

    def grab_focus(self):  # pylint: disable=arguments-differ
        """See Gtk.Widget.grab_focus()"""
        self._header.grab_focus()

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
        city_rows = []
        city_row = self._children_container.get_first_child()
        while city_row:
            city_rows.append(city_row)
            city_row = city_row.get_next_sibling()
        return city_rows

    def click_toggle_button(self):
        """Simulates a click on the toggle button to expand/collapse the row."""
        self._header.click_toggle_button()

    def _remove_city_rows(self):
        for city_row in self.city_rows:
            self._children_container.remove(city_row)
            city_row.reset()

    def _add_city_rows(self):
        cities = self._country.cities
        if self._user_tier == TierEnum.FREE and self._country.free:
            # If the current user has a free account, display first the free cities
            cities = chain(self._country.free_cities, self._country.paid_cities)

        for city in cities:
            city_row = CityRow()
            city_row.display(self._controller, city, self._user_tier)
            self._children_container.append(city_row)
