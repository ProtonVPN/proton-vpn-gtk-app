"""
Map geometry: outlines, projection, zoom/pan viewport and hit testing.

This module does not depend on Gtk nor on the Proton VPN API so that it can be
tested in isolation.


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
# pylint: disable=invalid-name  # short names are the usual ones in map math
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

Ring = Sequence[Tuple[float, float]]  # (longitude, latitude) pairs

MAP_DATA_PATH = Path(__file__).parents[3] / "assets" / "map" / "world.json"

LAT_MAX, LAT_MIN = 84.0, -57.0  # latitudes shown (hides most of Antarctica)
MIN_ZOOM, MAX_ZOOM = 1.0, 14.0

# Locations too small to have an outline at this map scale: code -> (lon, lat).
# They are drawn as dots.
SMALL_TERRITORIES = {
    "SG": (103.82, 1.35), "HK": (114.17, 22.32), "MT": (14.4, 35.9),
    "LU": (6.1, 49.8), "MC": (7.4, 43.7), "LI": (9.55, 47.16),
    "AD": (1.52, 42.5), "SM": (12.46, 43.94), "BH": (50.55, 26.07),
    "MU": (57.55, -20.3), "MV": (73.2, 3.2), "MO": (113.55, 22.2),
    "GI": (-5.35, 36.14), "IM": (-4.55, 54.2), "JE": (-2.13, 49.2),
    "GG": (-2.58, 49.45), "VA": (12.45, 41.9), "BM": (-64.75, 32.3),
    "CW": (-68.98, 12.17), "PR": (-66.5, 18.2), "SC": (55.49, -4.68),
    "MH": (171.2, 7.1), "FO": (-6.8, 62.0), "KY": (-81.25, 19.3),
    "KM": (43.3, -11.7),
}


def project(lon: float, lat: float) -> Tuple[float, float]:
    """
    Miller projection of a position, in map units: the map is 1 unit wide and
    ``MAP_ASPECT`` units high.
    """
    return (lon + 180.0) / 360.0, (_miller_y(LAT_MAX) - _miller_y(lat)) / (2 * math.pi)


def _miller_y(lat: float) -> float:
    return 1.25 * math.log(math.tan(math.pi / 4 + 0.4 * math.radians(lat)))


def unproject(u: float, v: float) -> Tuple[float, float]:
    """Inverse of :func:`project`."""
    y = _miller_y(LAT_MAX) - v * 2 * math.pi
    lat = math.degrees((math.atan(math.exp(y / 1.25)) - math.pi / 4) / 0.4)
    return u * 360.0 - 180.0, lat


MAP_ASPECT = (_miller_y(LAT_MAX) - _miller_y(LAT_MIN)) / (2 * math.pi)  # height / width


@dataclass(frozen=True)
class Shape:
    """
    Something that can be drawn and clicked on the map: a country, a US state
    or a dot for a very small territory.

    Attributes:
        country_code: Proton country code (e.g. "UK").
        us_state: postal code of the US state, if the shape is one (e.g. "TX").
        name: name of the US state, if the shape is one.
        rings: outer rings of the outline, as (longitude, latitude) pairs.
        point: (longitude, latitude) of the dot, for small territories.
    """
    country_code: str
    us_state: Optional[str] = None
    name: str = ""
    rings: Tuple[Ring, ...] = ()
    point: Optional[Tuple[float, float]] = None
    bounds: Tuple[Tuple[float, float, float, float], ...] = field(init=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "bounds", tuple(
            (min(x for x, _ in ring), min(y for _, y in ring),
             max(x for x, _ in ring), max(y for _, y in ring))
            for ring in self.rings
        ))

    @cached_property
    def map_rings(self) -> Tuple[Tuple[Tuple[float, float], ...], ...]:
        """The outline in map units (see :func:`project`)."""
        return tuple(tuple(project(lon, lat) for lon, lat in ring) for ring in self.rings)

    @cached_property
    def map_point(self) -> Optional[Tuple[float, float]]:
        """The dot position in map units (see :func:`project`), for small territories."""
        return project(*self.point) if self.point else None

    @property
    def key(self) -> str:
        """Unique identifier of the shape."""
        return f"US-{self.us_state}" if self.us_state else self.country_code

    def contains(self, lon: float, lat: float) -> bool:
        """Whether the position is inside the outline."""
        return any(
            x0 <= lon <= x1 and y0 <= lat <= y1 and point_in_ring(lon, lat, ring)
            for ring, (x0, y0, x1, y1) in zip(self.rings, self.bounds)
        )


def point_in_ring(lon: float, lat: float, ring: Ring) -> bool:
    """Ray casting point-in-polygon test."""
    inside = False
    x_prev, y_prev = ring[-1]
    for x_cur, y_cur in ring:
        if (y_cur > lat) != (y_prev > lat) \
                and lon < (x_prev - x_cur) * (lat - y_cur) / (y_prev - y_cur) + x_cur:
            inside = not inside
        x_prev, y_prev = x_cur, y_cur
    return inside


@lru_cache(maxsize=1)
def load_shapes() -> List[Shape]:
    """Loads the outlines of the countries (except the US), the US states and the dots."""
    data = json.loads(MAP_DATA_PATH.read_text(encoding="utf-8"))
    shapes = [
        Shape(country_code=c["code"], rings=tuple(tuple(map(tuple, r)) for r in c["rings"]))
        for c in data["countries"]
    ]
    shapes += [
        Shape(country_code="US", us_state=s["postal"], name=s["name"],
              rings=tuple(tuple(map(tuple, r)) for r in s["rings"]))
        for s in data["us_states"]
    ]
    outlined = {s.country_code for s in shapes}
    shapes += [
        Shape(country_code=code, point=point)
        for code, point in SMALL_TERRITORIES.items() if code not in outlined
    ]
    return shapes


@dataclass
class Viewport:
    """
    Maps the map (in map units) to the widget (in pixels), keeping the map's
    aspect ratio, with zoom and pan.
    """
    width: float = 1.0
    height: float = 1.0
    zoom: float = MIN_ZOOM
    pan_x: float = 0.0
    pan_y: float = 0.0

    @property
    def scale(self) -> float:
        """Pixels per map unit at zoom 1."""
        return min(self.width, self.height / MAP_ASPECT)

    @property
    def origin(self) -> Tuple[float, float]:
        """Top-left corner of the map at zoom 1 (the map is centered)."""
        return ((self.width - self.scale) / 2,
                (self.height - self.scale * MAP_ASPECT) / 2)

    def resize(self, width: float, height: float):
        """Sets the widget size."""
        self.width, self.height = max(width, 1.0), max(height, 1.0)
        self.clamp()

    def to_screen(self, lon: float, lat: float) -> Tuple[float, float]:
        """Widget position (pixels) of a geographic position."""
        u, v = project(lon, lat)
        ox, oy = self.origin
        return (self.pan_x + self.zoom * (ox + u * self.scale),
                self.pan_y + self.zoom * (oy + v * self.scale))

    def from_screen(self, x: float, y: float) -> Tuple[float, float]:
        """Geographic position under a widget position (pixels)."""
        ox, oy = self.origin
        u = ((x - self.pan_x) / self.zoom - ox) / self.scale
        v = ((y - self.pan_y) / self.zoom - oy) / self.scale
        return unproject(u, v)

    def zoom_at(self, x: float, y: float, factor: float):
        """Zooms by ``factor`` keeping the map position under (x, y) fixed."""
        zoom = min(MAX_ZOOM, max(MIN_ZOOM, self.zoom * factor))
        ratio = zoom / self.zoom
        self.pan_x = x - (x - self.pan_x) * ratio
        self.pan_y = y - (y - self.pan_y) * ratio
        self.zoom = zoom
        self.clamp()

    def pan_by(self, dx: float, dy: float):
        """Moves the map by a number of pixels."""
        self.pan_x += dx
        self.pan_y += dy
        self.clamp()

    def clamp(self):
        """Keeps the map covering the widget (or centered if smaller than it)."""
        ox, oy = self.origin
        self.pan_x = self._clamp_axis(self.pan_x, self.width, ox, ox + self.scale)
        self.pan_y = self._clamp_axis(
            self.pan_y, self.height, oy, oy + self.scale * MAP_ASPECT
        )

    def _clamp_axis(self, pan: float, size: float, start: float, end: float) -> float:
        if (end - start) * self.zoom <= size:
            return (size - (start + end) * self.zoom) / 2
        return min(-self.zoom * start, max(size - self.zoom * end, pan))


def hit_test(
    shapes: Iterable[Shape], viewport: Viewport, x: float, y: float,
    point_radius: float = 8.0
) -> Optional[Shape]:
    """
    Returns the shape under the widget position (x, y), if any. Dots are
    tested first as they are drawn above the outlines.
    """
    shapes = list(shapes)
    for shape in shapes:
        if shape.point:
            sx, sy = viewport.to_screen(*shape.point)
            if math.hypot(sx - x, sy - y) <= point_radius:
                return shape
    lon, lat = viewport.from_screen(x, y)
    for shape in shapes:
        if not shape.point and shape.contains(lon, lat):
            return shape
    return None
