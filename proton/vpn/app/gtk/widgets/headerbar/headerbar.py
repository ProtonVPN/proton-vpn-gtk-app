"""
This module defines the headerbar widget
that is present at the top of the window.
"""
from typing import TYPE_CHECKING

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.menu import Menu

if TYPE_CHECKING:
    from proton.vpn.app.gtk.app import MainWindow


class HeaderBar(Gtk.HeaderBar):
    """
    Allows to customize the header bar (also known as the title bar),
    by adding custom buttons, icons and text.
    """

    def __init__(self, controller: Controller, main_window: "MainWindow"):
        super().__init__()

        self.set_decoration_layout("menu:minimize,close")
        self.set_title("Proton VPN")
        self.set_show_close_button(True)

        menu_button = Gtk.MenuButton()
        self.menu = Menu(controller=controller, main_window=main_window)
        menu_button.set_menu_model(self.menu)
        self.pack_start(menu_button)
