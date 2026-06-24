"""
Localization helpers (gettext markers) for the Proton VPN GTK app.

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
import gettext
import os

DOMAIN = "proton-vpn-gtk-app"
LOCALE_DIR = os.path.join(os.path.dirname(__file__), "locale")
ENV_VAR = "PROTON_VPN_LOCALIZATION_ENABLED"


def _load(enabled: bool, locale_dir: str = LOCALE_DIR) -> gettext.NullTranslations:
    """Real catalog when enabled, otherwise a pass-through (returns source text)."""
    if not enabled:
        return gettext.NullTranslations()
    return gettext.translation(DOMAIN, locale_dir, fallback=True)


def localization_enabled(environ=None) -> bool:
    """Whether localization is on. Off unless the flag is explicitly set to '1'."""
    environ = os.environ if environ is None else environ
    return environ.get(ENV_VAR) == "1"


_translation = _load(localization_enabled())


# gettext's conventional name for the translation function is `_`
# pylint: disable=invalid-name
def _(message: str, translation: gettext.NullTranslations = _translation) -> str:
    """
    Translate message via the active catalog.
    :param message: the source text to translate.
    :return: The translated message, or message if langauge-file not found.
    """
    return translation.gettext(message)


def ngettext(
    singular: str,
    plural: str,
    n: int,
    translation: gettext.NullTranslations = _translation,
) -> str:
    """
    Translate a count-dependent message.
    :param singular: the singular form.
    :param plural: the (English) plural form.
    :param n: the count. Languages may define more than two forms
    (e.g. one/few/many) and gettext picks the right one, example:

    ```
    button = Gtk.Button(label=ngettext(
        "{server_count} server available.",
        "{server_count} servers available"),
        server_count
    )
    ```

    Returns:
        The plural form of the message.
    """
    return translation.ngettext(singular, plural, n)


# pylint: disable=invalid-name
def N_(message: str) -> str:
    """
    Mark the message for extraction without translating, no-op marker.
    This should be used for URIs, email adresses, etc. Example:

    ```
    help_link = Gtk.LinkButton(
        label=_("Need Help?"),
        uri=N_("https://protonvpn.com/support")
    )
    ```

    :param message: the source text to mark for translation.
    :return: The message unchanged.
    """
    return message
