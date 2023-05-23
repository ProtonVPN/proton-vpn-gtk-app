"""Utils used to increase accessibility on the app."""

from typing import List, Tuple

from gi.repository import Atk, Gtk


def add_widget_relationships(
        target_widget, relationships: List[Tuple[Gtk.Widget, Atk.RelationType]]):
    """Screen readers use these relationships to add information to the server row button."""
    for related_widget, relation_type in relationships:
        target_widget.get_accessible().add_relationship(
            relation_type, related_widget.get_accessible()
        )
