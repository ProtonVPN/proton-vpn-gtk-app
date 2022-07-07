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
        self.active_widget = None

        self._stack = Gtk.Stack()
        self.add(self._stack)

        self.login_widget = LoginWidget(controller)
        self._stack.add_named(self.login_widget, "login_widget")
        self.login_widget.connect("user-logged-in", self._on_user_logged_in)

        self.vpn_widget = VPNWidget(controller)
        self._stack.add_named(self.vpn_widget, "vpn_widget")
        self.vpn_widget.connect("user-logged-out", self._on_user_logged_out)

        self.connect("show", self._on_show)

    def initialize_visible_widget(self):
        # The widget should already be flagged to be shown
        # when this method is called.
        if self._controller.user_logged_in:
            self._display_vpn_widget()
        else:
            self._display_login_widget()

    def _display_vpn_widget(self):
        self.active_widget = self.vpn_widget
        self._stack.set_visible_child(self.vpn_widget)

    def _display_login_widget(self):
        self.active_widget = self.login_widget
        self._stack.set_visible_child(self.login_widget)

    def _on_user_logged_in(self, _):
        self._display_vpn_widget()

    def _on_user_logged_out(self, _):
        self._display_login_widget()
        self.login_widget.reset()

    def _on_show(self, _widget):
        self.initialize_visible_widget()
