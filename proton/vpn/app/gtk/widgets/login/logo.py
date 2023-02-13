# pylint: disable=missing-module-docstring
from gi.repository import GdkPixbuf, Gtk

from proton.vpn.app.gtk.assets import ASSETS_PATH


class ProtonVPNLogo(Gtk.Image):
    """Proton VPN logo shown in the login widget."""
    def __init__(self):
        super().__init__()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=str(ASSETS_PATH / "proton-vpn-logo.svg"),
            width=300,
            height=300,
            preserve_aspect_ratio=True
        )
        self.set_from_pixbuf(pixbuf)
