"""Utils used to increase accessibility on the app."""

from typing import List, Union
from packaging.version import Version

from proton.vpn.app.gtk import Gtk

from proton.vpn import logging

logger = logging.getLogger(__name__)


gtk_version = Version(
    f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
)
accessible_list_available = gtk_version >= Version("4.14.0")
if not accessible_list_available:
    logger.warning(
        "Upgrade for better UI accessibility. "
        "Gtk.AccessibleList requires GTK >= 4.14.0"
    )


def add_accessibility(
        target_widget: Gtk.Widget,
        relation_type: Gtk.AccessibleRelation,
        related_widgets: Union[Gtk.Widget, List[Gtk.Widget]]
):
    """Screen readers use these relationships to add information to the target widget."""
    if not accessible_list_available:
        return

    if isinstance(related_widgets, Gtk.Widget):
        related_widgets = [related_widgets]
    related_widgets = [Gtk.AccessibleList.new_from_list(related_widgets)]
    relation_types = [relation_type]
    target_widget.update_relation(relation_types, related_widgets)


def remove_accessibility(
        target_widget: Gtk.Widget,
        relation_type: Gtk.AccessibleRelation
):
    """Removes accessibility relations from the target widget."""
    if not accessible_list_available:
        return

    # Remove relation by setting it to an empty list
    relation_types = [relation_type]
    empty_list = [Gtk.AccessibleList.new_from_list([])]
    target_widget.update_relation(relation_types, empty_list)
