"""
Server search entry module.
"""
from __future__ import annotations

import time

from gi.repository import GObject

from proton.vpn import logging

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.vpn.serverlist.serverlist import ServerListWidget
from proton.vpn.app.gtk.utils.search import normalize

logger = logging.getLogger(__name__)


class SearchEntry(Gtk.SearchEntry):
    """Widget used to filter server list based on user input."""
    def __init__(self, server_list_widget: ServerListWidget):
        super().__init__()
        self._server_list_widget = server_list_widget
        self._server_list_widget.connect("ui-updated", lambda _: self.reset())
        self.set_placeholder_text("Press Ctrl+F to search")
        self.connect("search-changed", self._filter_list)
        self.connect("request-focus", lambda _: self.grab_focus())
        self.connect("unrealize", lambda _: self.reset())

    @GObject.Signal(name="request_focus", flags=GObject.SignalFlags.ACTION)
    def request_focus(self, _):
        """Emitting this signal requests input focus on the search text entry."""

    @GObject.Signal(name="search-complete")
    def search_complete(self):
        """Signal emitted after the UI finalized redrawing the UI after a search request."""

    def reset(self):
        """Resets the widget UI."""
        self.set_text("")

    def _filter_list(self, *_):
        start_time = time.time()
        entry_text = normalize(self.get_text())

        for country_row in self._server_list_widget.country_rows:
            country_match = entry_text in country_row.header_searchable_content

            server_match = False
            for server_row in country_row.server_rows:
                # Show server rows if they match the search text, or if they belong to
                # a country that matches the search text. Otherwise, hide them.
                server_row_visible = entry_text in server_row.searchable_content
                server_row.set_visible(server_row_visible or country_match)
                if server_row_visible and entry_text:
                    server_match = True

            # If there was at least a server in the current country row matching
            # the search text then expand country servers. Otherwise, collapse them.
            country_row.set_servers_visibility(server_match)

            # Show the whole country row if there was either a server match or
            # a country match. Otherwise, hide it.
            country_row.set_visible(server_match or country_match)

        self.emit("search-complete")
        end_time = time.time()
        logger.info(f"Search for '{entry_text}' done in {(end_time - start_time) * 1000:.2f} ms.")
