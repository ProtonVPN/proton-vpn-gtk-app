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
from typing import Callable, List, Optional

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
COLUMN_SENSITIVE = 1  # Whether the item is sensitive to selection.


class FilteredList(Gtk.TreeView):
    """
    Displays a list of countries and servers in a tree view.
    """
    def __init__(self,
                 countries: Callable[[Optional[str]], List[str]],
                 servers: Callable[[Optional[str]], List[str]]
                 ):
        super().__init__()
        self._countries = countries
        self._servers = servers
        self._model = Gtk.TreeStore(str, bool)
        self.set_model(Gtk.TreeModelSort(model=self._model))

        self.set_show_expanders(False)
        self.set_activate_on_single_click(True)

        def select_function(_treeselection, model, path, _current):
            tree_iter = model.get_iter(path)
            if tree_iter:
                sensitivity = model.get_value(tree_iter, COLUMN_SENSITIVE)
                return sensitivity

            return False
        self.get_selection().set_select_function(select_function)

        column = Gtk.TreeViewColumn(cell_renderer=Gtk.CellRendererText(),
                                    text=0, sensitive=1)
        self.append_column(column)
        column.set_sort_column_id(0)

        self.set_headers_visible(False)

    def update(self, search_text: str = None):
        """Rebuild the view using the search_text as a filter"""
        self._model.clear()

        sections = (
            ("Countries", self._countries),
            ("Servers", self._servers)
        )

        for section in sections:
            section_name, section_data = section
            data = list(section_data(search_text))
            if data:
                row = [f"{section_name} ({len(data)})", False]
                root = self._model.append(None, row)
                for i, item in enumerate(data):
                    self._model.append(root, [item, True])
                    if i == MAX_SEARCH_RESULTS_PER_SECTION:
                        self._model.append(None, ["...", False])
                        break

        self.expand_all()


class SearchResults(Gtk.ScrolledWindow):
    """Display a filtered view of countries and servers.
       Inside a scroll-able widget.
    """
    def __init__(self, controller):
        super().__init__()
        self.set_policy(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self.set_vexpand(False)
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self._container)
        self.set_property("height-request", 200)

        self._revealer = None

        def countries(search_text: str = None):
            result = set({})
            server_list = controller.server_list
            if server_list:
                for server in controller.server_list:
                    if search_text and (search_text in server.entry_country_name.lower()):
                        result.add(server.entry_country_name)
            return result

        def servers(search_text: str = None):
            server_list = controller.server_list
            if server_list:
                for server in controller.server_list:
                    if search_text and (search_text in server.name.lower()):
                        yield server.name

        self._filtered_country_list = FilteredList(countries, servers)
        self._filtered_country_list.connect("row-activated",
                                            self._on_row_activated)

        self._container.pack_start(self._filtered_country_list, expand=True,
                                   fill=True, padding=0)

    @GObject.Signal(name="result-chosen", arg_types=(str,))
    def result_chosen(self, _row: str):
        """Broadcast that a result has been chosen in the search results."""

    def on_search_changed(self, search_widget: Gtk.SearchEntry, revealer: Gtk.Revealer):
        """Callback when search entry has changed."""
        search_text = search_widget.get_text().lower()
        self._revealer = revealer

        self._filtered_country_list.update(search_text)

        if search_text:
            self._revealer.set_reveal_child(True)
        elif self._revealer:
            self._revealer.set_reveal_child(False)

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
