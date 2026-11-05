#!/usr/bin/env python3
"""Classify every object in data/objects.json into a sub-barrio, purely by
point-in-polygon test against data/subbarrios.geojson — never by hand.
Coordinates (lat/lng) stay the source of truth; this only adds:

  - sub_barrio: the matching sub-barrio's name, or "" if the point falls
    outside every polygon (left unassigned rather than guessed).
  - sub_barrio_boundary_version: the polygon version used, so a later
    boundary redraw can be told apart from this classification.

If a point falls inside more than one polygon (expected: Palermo Soho/
Hollywood/Viejo overlap by definition in the sources), all matches are kept
in sub_barrios (list) and sub_barrio holds the first/smallest-area match.
"""
import json


def point_in_ring(x, y, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def ring_area(ring):
    a = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def main():
    subbarrios = json.load(open("data/subbarrios.geojson"))
    objects = json.load(open("data/objects.json"))

    polys = []
    for feat in subbarrios["features"]:
        ring = feat["geometry"]["coordinates"][0]
        polys.append({
            "name": feat["properties"]["name"],
            "version": feat["properties"]["version"],
            "ring": ring,
            "area": ring_area(ring),
        })

    classified = 0
    for obj in objects:
        if obj.get("lat") is None or obj.get("lng") is None:
            obj["sub_barrio"] = ""
            obj["sub_barrios"] = []
            obj["sub_barrio_boundary_version"] = ""
            continue
        matches = [p for p in polys if point_in_ring(obj["lng"], obj["lat"], p["ring"])]
        matches.sort(key=lambda p: p["area"])  # smallest/most-specific first
        obj["sub_barrios"] = [m["name"] for m in matches]
        obj["sub_barrio"] = matches[0]["name"] if matches else ""
        obj["sub_barrio_boundary_version"] = matches[0]["version"] if matches else ""
        if matches:
            classified += 1

    json.dump(objects, open("data/objects.json", "w"), ensure_ascii=False, indent=2)
    print(f"{classified}/{len(objects)} objects matched a sub-barrio")
    from collections import Counter
    print(Counter(o["sub_barrio"] for o in objects if o["sub_barrio"]))


if __name__ == "__main__":
    main()
