import gettext

from proton.vpn.app.gtk import translator
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


def test_resolve_language_returns_locale_when_catalog_present(tmp_path):
    domain = "proton-vpn-gtk-app"
    mo = tmp_path / "fr_FR" / "LC_MESSAGES" / f"{domain}.mo"
    mo.parent.mkdir(parents=True)
    mo.write_bytes(b"")
    assert translator._resolve_language(["fr_FR"], domain, str(tmp_path)) == "fr_FR"


def test_resolve_language_is_none_when_catalog_absent(tmp_path):
    assert translator._resolve_language(
        ["fr_FR"], "proton-vpn-gtk-app", str(tmp_path)) is None
