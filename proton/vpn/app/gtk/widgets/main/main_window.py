"""
This module defines the main application window.
"""

from gi.repository import Gdk, Gtk, GdkPixbuf

from proton.vpn.app.gtk.assets.icons import ICONS_PATH
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.main_widget import MainWidget
from proton.vpn.app.gtk.widgets.headerbar.headerbar import HeaderBar
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.main.notifications import Notifications


class MainWindow(Gtk.ApplicationWindow):
    """Main window."""

    WIDTH = 400
    HEIGTH = 600

    def __init__(
            self, application: Gtk.Application,
            controller: Controller,
    ):
        super().__init__(application=application)
        self._controller = controller

        self.configure_window()

        notifications = Notifications(main_window=self, notification_bar=NotificationBar())

        self.header_bar = HeaderBar(
            controller=controller,
            main_window=self,
            notifications=notifications
        )
        self.set_titlebar(self.header_bar)

        self.main_widget = MainWidget(
            controller=controller,
            main_window=self,
            notifications=notifications
        )
        self.add(self.main_widget)

    def add_keyboard_shortcut(self, target_widget: Gtk.Widget, target_signal: str, shortcut: str):
        """
        Adds a keyboard shortcut so that when pressed it causes the target signal
        to be triggered on the target widget.

        :param target_widget: The widget the keyboard shortcut will trigger the signal on.
        :param target_signal: The signal the keyboard shortcut will trigger on the target widget.
        :param shortcut: The keyboard shortcut should be a string parseable with
        Gtk.parse_accelerator:
        https://lazka.github.io/pgi-docs/#Gtk-3.0/functions.html#Gtk.accelerator_parse
        """
        key, modifier = Gtk.accelerator_parse(shortcut)
        target_widget.add_accelerator(
            target_signal, self._accelerators_group,
            key, modifier, Gtk.AccelFlags.VISIBLE
        )

    def configure_window(self):
        """
        Handle delete-event, set window resize restrictions...
        """
        # Handle event emitted when the button to close the window is clicked.
        self.connect("delete-event", self._on_close_window_button_clicked)

        # The accelerator group is used to then add keyboard shortcuts.
        self._accelerators_group = Gtk.AccelGroup()
        self.add_accel_group(self._accelerators_group)

        self.set_border_width(10)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon(GdkPixbuf.Pixbuf.new_from_file_at_size(
            filename=str(ICONS_PATH / "proton-vpn-sign.svg"),
            width=128, height=128
        ))

        # The window should be able to be resized on the vertical axis but not
        # on the horizontal axis.
        self.set_size_request(MainWindow.WIDTH, MainWindow.HEIGTH)
        geometry = Gdk.Geometry()
        geometry.min_width = 0
        geometry.max_width = MainWindow.WIDTH
        geometry.min_height = 0
        geometry.max_height = 99999
        self.set_geometry_hints(
            self,
            geometry,
            (Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE)
        )

    def _on_close_window_button_clicked(self, *_) -> bool:
        """
        Handles the delete-event event emitted when the user tries to close
        the window by clicking the x button.

        Instead of letting the window x button close the app, therefore
        quitting the app, the action is delegated to the Exit entry in
        the menu bar widget.
        """
        self.header_bar.menu.quit_button_click()

        # Returning True when handling the delete-event stops other handlers
        # from being invoked for this event:
        # https://docs.gtk.org/gtk3/signal.Widget.delete-event.html
        # This means that the delete-event is not going to cause the window
        # to be closed by itself. Instead, the action of quitting the
        # app is delegated to the Exit entry on the header bar menu.
        return True
