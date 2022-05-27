from gi.repository import Gtk


class LoginWindow(Gtk.ApplicationWindow):
    def __init__(self):
        super().__init__(title="Proton VPN - Login")

        # widgets
        self._grid = None
        self._login_button = None

        self._init_ui()

    def _init_ui(self):
        self.connect("destroy", self.on_exit)

        self.set_size_request(400, 150)

        self.set_border_width(10)

        # Setting up the grid in which the elements are to be positioned
        self._grid = Gtk.Grid()
        self._grid.set_column_homogeneous(True)
        self._grid.set_row_homogeneous(True)
        self._grid.set_row_spacing(10)
        self.add(self._grid)

        self._username_entry = Gtk.Entry()
        self._grid.attach(self._username_entry, 0, 0, 1, 1)

        self._password_entry = Gtk.Entry()
        self._grid.attach_next_to(self._password_entry, self._username_entry, Gtk.PositionType.BOTTOM, 1, 1)

        # Add login button
        self._login_button = Gtk.Button(label="Login")
        self._login_button.connect("clicked", self._on_login_button_clicked)
        self._grid.attach_next_to(self._login_button, self._password_entry, Gtk.PositionType.BOTTOM, 1, 1)

    def _on_login_button_clicked(self, _):
        pass

    def _on_exit(self, *_):
        Gtk.main_quit()
