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

from proton.vpn import logging

from proton.vpn.session.feature_flags_fetcher import FeatureFlags, FeatureFlagsFetcher

logger = logging.getLogger(__name__)

DOMAIN = "proton-vpn-gtk-app"
LOCALE_DIR = os.path.join(os.path.dirname(__file__), "locale", "binaries")
LOCALIZATION_KILL_SWITCH = "LocalizationKillSwitch"


def _resolve_language(languages, domain, localedir) -> Optional[str]:
    """Locale code of the compiled `domain` catalog gettext resolves for
    `languages`, e.g. "fr_FR".
    """
    mo_path = gettext.find(domain, localedir, languages=languages)
    catalog = Path(mo_path).parent.parent.name if mo_path else None
    # gettext reads the first of these that is set and non-empty, in this order.
    env = {var: os.environ[var] for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")
           if os.environ.get(var)}
    logger.info("Using catalog %s for %s.", catalog, languages if languages is not None else env)
    return catalog


@functools.cache
def active_language() -> Optional[str]:
    """The language we localize into for the active locale (e.g. "fr_FR"), or
    None when catalog doesn't exist."""
    return _resolve_language(None, DOMAIN, LOCALE_DIR)


def _localization_enabled(feature_flags: FeatureFlags, language: Optional[str]) -> bool:
    """Whether localization is on or not. On by default, gated on compiled
    catalog (.mo), and turned off by the remote `LocalizationKillSwitch`.

    :param feature_flags: the resolved feature flags.
    :param language: the active language (e.g. "fr_FR"), or None when no catalog exists.
    """
    enabled = not feature_flags.get(LOCALIZATION_KILL_SWITCH) and language is not None
    logger.info("Localization enabled: %s.", enabled)
    return enabled


def _load(enabled: bool, locale_dir: str = LOCALE_DIR) -> gettext.NullTranslations:
    """Real catalog when enabled, otherwise a pass-through (returns source text)."""
    if not enabled:
        return gettext.NullTranslations()
    return gettext.translation(DOMAIN, locale_dir, fallback=True)


LOCALIZATION_ENABLED = _localization_enabled(
    FeatureFlagsFetcher(session=None).load_from_cache(),
    active_language()
)
_translation = _load(LOCALIZATION_ENABLED)


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
