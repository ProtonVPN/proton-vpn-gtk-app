"""Utilities used on the search features of the app."""


def normalize(search_string: str):
    """Returns the normalized version of the input search string."""
    return search_string.lower().replace(" ", "")
