"""
Module for the disconnect dialog that prompts the user for confirmation
upon logout or exit.
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

    def __init__(
        self,
        title: str,
        message: str,
        buttons: List[Tuple[str, Gtk.ResponseType]] = None,
    ):
        super().__init__()
        self.set_title(title)
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
