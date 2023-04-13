"""
This module defines the headerbar widget
that is present at the top of the window.


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
from typing import TYPE_CHECKING

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.menu import Menu
from proton.vpn.app.gtk.widgets.main.notifications import Notifications

if TYPE_CHECKING:
    from proton.vpn.app.gtk.app import MainWindow


class HeaderBar(Gtk.HeaderBar):
    """
    Allows to customize the header bar (also known as the title bar),
    by adding custom buttons, icons and text.
    """

    def __init__(
            self,
            controller: Controller,
            main_window: "MainWindow",
            notifications: Notifications
    ):
        super().__init__()

        self.set_decoration_layout("menu:minimize,close")
        self.set_title("Proton VPN")
        self.set_show_close_button(True)

        menu_button = Gtk.MenuButton()
        self.menu = Menu(
            controller=controller,
            main_window=main_window,
            notifications=notifications
        )
        menu_button.set_menu_model(self.menu)
        self.pack_start(menu_button)
