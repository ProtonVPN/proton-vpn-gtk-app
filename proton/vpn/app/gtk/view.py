from __future__ import annotations

import logging

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.login import LoginWidget
from proton.vpn.app.gtk.widgets.vpn import VPNWidget

logger = logging.getLogger(__name__)


class MainWindow(Gtk.ApplicationWindow):
    """Main window."""
    def __init__(self, controller: Controller):
        super().__init__(title="Proton VPN")

        self._controller = controller

        self.set_size_request(400, 150)
        self.set_border_width(10)
        self.set_resizable(False)

        self._stack = Gtk.Stack()
        self.add(self._stack)

        self.login_widget = LoginWidget(controller)
        self._stack.add_named(self.login_widget, "login_widget")
        self.login_widget.connect("user-logged-in", self.on_user_logged_in)

        self.vpn_widget = VPNWidget(controller)
        self._stack.add_named(self.vpn_widget, "vpn_widget")
        self.vpn_widget.connect("user-logged-out", self.on_user_logged_out)

    def on_user_logged_in(self, _):
        self._stack.set_visible_child(self.vpn_widget)

    def on_user_logged_out(self, _):
        self._stack.set_visible_child(self.login_widget)
