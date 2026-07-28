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
import functools
import gettext
import os
from pathlib import Path
from typing import Optional


DOMAIN = "proton-vpn-gtk-app"
LOCALE_DIR = os.path.join(os.path.dirname(__file__), "locale", "binaries")
ENV_VAR = "PROTON_VPN_LOCALIZATION_ENABLED"


def _resolve_language(languages, domain, localedir) -> Optional[str]:
    """Locale code of the compiled `domain` catalog gettext resolves for
    `languages`, e.g. "fr_FR".
    """
    mo_path = gettext.find(domain, localedir, languages=languages)
    if mo_path is None:
        return None
    return Path(mo_path).parent.parent.name


@functools.cache
def active_language() -> Optional[str]:
    """The language we localize into for the active locale (e.g. "fr_FR"), or
    None when catalog doesn't exist."""
    return _resolve_language(None, DOMAIN, LOCALE_DIR)


def localization_enabled(environ=None) -> bool:
    """Whether localization is enabled: requires both the env flag set to '1'
    and a compiled catalog (.mo) for the active language. Returns False if
    either is missing."""
    environ = os.environ if environ is None else environ
    if environ.get(ENV_VAR) != "1":
        return False
    return active_language() is not None


def _load(enabled: bool, locale_dir: str = LOCALE_DIR) -> gettext.NullTranslations:
    """Real catalog when enabled, otherwise a pass-through (returns source text)."""
    if not enabled:
        return gettext.NullTranslations()
    return gettext.translation(DOMAIN, locale_dir, fallback=True)


_translation = _load(localization_enabled())


# pgettext's conventional name is `C_`
# pylint: disable=invalid-name
def C_(
    context: str,
    message: str,
    translation: gettext.NullTranslations = _translation,
) -> str:
    """
    Translate message within context via the active catalog.
    :param context: the msgctxt describing the string's role (e.g. "button").
    :param message: the source text to translate.
    :return: The translated message, or message if language-file not found.
    """
    return translation.pgettext(context, message)


def npgettext(
    context: str,
    singular: str,
    plural: str,
    n: int,
    translation: gettext.NullTranslations = _translation,
) -> str:
    """
    Translate a count-dependent message within context.
    :param context: the msgctxt describing the string's role.
    :param singular: the singular form.
    :param plural: the (English) plural form.
    :param n: the count. Languages may define more than two forms
    (e.g. one/few/many) and gettext picks the right one.

    Returns:
        The plural form of the message.
    """
    return translation.npgettext(context, singular, plural, n)
