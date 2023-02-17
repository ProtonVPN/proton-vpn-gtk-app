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

    # pylint: disable=too-many-arguments
    def __init__(
            self, application: Gtk.Application,
            controller: Controller,
            notifications: Notifications = None,
            header_bar: HeaderBar = None,
            main_widget: MainWidget = None
    ):
        super().__init__(application=application)
        self._controller = controller

        self._configure_window()

        notifications = notifications or Notifications(
            main_window=self, notification_bar=NotificationBar()
        )

        self.header_bar = header_bar or HeaderBar(
            controller=controller,
            main_window=self,
            notifications=notifications
        )
        self.set_titlebar(self.header_bar)

        self.main_widget = main_widget or MainWidget(
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

    def _configure_window(self):
        """
        Handle delete-event, set window resize restrictions...
        """

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

    def configure_close_button_behaviour(self, tray_indicator_enabled: bool):
        """Configures the behaviour of the button to close the window
        (the x button), depending on if the tray indicator is used or not."""
        if tray_indicator_enabled:
            self.configure_close_button_to_hide_window()
        else:
            self.configure_close_button_to_trigger_quit_menu_entry()

    def configure_close_button_to_hide_window(self):
        """Configures the x (close window) button so that when clicked,
        the window is hidden instead closed."""
        def on_close_button_clicked_then_hide_window(*_) -> bool:
            """
            Instead of letting the window x button close the app, therefore
            quitting the app, the action is delegated to the Exit entry in
            the menu bar widget.
            """
            self.hide()

            # Returning True when handling the delete-event stops other handlers
            # from being invoked for this event, therefore preventing the default
            # behaviour:
            # https://docs.gtk.org/gtk3/signal.Widget.delete-event.html
            return True

        # Handle the event emitted when the user tries to close the window.
        self.connect(
            "delete-event",
            on_close_button_clicked_then_hide_window
        )

    def configure_close_button_to_trigger_quit_menu_entry(self):
        """Configures the x (close window) button so that when clicked,
        the Exit menu entry is triggered instead."""
        def on_close_button_clicked_then_click_quit_menu_entry(*_) -> bool:
            """
            Instead of letting the x button close the app, therefore
            quitting the app, the action is delegated to the Exit entry in
            the menu bar widget, which may request confirmation to the user.
            """
            self.header_bar.menu.quit_button_click()

            # Returning True when handling the delete-event stops other handlers
            # from being invoked for this event, therefore preventing the default
            # behaviour:
            # https://docs.gtk.org/gtk3/signal.Widget.delete-event.html
            return True

        # Handle the event emitted when the user tries to close the window.
        self.connect(
            "delete-event",
            on_close_button_clicked_then_click_quit_menu_entry
        )
