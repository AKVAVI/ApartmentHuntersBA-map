#!/usr/bin/env python3
"""Recolor OpenFreeMap's "bright" vector style into the site's palette and
write data/basemap-style.json (loaded by the map via MapLibre GL).

Source style: https://tiles.openfreemap.org/styles/bright (free, no API key,
OpenStreetMap data, ODbL). Run: python3 scripts/build_basemap_style.py
"""
import json
import urllib.request

SRC = "https://tiles.openfreemap.org/styles/bright"

BG = "#f7f6f3"
INK = "#2b2a28"
MUTED = "#6f695f"
ACCENT = "#b5693b"
WATER = "#cddde3"
PARK = "#dde7d3"
WOOD = "#cfdcc3"
BUILDING = "#ebe5dc"
BUILDING_EDGE = "#ddd5c8"
ROAD = "#ffffff"
ROAD_CASING = "#e6e1d8"
MAJOR = "#f7e8da"
MAJOR_CASING = "#e0bf9f"
MOTORWAY = "#efcaa8"
MOTORWAY_CASING = "#c99467"
RAIL = "#cdc6ba"


def pick(layer_id, prop, old):
    i = layer_id
    if prop == "background-color":
        return BG
    if i.startswith("water") or i.startswith("waterway"):
        if prop in ("fill-color", "line-color"):
            return WATER
        if prop == "text-color":
            return "#6b8794"
    if i.startswith("landcover-wood"):
        return WOOD if prop == "fill-color" else old
    if i.startswith(("park", "landcover-grass")):
        return PARK
    if i.startswith("landuse-cemetery"):
        return "#e3e6dc"
    if i.startswith("landuse-hospital"):
        return "#f3e3e3"
    if i.startswith("landuse-school"):
        return "#eee8f0"
    if i.startswith("landuse"):
        return "rgba(220,213,200,0.25)"
    if i.startswith("landcover-sand"):
        return "#efe8d2"
    if i.startswith("building"):
        return BUILDING_EDGE if "outline" in prop else BUILDING
    if "motorway" in i or "trunk" in i:
        return MOTORWAY_CASING if "casing" in i else MOTORWAY
    if "primary" in i or "secondary" in i or "link" in i:
        return MAJOR_CASING if "casing" in i else MAJOR
    if "minor" in i or "service" in i:
        return ROAD_CASING if "casing" in i else ROAD
    if "path" in i:
        return "#d9cfc0"
    if "railway" in i:
        return RAIL
    if i.startswith("highway-area") or i.startswith("road_area"):
        return "#efeae1" if prop == "fill-color" else ROAD_CASING
    if i.startswith("aeroway"):
        return "#efeae1" if "area" in i else "#e2dccf"
    if i.startswith("boundary"):
        return "#cdbfae"
    if i.startswith("poi_transit"):
        return ACCENT if prop == "text-color" else BG
    if i.startswith(("poi", "highway-name", "airport")):
        return MUTED if prop == "text-color" else BG
    if i.startswith("label"):
        return INK if prop == "text-color" else BG
    return old


def main():
    req = urllib.request.Request(SRC, headers={"User-Agent": "EstateArgMap/1.0"})
    style = json.load(urllib.request.urlopen(req))
    for layer in style["layers"]:
        paint = layer.get("paint", {})
        for prop, old in list(paint.items()):
            if prop.endswith("color") and "halo" not in prop or prop == "text-halo-color":
                new = pick(layer["id"], prop, old)
                if prop == "text-halo-color":
                    new = BG
                paint[prop] = new
    json.dump(style, open("data/basemap-style.json", "w"), ensure_ascii=False)
    print("layers:", len(style["layers"]))


if __name__ == "__main__":
    main()
