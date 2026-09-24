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


announce_available = gtk_version >= Version("4.14.0")
if not announce_available:
    logger.warning(
        "Upgrade for better UI accessibility. "
        "Gtk.Accessible.announce requires GTK >= 4.14.0"
    )


def for_speech(text: str) -> str:
    """Returns text without trailing full stops, ellipses or spaces."""
    return text.rstrip(" .\u2026")


def announce(widget: Gtk.Widget, message: str, urgent: bool = False):
    """Asks the screen reader to speak a message, without moving focus.

    Issued from the toplevel window: GTK drops announcements from widgets
    with no registered AT-SPI context, which includes the non-focusable
    labels this is called on behalf of.

    :param urgent: cut into current speech rather than queue behind it.
    """
    root = widget.get_root()
    if not isinstance(root, Gtk.Window):
        return

    if announce_available:
        # Priority is honoured from Orca 49. Orca 43 and 46 ignore it, so
        # it is inert rather than wrong on those.
        root.announce(
            message,
            Gtk.AccessibleAnnouncementPriority.HIGH if urgent
            else Gtk.AccessibleAnnouncementPriority.MEDIUM
        )
        return

    # GTK < 4.14 has no announce(). A screen reader speaks accessible-name
    # changes on the active window, so the message goes there instead. The
    # visible title is untouched, but the window then reads as its status
    # rather than "Proton VPN", at launch and on any switch back to it.
    root.update_property([Gtk.AccessibleProperty.LABEL], [message])


def reset_announcements(widget: Gtk.Widget):
    """Puts the window's accessible name back to its title.

    A no-op where announce() is available, as that path never touches the
    window. Only call it after announce() has been used: writing the name of
    an active window is itself announced, so an unnecessary call would have
    the app name read out.
    """
    if announce_available:
        return

    root = widget.get_root()
    if not isinstance(root, Gtk.Window):
        return

    root.update_property([Gtk.AccessibleProperty.LABEL], [root.get_title()])
