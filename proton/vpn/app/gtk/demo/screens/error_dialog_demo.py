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


Demo factories for the error dialog, e.g. shown when the VPN is connected but
traffic stays blocked until the user authenticates with a hardware key.
"""
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo.registry import register_demo
from proton.vpn.app.gtk.demo.sizing import NATURAL, UNCONSTRAINED
from proton.vpn.app.gtk.utils.exception_handler import ExceptionHandler
from proton.vpn.app.gtk.widgets.main.notifications import build_error_dialog


def _at_natural_width(dialog: Gtk.MessageDialog) -> Gtk.MessageDialog:
    """The app opens the dialog as wide as its text wants; the demo would
    otherwise show it at its narrowest."""
    natural_width = dialog.get_child().measure(Gtk.Orientation.HORIZONTAL, UNCONSTRAINED)[1]
    dialog.set_default_size(natural_width, NATURAL)
    return dialog


@register_demo("error-dialog", label="2fa-required")
def error_dialog_2fa_required() -> Gtk.MessageDialog:
    """The dialog shown while traffic is blocked until hardware-key authentication."""
    return _at_natural_width(build_error_dialog(
        None,
        ExceptionHandler.VPN_HARD_JAILED_2FA_ERROR_TITLE,
        ExceptionHandler.VPN_HARD_JAILED_2FA_ERROR_MESSAGE,
    ))


@register_demo("error-dialog", label="with-hint")
def error_dialog_with_hint() -> Gtk.MessageDialog:
    """A dialog with a hint below the message, as API errors can have."""
    return _at_natural_width(build_error_dialog(
        None,
        ExceptionHandler.TIME_OUT_OF_SYNC_ERROR_TITLE,
        ExceptionHandler.TIME_OUT_OF_SYNC_ERROR_MESSAGE,
        hint="A hint from the server, shown in smaller text.",
    ))
