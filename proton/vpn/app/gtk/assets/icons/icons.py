"""
Utility module to load and cache icons.

We should consider to switch to Gtk.IconTheme:
https://docs.gtk.org/gtk3/class.IconTheme.html
"""
from pathlib import Path
from typing import Optional

from gi.repository import GdkPixbuf

ICONS_PATH = Path(__file__).parent

_cache = {}


def get(
        relative_path: Path,
        width: Optional[int] = None,
        height: Optional[int] = None,
        preserve_aspect_ratio: bool = True
) -> GdkPixbuf.Pixbuf:
    """
    Loads the image (if it wasn't cached), caches it and returns it.
    :param relative_path: Path relative to the icons directory root.
    :param width: Optional width of the image to be loaded.
    :param height: Optional height of the image to be loaded.
    :param preserve_aspect_ratio: Whether the aspect ratio should be preserved
    or not. The default is True.
    """
    # Pixbuf API quirks.
    width = width if width is not None else -1
    height = height if height is not None else -1

    cache_key = (relative_path, width, height, preserve_aspect_ratio)
    cached_icon = _cache.get(cache_key)
    if cached_icon:
        return cached_icon

    full_path = ICONS_PATH / relative_path
    if not full_path.is_file():
        raise ValueError(f"File not found: {full_path}")

    filename = str(ICONS_PATH / relative_path)
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
        filename=filename, width=width, height=height,
        preserve_aspect_ratio=preserve_aspect_ratio
    )
    _cache[cache_key] = pixbuf

    return pixbuf
