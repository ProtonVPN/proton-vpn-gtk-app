"""
Localized country names.

Country names are not translated by the API.


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
from proton.vpn.session.servers.country_codes import get_country_name_by_code

from proton.vpn.app.gtk.translator import C_


def get_localized_country_name(country_code: str) -> str:
    """Returns the country name localized to the active language.

    :param country_code: country code (e.g. "CH"), case-insensitive.
    """
    return C_("country", get_country_name_by_code(country_code))
