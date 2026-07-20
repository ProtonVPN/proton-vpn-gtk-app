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
"""
from proton.vpn.app.gtk.utils import country


def test_returns_english_name_when_untranslated():
    # No catalog for the language in the test env -> C_ returns the source text.
    assert country.get_localized_country_name("CH") == "Switzerland"


def test_country_code_is_case_insensitive():
    assert country.get_localized_country_name("ch") == "Switzerland"


def test_maps_uk_to_united_kingdom():
    # The API uses "UK"; api-core maps it to "United Kingdom".
    assert country.get_localized_country_name("UK") == "United Kingdom"


def test_unknown_code_falls_back_to_api_core_name():
    # get_country_name_by_code returns the code itself when unknown.
    assert country.get_localized_country_name("ZZ") == "ZZ"
