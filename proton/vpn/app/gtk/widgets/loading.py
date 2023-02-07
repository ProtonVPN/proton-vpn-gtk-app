"""
This module defines the Loading widget. This widget is responsible for displaying
the loading screen.
"""

from proton.vpn.app.gtk import Gtk


class LoadingWidget(Gtk.Box):
    """Loading widget responsible for displaying loading status
    to the user."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._label = Gtk.Label(label="Loading app...")
        self.pack_start(self._label, expand=True, fill=True, padding=0)
        # Adding the background class (which is a GTK class) gives the default
        # background color to this widget. This is needed as otherwise the widget
        #  background is transparent, but the intended use of this widget is to
        #  hide other widgets while an action is ongoing.
        self.get_style_context().add_class("background")
        self.set_no_show_all(True)

    def show(self):  # pylint: disable=W0221
        """Shows the loading screen to the user."""
        self._label.show()
        Gtk.Box.show(self)
