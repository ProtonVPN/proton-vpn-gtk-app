"""
This module defines the headerbar widget
that is present at the top of the window.
"""
from gi.repository import Gio
from proton.vpn.app.gtk import Gtk


class HeaderBarWidget(Gtk.HeaderBar):
    """Headerbar widget.
    Allows to customize the headerbar (also known as the title bar),
    by adding custom buttons, icons and text.
    """
    def __init__(self):
        super().__init__()
        self.set_decoration_layout("menu:minimize,close")
        self.set_title("Proton VPN")
        self.set_show_close_button(True)

        self.menu_button_widget = Gtk.MenuButton()
        self._menu_widget = MenuWidget()
        self.menu_button_widget.set_menu_model(self._menu_widget)

        self.pack_start(self.menu_button_widget)

    @property
    def bug_report_action(self):
        """Shortcut property for the report Gtk.SimpleAction"""
        return self._menu_widget.bug_report_action

    @property
    def about_action(self):
        """Shortcut property for the about Gtk.SimpleAction"""
        return self._menu_widget.about_action

    @property
    def quit_action(self):
        """Shortcut property for the quit Gtk.SimpleAction"""
        return self._menu_widget.quit_action


class MenuWidget(Gio.Menu):
    """Custom menu widget that is displayed in the headerbar."""
    def __init__(self):
        super().__init__()
        self.bug_report_action = Gio.SimpleAction.new("report", None)
        self.about_action = Gio.SimpleAction.new("about", None)
        self.quit_action = Gio.SimpleAction.new("quit", None)

        self.append_item(Gio.MenuItem.new("Report an Issue", "win.report"))
        self.append_item(Gio.MenuItem.new("About", "win.about"))
        self.append_item(Gio.MenuItem.new("Exit", "win.quit"))
