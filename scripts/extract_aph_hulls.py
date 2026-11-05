#!/usr/bin/env python3
"""One-off: derive approximate polygons for APH3 (Palermo Chico) and APH4
(Belgrano R) as the convex hull of the officially cataloged parcels tagged
with that APH number in the city's "Áreas de Protección Histórica" GeoJSON.

This is NOT the exact legal boundary (that only exists as a plan annex to
the Código Urbanístico, published as a PDF, not open geodata) — it is a
convex hull around every building the city's own catalog places inside
that APH, which is why boundary_type is "official_aph_hull" rather than
"official".

Source file is huge (~250MB, per-parcel) and not meant to be committed;
run this once against a local copy and paste the resulting hulls into
data/subbarrios.geojson.
"""
import json
import sys

APH_SOURCE = "/tmp/aph.geojson"  # downloaded from data.buenosaires.gob.ar, not committed


def convex_hull(points):
    points = sorted(set(points))
    if len(points) <= 2:
        return points

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def points_for_aph(prefix):
    pts = []
    with open(APH_SOURCE, encoding="utf-8") as f:
        data = json.load(f)
    for feat in data["features"]:
        tag = feat["properties"].get("APH_NRO_Y_") or ""
        if not tag.startswith(prefix):
            continue
        geom = feat["geometry"]
        coords = geom["coordinates"]
        if geom["type"] == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    for x, y in ring:
                        pts.append((x, y))
        elif geom["type"] == "Polygon":
            for ring in coords:
                for x, y in ring:
                    pts.append((x, y))
    return pts


def main():
    for prefix, name in [("003", "palermo_chico"), ("004", "belgrano_r")]:
        pts = points_for_aph(prefix)
        hull = convex_hull(pts)
        hull_closed = hull + [hull[0]]
        print(name, "parcels_points:", len(pts), "hull_vertices:", len(hull))
        print(json.dumps(hull_closed))
        print()


if __name__ == "__main__":
    main()
