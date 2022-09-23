"""
This module defines utilities that are used by different modules.
"""
from iso3166 import countries


def get_country_name_by_code(country_code: str):
    """Returns country name based on provided country code, in ISO 3166 format."""
    if country_code.lower() == "uk":
        # Even though we use UK, the correct ISO 3166 code is GB.
        country_code = "gb"

    country = countries.get(country_code.lower(), default=None)

    # If the country name was not found then default to the country code.
    return country.name if country else country_code
