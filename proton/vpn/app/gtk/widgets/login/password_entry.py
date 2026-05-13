"""
Copyright (c) 2025 Proton AG

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
from pathlib import Path

from gi.repository import Gdk, Gtk
from proton.vpn.app.gtk.assets import icons
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect


class PasswordEntry(Gtk.Entry):
    """
    Entry used to introduce the password in the login form.

    On top of the inherited functionality from Gtk.Entry, an icon is shown
    inside the text entry to show or hide the password.

    By default, the text (password) introduced in the entry is not show.
    Therefore, the icon to be able to show the text is displayed. Once this
    icon is pressed, the text is revealed and the icon to hide the password
    is shown instead.
    """
    def __init__(self):
        super().__init__()
        self.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.set_visibility(False)
        # Load icon to hide the password.
        eye_dirpath = Path("eye")
        hide_fp = eye_dirpath / "hide.svg"
        self._hide_pixbuff = icons.get(
            hide_fp,
            width=17,
            height=17,
            preserve_aspect_ratio=True
        )
        # Load icon to show the password.
        show_fp = eye_dirpath / "show.svg"
        self._show_pixbuff = icons.get(
            show_fp,
            width=17,
            height=17,
            preserve_aspect_ratio=True
        )
        # By default, the password is not shown. Therefore, the icon to
        # be able to show the password is shown.
        show_texture = Gdk.Texture.new_for_pixbuf(self._show_pixbuff)
        self.set_icon_from_gicon(
            Gtk.EntryIconPosition.SECONDARY,
            show_texture
        )
        self.set_icon_activatable(
            Gtk.EntryIconPosition.SECONDARY,
            True
        )
        safe_signal_connect(
            self, "icon-press", self._on_change_password_visibility_icon_press
        )

    def _on_change_password_visibility_icon_press(self, gtk_entry_object, _icon_position):
        """Changes password visibility, updating accordingly the icon."""
        is_text_visible = gtk_entry_object.get_visibility()
        gtk_entry_object.set_visibility(not is_text_visible)
        pixbuf = self._show_pixbuff if is_text_visible else self._hide_pixbuff
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_icon_from_gicon(
            Gtk.EntryIconPosition.SECONDARY,
            texture
        )
