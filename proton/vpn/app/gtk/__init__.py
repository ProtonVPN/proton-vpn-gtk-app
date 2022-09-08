"""
This module includes the Proton VPN GTK application for Linux.
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # pylint: disable=C0413 # noqa: E402

__all__ = [Gtk]
