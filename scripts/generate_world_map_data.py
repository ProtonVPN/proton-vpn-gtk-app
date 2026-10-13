#!/usr/bin/env python3
"""
Generates proton/vpn/app/gtk/assets/map/world.json, the geometry used by the
world map view of the server list.

Source: Natural Earth 1:110m (public domain, https://www.naturalearthdata.com):
    ne_110m_admin_0_countries.geojson
    ne_110m_admin_1_states_provinces.geojson

Usage:
    scripts/generate_world_map_data.py COUNTRIES.geojson STATES.geojson
"""
import json
import sys
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "proton/vpn/app/gtk/assets/map/world.json"

# Natural Earth country codes that differ from the ones used by Proton.
CODE_ALIASES = {"GB": "UK"}


def country_code(properties: dict) -> str | None:
    """Returns the country code, working around Natural Earth's "-99" placeholders."""
    for key in ("ISO_A2_EH", "ISO_A2", "WB_A2"):
        code = properties.get(key)
        if code and code != "-99":
            return CODE_ALIASES.get(code, code)
    return None


def rings(geometry: dict) -> list[list[list[float]]]:
    """Returns the outer ring of each polygon, with coordinates rounded to 2 decimals."""
    polygons = (
        geometry["coordinates"] if geometry["type"] == "MultiPolygon"
        else [geometry["coordinates"]]
    )
    return [[[round(x, 2), round(y, 2)] for x, y in polygon[0]] for polygon in polygons]


def main(countries_path: str, states_path: str):
    """Writes the compact map data file."""
    countries = json.loads(Path(countries_path).read_text(encoding="utf-8"))["features"]
    states = json.loads(Path(states_path).read_text(encoding="utf-8"))["features"]
    data = {
        "countries": [
            {"code": country_code(f["properties"]), "rings": rings(f["geometry"])}
            for f in countries
            if country_code(f["properties"]) not in (None, "US")
        ],
        "us_states": [
            {"name": f["properties"]["name"], "postal": f["properties"]["postal"],
             "rings": rings(f["geometry"])}
            for f in states
        ],
    }
    OUTPUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main(countries_path=sys.argv[1], states_path=sys.argv[2])
