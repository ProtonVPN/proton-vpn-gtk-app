import gettext

from proton.vpn.app.gtk.translator import _, ngettext, localization_enabled


class FrenchCatalog(gettext.NullTranslations):
    """Fake catalog: French for known strings, source text otherwise."""

    def gettext(self, message):
        return {"Sign in": "Se connecter"}.get(message, message)

    def ngettext(self, singular, plural, n):
        return "serveur" if n == 1 else "serveurs"


def test_localization_off_by_default():
    assert localization_enabled({}) is False


def test_gettext_returns_translation_when_enabled():
    assert _("Sign in", FrenchCatalog()) == "Se connecter"


def test_gettext_returns_source_when_disabled():
    assert _("Sign in", gettext.NullTranslations()) == "Sign in"


def test_ngettext_returns_singular_translation_when_count_is_one():
    assert ngettext("server", "servers", 1, FrenchCatalog()) == "serveur"


def test_ngettext_returns_singular_source_when_disabled_and_count_is_one():
    assert ngettext("server", "servers", 1, gettext.NullTranslations()) == "server"


def test_ngettext_returns_plural_translation_when_count_is_more_than_one():
    assert ngettext("server", "servers", 2, FrenchCatalog()) == "serveurs"


def test_ngettext_returns_plural_source_when_disabled_and_count_is_more_than_one():
    assert ngettext("server", "servers", 2, gettext.NullTranslations()) == "servers"
