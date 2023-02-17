import pytest
from gi.repository import GLib

from unittest.mock import Mock, patch

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow


class HeaderBarMock(Gtk.HeaderBar):
    def __init__(self):
        super().__init__()
        self.menu = Mock()


@pytest.fixture
def main_window():
    return MainWindow(
        application=None,
        controller=Mock(),
        notifications=Mock(),
        header_bar=HeaderBarMock(),
        main_widget=Gtk.Label(label="Main widget")
    )


@pytest.fixture
def dummy_app(main_window):
    def show_window(app):
        app.add_window(main_window)
        main_window.show()

    app = Gtk.Application()
    app.connect("activate", show_window)
    return app


def test_close_button_triggers_quit_menu_entry_when_tray_indicator_is_not_used(dummy_app, main_window):
    main_window.configure_close_button_behaviour(tray_indicator_enabled=False)

    main_window.connect("show", lambda _: main_window.close())
    GLib.idle_add(dummy_app.quit)

    dummy_app.run()

    main_window.header_bar.menu.quit_button_click.assert_called_once()


def test_close_button_hides_window_when_tray_indicator_is_used(dummy_app, main_window):
    main_window.configure_close_button_behaviour(tray_indicator_enabled=True)

    main_window.connect("show", lambda _: main_window.close())
    GLib.idle_add(dummy_app.quit)

    with patch.object(main_window, "hide"):
        dummy_app.run()

        main_window.hide.assert_called_once()
