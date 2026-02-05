"""
Server search results module.


Copyright (c) 2023 Proton AG

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
from typing import Callable, List, Optional, Set, Tuple, Generator

from gi.repository import GObject

from proton.vpn.app.gtk import Gtk
from proton.vpn import logging

logger = logging.getLogger(__name__)

# We're hittig a bug in the GTK treeview where x11 crashes with BadAlloc
# if we try to display > 1500 rows in certain configurations.
# This avoids the issue by limiting the number of results displayed.
# This is ultimately a better user experience as the whole point of
# the search is to find a specific item.
MAX_SEARCH_RESULTS_PER_SECTION = 100

# Column indexes in the tree model for the FilteredList.
COLUMN_NAME = 0  # The name of the item.
COLUMN_LOAD = 1  # The server load
COLUMN_LOAD_COLOR = 2  # Sets the column color.
COLUMN_SENSITIVE = 3  # Whether the item is sensitive to selection.
LOAD_COLOR = "Grey"  # We want to show the load % in grey.


class FilteredList(Gtk.TreeView):
    """
    Displays a list of countries, cities and servers in a tree view.
    """
    def __init__(
        self,
        countries: Callable[[Optional[str]], List[(str, int)]],
        cities: Callable[[Optional[str]], List[(str, int)]],
        servers: Callable[[Optional[str]], List[(str, int)]]
    ):
        super().__init__()
        self._countries = countries
        self._cities = cities
        self._servers = servers
        self._model = Gtk.TreeStore(str, str, str, bool)
        self.set_model(Gtk.TreeModelSort(model=self._model))

        self.set_show_expanders(False)
        self.set_activate_on_single_click(True)

        def select_function(
            _treeselection: Gtk.TreeSelection,
            model: Gtk.TreeModel,
            path: Gtk.TreePath,
            _current: bool
        ) -> bool:
            tree_iter = model.get_iter(path)
            if not tree_iter:
                return False

            sensitivity = model.get_value(tree_iter, COLUMN_SENSITIVE)
            return sensitivity

        self.get_selection().set_select_function(select_function)

        # server name
        name_column = Gtk.TreeViewColumn(
            "Name",
            cell_renderer=Gtk.CellRendererText(),
            text=COLUMN_NAME,
            sensitive=COLUMN_SENSITIVE
        )

        self.append_column(name_column)

        # server load
        load_column = Gtk.TreeViewColumn(
            "Load",
            cell_renderer=Gtk.CellRendererText(),
            text=COLUMN_LOAD,
            sensitive=COLUMN_SENSITIVE,
            foreground=COLUMN_LOAD_COLOR
        )

        self.append_column(load_column)

        self.set_headers_visible(False)

    def update(self, search_text: str = None):
        """Rebuild the view using the search_text as a filter"""
        self._model.clear()

        sections = (
            ("Countries", self._countries),
            ("Cities", self._cities),
            ("Servers", self._servers)
        )

        for section in sections:
            section_name, section_data = section
            data = list(section_data(search_text))
            if not data:
                continue

            row = [f"{section_name} ({len(data)})", "", LOAD_COLOR, False]
            root = self._model.append(None, row)
            for i, (name, load) in enumerate(data):
                load_string = "" if load is None else f"{load}%"
                self._model.append(
                    root,
                    [name, load_string, LOAD_COLOR, True]
                )
                if i == MAX_SEARCH_RESULTS_PER_SECTION:
                    self._model.append(
                        None,
                        ["...", "", LOAD_COLOR, False]
                    )
                    break

        self.expand_all()


class SearchResults(Gtk.ScrolledWindow):
    """Display a filtered view of countries and servers.
       Inside a scroll-able widget.
    """
    def __init__(self, controller, city_view_enabled: bool):
        super().__init__()
        self.set_policy(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self.set_vexpand(False)
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self._container)
        self.set_property("height-request", 200)

        self._revealer = None

        def countries(search_text: str = None) -> Set(Optional[Tuple[str, None]]):
            result = set({})
            server_list = controller.server_list

            if not server_list:
                return result

            for server in controller.server_list:
                if self._search_input_exists(search_text, server, entry_country_name=True):
                    result.add((server.entry_country_name, None))

            return result

        if city_view_enabled:
            def cities(search_text: str = None) -> Generator[Tuple[Optional[str], Optional[int]]]:
                result = set({})
                server_list = controller.server_list

                if not server_list:
                    yield (None, None)

                for server in controller.server_list:
                    if self._search_input_exists(search_text, server, city_name=True):
                        city_name = server.city
                        if city_name:
                            result.add(city_name)

                for city_name in sorted(result):
                    yield (city_name, None)
        else:
            def cities(search_text: str = None) -> None:  # pylint: disable=unused-argument
                return set({})

        def servers(search_text: str = None) -> Generator[Tuple[Optional[str], Optional[int]]]:
            def user_tier_allows_access_to_server(server_tier: int, user_tier: int) -> bool:
                return server_tier <= user_tier

            user_tier = controller.user_tier
            server_list = controller.server_list
            if not server_list:
                yield (None, None)

            for server in controller.server_list:
                if not user_tier_allows_access_to_server(server.tier, user_tier):
                    continue

                if self._search_input_exists(search_text, server, server_name=True):
                    yield (server.name, server.load)

        self._filtered_country_list = FilteredList(countries, cities, servers)
        self._filtered_country_list.connect(
            "row-activated", self._on_row_activated
        )

        self._container.append(self._filtered_country_list)

    def _search_input_exists(  # pylint: disable=too-many-arguments
        self, search_text: str, server, entry_country_name: bool = False,
        city_name: bool = False, server_name: bool = False
    ) -> bool:
        if entry_country_name:
            return search_text and (search_text in server.entry_country_name.lower())

        if city_name:
            return search_text and server.city and (search_text in server.city.lower())

        if server_name:
            return search_text and (search_text in server.name.lower())

        return None

    @GObject.Signal(name="result-chosen", arg_types=(str,))
    def result_chosen(self, _row: str):
        """Broadcast that a result has been chosen in the search results."""

    def on_search_changed(self, search_widget: Gtk.SearchEntry, revealer: Gtk.Revealer):
        """Callback when search entry has changed."""
        search_text = search_widget.get_text().lower()
        self._revealer = revealer

        self._filtered_country_list.update(search_text)
        self._revealer.set_reveal_child(bool(search_text))

    def _on_row_activated(
        self,
        tree_view: FilteredList,
        path: Gtk.TreePath,
        _tree_view_column: Gtk.TreeViewColumn
    ):
        model = tree_view.get_model()
        tree_iter = model.get_iter(path)
        if tree_iter:
            selected_value = model.get_value(tree_iter, COLUMN_NAME)
            self._revealer.set_reveal_child(False)
            self.emit("result-chosen", selected_value)
