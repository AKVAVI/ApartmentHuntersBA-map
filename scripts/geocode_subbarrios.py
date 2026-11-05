#!/usr/bin/env python3
"""Build approximate polygons for informal sub-barrios from their documented
street boundaries.

Method: pull each boundary street's real OSM line geometry (Overpass API),
keep only the points within ~1.3km of the parent barrio's centre (so a long
avenue only contributes the stretch that actually runs past this
sub-barrio), pool the points from all of a sub-barrio's boundary streets,
and take their convex hull. This hugs the named streets without depending
on fragile exact-intersection lookups (most of these avenues don't
literally cross within the area, or OSM splits them into many short ways).

This is a best-effort approximation of a boundary that, by definition, has
no official geometry — see docs/subbarrios-sources.md for the source of
each street list and its confidence level.

Writes data/subbarrios_informal_raw.json (intermediate; merged by hand into
data/subbarrios.geojson together with the APH-derived hulls from
extract_aph_hulls.py).
"""
import json
import math
import time
import urllib.parse
import urllib.request

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "EstateArgMap/1.0 (contact: lukomorie1@gmail.com)"

# Centers are the centroid of this project's own already-geocoded listings
# in each sub-barrio (data/objects.json) where available — grounded in real
# addresses rather than a guess. Palermo Nuevo has no listings yet, so its
# center is a manual estimate near Plaza Italia (the area the sources place
# it in: between Santa Fe, Sarmiento, Av. del Libertador and the old
# San Martín rail line).
SUBBARRIOS_INFORMAL = [
    {"id": "palermo_soho", "name": "Palermo Soho", "parent": "palermo", "radius_km": 1.0,
     "center": (-34.5871, -58.4295),
     "streets": ["Avenida Raúl Scalabrini Ortiz", "Avenida Córdoba", "Avenida Juan Bautista Justo", "Avenida Santa Fe"]},
    {"id": "palermo_hollywood", "name": "Palermo Hollywood", "parent": "palermo", "radius_km": 1.0,
     "center": (-34.5788, -58.4363),
     "streets": ["Avenida Juan Bautista Justo", "Avenida Córdoba", "Avenida Dorrego", "Avenida Santa Fe"]},
    {"id": "palermo_viejo", "name": "Palermo Viejo", "parent": "palermo", "radius_km": 1.2,
     "center": (-34.5906, -58.4329),
     "streets": ["Avenida Córdoba", "Avenida Santa Fe", "Avenida Dorrego", "Avenida Raúl Scalabrini Ortiz"]},
    {"id": "palermo_nuevo", "name": "Palermo Nuevo", "parent": "palermo", "radius_km": 1.3,
     "center": (-34.5800, -58.4120),
     "streets": ["Avenida Santa Fe", "Sarmiento", "Avenida Del Libertador", "Avenida Cabildo"]},
    {"id": "las_canitas", "name": "Las Cañitas", "parent": "palermo", "radius_km": 1.0,
     "center": (-34.5695, -58.4328),
     "streets": ["Avenida Luis María Campos", "Matienzo", "Avenida Del Libertador", "Avenida Dorrego"]},
    {"id": "belgrano_c", "name": "Belgrano C", "parent": "belgrano", "radius_km": 0.8,
     "center": (-34.5542, -58.4550),
     "streets": ["Avenida Cabildo", "Olazábal", "Congreso", "Conesa"]},
    {"id": "bajo_belgrano", "name": "Bajo Belgrano", "parent": "belgrano", "radius_km": 0.85,
     "center": (-34.5528, -58.4482),
     "streets": ["Avenida Cabildo", "Avenida Del Libertador", "Avenida Monroe", "Avenida Leopoldo Lugones"]},
]

ALL_STREETS = sorted({s for sb in SUBBARRIOS_INFORMAL for s in sb["streets"]})
CACHE_PATH = "/tmp/subbarrio_streets_osm.json"


def overpass_fetch_streets(names):
    name_full = "|".join(names)
    query = f"""
[out:json][timeout:90];
area["name"="Ciudad Autónoma de Buenos Aires"]["admin_level"="4"]->.caba;
way["highway"]["name"~"^({name_full})$"](area.caba);
out geom;
"""
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(OVERPASS_URL, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


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


def points_for_street(name, elements):
    pts = []
    for el in elements:
        if el["type"] != "way":
            continue
        if el.get("tags", {}).get("name") != name:
            continue
        for g in el.get("geometry", []):
            pts.append((g["lon"], g["lat"]))
    return pts


def main():
    if __import__("os").path.exists(CACHE_PATH):
        print("using cached OSM fetch:", CACHE_PATH)
        osm = json.load(open(CACHE_PATH))
    else:
        print("Fetching street geometries from Overpass...")
        osm = overpass_fetch_streets(ALL_STREETS)
        json.dump(osm, open(CACHE_PATH, "w"))
        time.sleep(1)
    elements = osm["elements"]
    print(f"  got {len(elements)} ways")

    out = {}
    for sb in SUBBARRIOS_INFORMAL:
        print(f"--- {sb['name']} ---")
        clat, clon = sb["center"]
        radius = sb["radius_km"]
        pooled = []
        for street in sb["streets"]:
            pts = points_for_street(street, elements)
            nearby = [(lon, lat) for lon, lat in pts if haversine_km(clat, clon, lat, lon) <= radius]
            print(f"    {street}: {len(pts)} pts total, {len(nearby)} within {radius}km")
            pooled.extend(nearby)
        if len(pooled) < 3:
            print("    NOT ENOUGH POINTS")
            out[sb["id"]] = {"name": sb["name"], "parent_barrio": sb["parent"].title(),
                              "streets": sb["streets"], "ring": None}
            continue
        hull = convex_hull(pooled)
        ring = [[lon, lat] for lon, lat in hull]
        ring.append(ring[0])
        out[sb["id"]] = {"name": sb["name"], "parent_barrio": sb["parent"].title(),
                          "streets": sb["streets"], "ring": ring, "hull_vertices": len(hull)}
        json.dump(out, open("data/subbarrios_informal_raw.json", "w"), ensure_ascii=False, indent=2)
    print("done")


if __name__ == "__main__":
    main()
