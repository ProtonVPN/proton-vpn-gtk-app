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


Demo factories for the bug report dialog.
"""
from proton.vpn.app.gtk.demo.registry import register_demo
from proton.vpn.app.gtk.demo.mocks import mock_controller, mock_main_window
from proton.vpn.app.gtk.widgets.headerbar.menu.bug_report_dialog import BugReportDialog


@register_demo("bug-report", label="empty")
def bug_report_empty() -> BugReportDialog:
    """Bug report dialog with empty fields."""
    return BugReportDialog(mock_controller(), mock_main_window())


@register_demo("bug-report", label="filled")
def bug_report_filled() -> BugReportDialog:
    """Bug report dialog pre-filled with sample input."""
    dialog = BugReportDialog(mock_controller(), mock_main_window())
    dialog.username_entry.set_text("demo_user")
    dialog.email_entry.set_text("demo@example.com")
    dialog.description_buffer.set_text(
        "Pre-filled demo description for screenshot purposes."
    )
    dialog.send_logs_checkbox.set_active(True)
    return dialog


@register_demo("bug-report", label="disabled")
def bug_report_disabled() -> BugReportDialog:
    """Bug report dialog with its form disabled (as during submission)."""
    dialog = BugReportDialog(mock_controller(), mock_main_window())
    # No public API toggles this; reach into the private method rather than grow
    # the dialog's API for a demo-only need.
    dialog._disable_form()  # pylint: disable=protected-access
    return dialog
