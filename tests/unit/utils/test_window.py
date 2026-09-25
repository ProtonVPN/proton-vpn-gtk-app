"""
Copyright (c) 2026 Proton AG

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


Tests that every top-level window the app shows is a .proton-app CSS root.
"""
from unittest.mock import Mock

import pytest

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.utils.window import PROTON_APP_CSS_CLASS, register_proton_window
from proton.vpn.app.gtk.widgets.headerbar.menu.about_dialog import AboutDialog
from proton.vpn.app.gtk.widgets.headerbar.menu.bug_report_dialog import BugReportDialog
from proton.vpn.app.gtk.widgets.headerbar.menu.release_notes_dialog import ReleaseNotesDialog
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access import EarlyAccessDialog
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window import SettingsWindow
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.app_select_window \
    import AppSelectionWindow
from proton.vpn.app.gtk.widgets.main.confirmation_dialog import ConfirmationDialog
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.app.gtk.widgets.main.pull_notifications.nps_survey_modal import NPSSurveyModal
from tests.unit.testing_utils import process_gtk_events


def test_register_proton_window_adds_the_root_class():
    window = Gtk.Window()

    register_proton_window(window)

    assert window.has_css_class(PROTON_APP_CSS_CLASS)
    window.destroy()


def _main_window():
    controller = Mock()
    controller.notifications.get_nps_survey_notifications.return_value = []
    return MainWindow(
        application=None, controller=controller, notifications=Mock(),
        header_bar=Gtk.HeaderBar(), main_widget=Gtk.Label(),
    )


WINDOW_FACTORIES = {
    "MainWindow": _main_window,
    "SettingsWindow": lambda: SettingsWindow(controller=Mock()),
    "AppSelectionWindow": lambda: AppSelectionWindow(
        title="Apps", controller=Mock(), stored_apps=[], installed_apps=[]
    ),
    "NPSSurveyModal": lambda: NPSSurveyModal(
        controller=Mock(), submit_handler=Mock(), dismiss_handler=Mock()
    ),
    "BugReportDialog": lambda: BugReportDialog(
        controller=Mock(), main_window=Mock(), log_collector=Mock()
    ),
    "EarlyAccessDialog": EarlyAccessDialog,
    "ConfirmationDialog": lambda: ConfirmationDialog(message="Sure?", title="Confirm"),
    "AboutDialog": AboutDialog,
}


@pytest.mark.parametrize("factory", WINDOW_FACTORIES.values(), ids=WINDOW_FACTORIES.keys())
def test_top_level_window_is_a_proton_app_root(factory):
    window = factory()

    assert window.has_css_class(PROTON_APP_CSS_CLASS)
    window.destroy()
    process_gtk_events()


def test_release_notes_dialog_is_a_proton_app_root(monkeypatch, tmp_path):
    # Use a temporary notes file, so the test doesn't depend on the contents of
    # the shipped release_notes.md.
    notes = tmp_path / "release_notes.md"
    notes.write_text("## 1.0.0\n- First release.\n", encoding="utf-8")
    monkeypatch.setattr(ReleaseNotesDialog, "RELEASE_NOTES", str(notes))

    window = ReleaseNotesDialog()

    assert window.has_css_class(PROTON_APP_CSS_CLASS)
    window.destroy()
    process_gtk_events()


def test_error_dialog_is_a_proton_app_root():
    parent = Gtk.Window()
    notifications = Notifications(main_window=parent, notification_bar=Mock())

    notifications.show_error_dialog("Something failed.", "Error")
    process_gtk_events()

    assert notifications.error_dialog.has_css_class(PROTON_APP_CSS_CLASS)
    notifications.error_dialog.destroy()
    parent.destroy()
    process_gtk_events()
