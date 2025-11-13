from unittest.mock import Mock

from gi.repository import Gio

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.installed_apps import get_app_executable



def test_get_app_executable_gets_executable_path_without_args_for_native_apps():
    app = Mock(spec=Gio.AppInfo)
    executable = "/usr/bin/google-chrome-stable"
    app.get_commandline.return_value = "/usr/bin/google-chrome-stable %U"
    app.get_executable.return_value = "/usr/bin/google-chrome-stable"
    assert get_app_executable(app) == "/usr/bin/google-chrome-stable"


def test_get_app_executable_gets_snap_app_path_from_snap_desktop_files():
    app = Mock(spec=Gio.AppInfo)
    app.get_commandline.return_value = "/snap/bin/firefox %u"
    app.get_executable.return_value = "/snap/bin/firefox"
    assert get_app_executable(app) == "/snap/firefox/"


def test_get_app_executable_trims_double_at_symbol_from_flatpak_desktop_files():
    # It's not possible to instantiate a flatpak desktop file with Gio.DesktopAppInfo.new_from_filename(flatpak_desktop_file_path)
    # on Ubuntu (TypeError) but it's possible on Fedora. Flatpak desktop files are also returned with Gio.AppInfo.get_all().
    # That's why a Mock is used instead of the loading it as in other tests.
    app = Mock(spec=Gio.AppInfo)
    app.get_commandline.return_value = "/usr/bin/flatpak run --branch=stable --arch=x86_64 --command=brave --file-forwarding com.brave.Browser @@u %U @@"
    app.get_executable.return_value = "/usr/bin/flatpak"

    assert get_app_executable(app) == "/usr/bin/flatpak run --branch=stable --arch=x86_64 --command=brave --file-forwarding com.brave.Browser"  # @@ argument trimmed off
