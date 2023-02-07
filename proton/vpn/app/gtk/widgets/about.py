"""
Module for the about dialog.
"""
from gi.repository import GdkPixbuf
from proton.vpn.app.gtk import Gtk

from proton.vpn.app.gtk.assets.icons import ICONS_PATH
from proton.vpn.app.gtk import __version__


class AboutWidget(Gtk.AboutDialog):
    """This widget will display general information about this application"""
    TITLE = "About"
    PROGRAM_NAME = "Proton VPN Linux Client"
    VERSION = __version__
    COPYRIGHT = "Proton AG 2023"
    LICENSE = Gtk.License.GPL_3_0
    WEBSITE = "https://protonvpn.com"
    WEBSITE_LABEL = "Proton VPN"
    AUTHORS = ["Proton AG"]

    def __init__(self):
        super().__init__()
        self.set_title(self.TITLE)
        self.set_program_name(self.PROGRAM_NAME)
        self.set_version(self.VERSION)
        self.set_copyright(self.COPYRIGHT)
        self.set_license_type(self.LICENSE)
        self.set_website(self.WEBSITE)
        self.set_website_label(self.WEBSITE_LABEL)
        self.set_authors(self.AUTHORS)
        self._set_icon()

    def _set_icon(self):
        self.set_logo(GdkPixbuf.Pixbuf.new_from_file_at_size(
            filename=str(ICONS_PATH / "proton-vpn-sign.svg"),
            width=80, height=80
        ))
