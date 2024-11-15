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
from typing import Union
from gi.repository import Pango
from proton.vpn.app.gtk import Gtk
from proton.vpn import logging

logger = logging.getLogger(__name__)


class ConfirmationDialog(Gtk.Dialog):
    """Confirmation dialog widget."""
    WIDTH = 150
    HEIGHT = 200

    def __init__(
        self, message: Union[Gtk.Widget, str],
        title: str,
        yes_text: str = None, no_text: str = None
    ):
        super().__init__()
        self.set_title(title)
        self.set_default_size(self.WIDTH, self.HEIGHT)

        yes_button = self.add_button("_Yes" if not yes_text else yes_text, Gtk.ResponseType.YES)
        no_button = self.add_button("_No" if not no_text else no_text, Gtk.ResponseType.NO)

        no_button.get_style_context().add_class("primary")
        yes_button.get_style_context().add_class("danger")

        if isinstance(message, str):
            widget = Gtk.Label(label=message)
            widget.set_width_chars(50)
            widget.set_max_width_chars(50)
            widget.set_line_wrap(True)
            widget.set_line_wrap_mode(Pango.WrapMode.WORD)
        else:
            widget = message

        # By default Gtk.Dialog has a vertical box child (Gtk.Box) `vbox`
        self.vbox.set_border_width(20)  # pylint: disable=no-member
        self.vbox.set_spacing(20)  # pylint: disable=no-member
        self.vbox.add(widget)  # pylint: disable=no-member
        self.connect("realize", lambda _: self.show_all())  # pylint: disable=no-member, disable=line-too-long # noqa: E501 # nosemgrep: python.lang.correctness.return-in-init.return-in-init
