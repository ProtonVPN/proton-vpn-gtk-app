import gettext

from proton.vpn.app.gtk.translator import C_, npgettext, localization_enabled


class FrenchCatalog(gettext.NullTranslations):
    """Fake catalog: French for known (context, string) pairs, source text otherwise."""

    def pgettext(self, context, message):
        return {("button", "Sign in"): "Se connecter"}.get((context, message), message)

    def npgettext(self, context, singular, plural, n):
        return "serveur" if n == 1 else "serveurs"


def test_localization_off_by_default():
    assert localization_enabled({}) is False


def test_pgettext_returns_translation_when_enabled():
    assert C_("button", "Sign in", FrenchCatalog()) == "Se connecter"


def test_pgettext_returns_source_when_disabled():
    assert C_("button", "Sign in", gettext.NullTranslations()) == "Sign in"


def test_npgettext_returns_singular_translation_when_count_is_one():
    assert npgettext("info", "server", "servers", 1, FrenchCatalog()) == "serveur"


def test_npgettext_returns_singular_source_when_disabled_and_count_is_one():
    assert npgettext("info", "server", "servers", 1, gettext.NullTranslations()) == "server"


def test_npgettext_returns_plural_translation_when_count_is_more_than_one():
    assert npgettext("info", "server", "servers", 2, FrenchCatalog()) == "serveurs"


def test_npgettext_returns_plural_source_when_disabled_and_count_is_more_than_one():
    assert npgettext("info", "server", "servers", 2, gettext.NullTranslations()) == "servers"
