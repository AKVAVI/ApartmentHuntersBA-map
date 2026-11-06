#!/usr/bin/env python3
"""Classify every object in data/objects.json into one of the sub-barrios in
data/subbarrios.geojson, purely by point-in-polygon against its existing
coordinates — never by hand, never by guessing.

The four current zones (Palermo Chico, Palermo Soho, Palermo Hollywood,
Las Cañitas) are built to be mutually exclusive (see
scripts/build_subbarrios_v2.py and docs/subbarrios-sources.md): verified to
have zero pairwise edge-crossings before this script runs. So a point
should match at most one zone. If it ever matches more than one, that is a
real problem with the polygons, not something to silently resolve by
picking "the smallest one" — this script stops and reports it instead of
guessing.

Fields written per object:
  - sub_barrio: the matching zone's name, or "" if the point falls outside
    all four (left unassigned rather than guessed).
  - sub_barrio_boundary_version: the polygon version used, so a later
    boundary redraw can be told apart from this classification.
"""
import json
import sys


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


def main():
    subbarrios = json.load(open("data/subbarrios.geojson"))
    objects = json.load(open("data/objects.json"))

    polys = [
        {"name": f["properties"]["name"], "version": f["properties"]["version"], "ring": f["geometry"]["coordinates"][0]}
        for f in subbarrios["features"]
    ]

    ambiguous = []
    classified = 0
    for obj in objects:
        obj["sub_barrio"] = ""
        obj["sub_barrio_boundary_version"] = ""
        if obj.get("lat") is None or obj.get("lng") is None:
            continue
        matches = [p for p in polys if point_in_ring(obj["lng"], obj["lat"], p["ring"])]
        if len(matches) > 1:
            ambiguous.append((obj["id"], [m["name"] for m in matches]))
            continue
        if matches:
            obj["sub_barrio"] = matches[0]["name"]
            obj["sub_barrio_boundary_version"] = matches[0]["version"]
            classified += 1

    if ambiguous:
        print("ERROR: these objects matched more than one sub-barrio — the", file=sys.stderr)
        print("zones are supposed to be mutually exclusive, so this means the", file=sys.stderr)
        print("polygons overlap somewhere. Left unassigned; fix the polygons", file=sys.stderr)
        print("(do not resolve this by picking one) before trusting this data:", file=sys.stderr)
        for obj_id, names in ambiguous:
            print(f"  {obj_id}: {names}", file=sys.stderr)

    json.dump(objects, open("data/objects.json", "w"), ensure_ascii=False, indent=2)

    from collections import Counter
    print(f"{classified}/{len(objects)} objects matched a sub-barrio ({len(ambiguous)} ambiguous)")
    print(Counter(o["sub_barrio"] for o in objects if o["sub_barrio"]))


if __name__ == "__main__":
    main()
