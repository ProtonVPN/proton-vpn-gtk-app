"""
This module includes the Proton VPN GTK application for Linux.
"""
from importlib.metadata import version, PackageNotFoundError
import gi

try:
    __version__ = version("proton-vpn-gtk-app")
except PackageNotFoundError:
    __version__ = "development"

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # pylint: disable=C0413 # noqa: E402

from proton.vpn import logging  # pylint: disable=C0413 # noqa: E402


logging.config(filename="vpn-app")

__all__ = [Gtk]
