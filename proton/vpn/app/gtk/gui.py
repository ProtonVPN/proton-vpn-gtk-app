import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from proton.vpn.app.gtk.view import LoginWindow


class GUI:
    """GUI entry point."""

    def __init__(self, login_window=None):
        self._login_window = login_window or LoginWindow()

    def show(self):
        """Shows the UI to the user."""
        self._login_window.show_all()
        return Gtk.main()
