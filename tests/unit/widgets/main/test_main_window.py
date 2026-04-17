"""
Copyright (c) 2023 Proton AG

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
from concurrent.futures import Future
import pytest
from gi.repository import GLib

from unittest.mock import Mock

from proton.session.exceptions import ProtonAPINotReachable, ProtonAPIError
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.exceptions import NPSError
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow
from tests.unit.testing_utils import process_gtk_events


class HeaderBarMock(Gtk.HeaderBar):
    def __init__(self):
        super().__init__()
        self.menu = Mock()


@pytest.fixture
def controller():
    mock = Mock()
    mock.notifications.get_nps_survey_notifications.return_value = []
    return mock


@pytest.fixture
def main_window(controller):
    return MainWindow(
        application=None,
        controller=controller,
        notifications=Mock(),
        header_bar=HeaderBarMock(),
        main_widget=Gtk.Label(label="Main widget")
    )


@pytest.fixture
def dummy_app(main_window):
    def show_window(app):
        app.add_window(main_window)
        main_window.set_visible(True)
        process_gtk_events()

    app = Gtk.Application()
    app.connect("activate", show_window)
    return app


def test_close_button_triggers_quit_menu_entry_when_tray_indicator_is_not_used(dummy_app, main_window):
    main_window.configure_close_button_behaviour(tray_indicator_enabled=False)

    main_window.connect("show", lambda _: main_window.close())

    GLib.timeout_add(interval=50, function=dummy_app.quit)
    process_gtk_events()

    dummy_app.run()
    process_gtk_events()

    main_window.header_bar.menu.quit_button_click.assert_called_once()


def test_close_button_hides_window_when_tray_indicator_is_used(dummy_app, main_window):
    main_window.configure_close_button_behaviour(tray_indicator_enabled=True)

    main_window.connect("show", lambda _: main_window.close())
    GLib.timeout_add(interval=50, function=dummy_app.quit)
    process_gtk_events()

    dummy_app.run()
    process_gtk_events()

    assert main_window.is_visible() is False


def _stub_submission_with_exception(controller, exc: Exception):
    """Configures the controller so that submitting any NPS response returns
    a future that has already failed with the given exception."""
    future = Future()
    future.set_exception(exc)
    controller.submit_nps_survey_response.return_value = future


@pytest.fixture
def nps_modal(main_window):
    """Opens the NPS survey modal and yields it for interaction."""
    modal = main_window.create_nps_survey_modal()
    modal.set_transient_for(main_window)
    modal.show()
    yield modal
    modal.destroy()
    process_gtk_events()


def test_nps_submission_api_not_reachable_is_logged_and_not_reraised(
    controller, nps_modal
):
    _stub_submission_with_exception(controller, ProtonAPINotReachable("offline"))

    nps_modal.emit("close-request")

    process_gtk_events()  # would raise if anything was scheduled


def test_nps_submission_proton_api_error_is_logged_and_not_reraised(
    controller, nps_modal
):
    _stub_submission_with_exception(
        controller,
        ProtonAPIError(400, {}, {"Code": 2000, "Error": "bad request"})
    )

    nps_modal.emit("close-request")

    process_gtk_events()  # would raise if anything was scheduled


def test_nps_submission_unexpected_exception_is_reraised_on_main_thread_as_nps_error(
    controller, nps_modal
):
    cause = RuntimeError("something broke")
    _stub_submission_with_exception(controller, cause)

    nps_modal.emit("close-request")

    with pytest.raises(NPSError) as exc_info:
        process_gtk_events()

    assert exc_info.value.__cause__ is cause
