from __future__ import annotations

import logging

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main import MainWidget

logger = logging.getLogger(__name__)


class MainWindow(Gtk.ApplicationWindow):
    """Main window."""
    def __init__(self, controller: Controller):
        super().__init__(title="Proton VPN")

        self._controller = controller

        self.set_size_request(400, 150)
        self.set_border_width(10)
        self.set_resizable(False)

        self.main_widget = MainWidget(controller=controller)
        self.add(self.main_widget)
