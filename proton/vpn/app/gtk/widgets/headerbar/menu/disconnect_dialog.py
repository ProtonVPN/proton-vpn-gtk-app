"""
Module for the disconnect dialog that prompts the user for confirmation
upon logout or exit.


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
from typing import List, Tuple

from proton.vpn.app.gtk import Gtk
from proton.vpn import logging

logger = logging.getLogger(__name__)


class DisconnectDialog(Gtk.Dialog):
    """Base disconnect dialog widget.
    Since the behaviours on_logout and on_quit are exactly the same
    with just differences of context, this class serves as base for both
    occasions.
    """
    WIDTH = 150
    HEIGHT = 200
    TITLE = "Active connection found"

    def __init__(
        self,
        message: str,
        buttons: List[Tuple[str, Gtk.ResponseType]] = None,
    ):
        super().__init__()
        self.set_title(self.TITLE)
        self.set_default_size(self.WIDTH, self.HEIGHT)

        if not buttons:
            buttons = [
                ("_Yes", Gtk.ResponseType.YES),
                ("_No", Gtk.ResponseType.NO)
            ]

        for button_tuple in buttons:
            self.add_button(button_tuple[0], button_tuple[1])

        label = Gtk.Label(label=message)

        # By default Gtk.Dialog has a vertical box child (Gtk.Box) `vbox`
        self.vbox.set_border_width(20)  # pylint: disable=no-member
        self.vbox.set_spacing(20)  # pylint: disable=no-member
        self.vbox.add(label)  # pylint: disable=no-member
        self.connect("realize", lambda _: self.show_all())
