from __future__ import annotations

from typing import Union

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.login import LoginWidget
from proton.vpn.app.gtk.widgets.vpn import VPNWidget


class MainWidget(Gtk.Bin):
    """
    Main Proton VPN widget. It switches between the LoginWidget and the
    VPNWidget, depending on whether the user is logged in or not.
    """

    def __init__(self, controller: Controller):
        super().__init__()
        self._controller = controller

        self.login_widget = LoginWidget(controller)
        self.login_widget.connect("user-logged-in", self._on_user_logged_in)

        self.vpn_widget = VPNWidget(controller)
        self.vpn_widget.connect("user-logged-out", self._on_user_logged_out)

        self.connect("show", self._on_show)

    @property
    def active_widget(self):
        return self.get_child()

    @active_widget.setter
    def active_widget(self, widget: Union[LoginWidget, VPNWidget]):
        if self.get_child():
            self.remove(self.get_child())
        self.add(widget)

    def initialize_visible_widget(self):
        # The widget should already be flagged to be shown
        # when this method is called.
        self._display_widget(
            self.vpn_widget
            if self._controller.user_logged_in else
            self.login_widget
        )

    def _on_user_logged_in(self, _login_widget: LoginWidget):
        self._display_widget(self.vpn_widget)

    def _on_user_logged_out(self, _login_widget: LoginWidget):
        self._display_widget(self.login_widget)
        self.login_widget.reset()

    def _display_widget(self, widget: Union[LoginWidget, VPNWidget]):
        self.active_widget = widget
        self.active_widget.show_all()

    def _on_show(self, _main_widget: MainWidget):
        self.initialize_visible_widget()
