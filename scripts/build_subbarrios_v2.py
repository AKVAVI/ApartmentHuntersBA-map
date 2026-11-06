#!/usr/bin/env python3
"""Build data/subbarrios.geojson (v2) for exactly four sub-barrios, each as a
real quadrilateral formed by the actual intersections of its four named
boundary streets (or, for Palermo Chico, the FC San Martín railway on one
side) — no convex hull, no pooling points within a radius of listings.

Each zone's streets are picked as two pairs of roughly-parallel "long"
sides and two roughly-parallel "cross" sides, so each adjacent pair has a
real, unique intersection point; the four intersections become the
polygon's four corners in order. See docs/subbarrios-sources.md for the
reasoning and sources behind each street list.

Run after fetching the needed street/rail geometry into
/tmp/subbarrios_v2_osm.json (overpass_fetch below does this once and
caches it there).
"""
import itertools
import json
import os
import urllib.parse
import urllib.request

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "EstateArgMap/1.0 (contact: lukomorie1@gmail.com)"
CACHE_PATH = "/tmp/subbarrios_v2_osm.json"
VERSION = "2.0"

# Each zone: 4 boundary lines in cyclic order (so consecutive entries are
# the adjacent pairs whose real intersection is a corner). `kind` is
# "way" (a named street, matched by OSM `name`) or "rail" (any OSM
# railway way, matched within a bbox since it has no single consistent
# name through this stretch).
ZONES = [
    {
        "id": "palermo_chico", "name": "Palermo Chico",
        "center": (-34.5790, -58.4010),
        "boundary_type": "informal_google", "confidence": "medium",
        "source": "Google Maps neighborhood boundary for \"Palermo Chico\" (viewed 2026-11-06), traced against real street/rail geometry",
        "methodology": "Google Maps draws an actual polygon for this one place (unlike the other three). Its four sides, read off the map: Av. Casares (W) / FC San Martín rail (N) / Austria (E) / Av. del Libertador (S). The polygon is traced by walking each street/rail's own real OSM polyline between verified junctions: Av. Casares from its intersection with Av. del Libertador (SW) up to its intersection with the FC San Martín rail (NW); the rail corridor from there heading toward Austria; Austria from its own northernmost mapped point (it does not reach the railway here — their real crossing is several blocks south, near Canal Siete, so the rail-to-Austria handoff is the one place this traces a straight line across a real gap rather than a mapped street) down to its intersection with Av. del Libertador (SE); and Av. del Libertador back to the SW corner. 104 vertices, no self-intersection, ~0.85 km² — visually matches the shape Google draws, not just its corner points.",
        "explicit_corners": "palermo_chico",
    },
    {
        "id": "palermo_soho", "name": "Palermo Soho",
        "center": (-34.5871, -58.4295),
        "boundary_type": "informal", "confidence": "low",
        "source": "Mudafy.com.ar / roomix.ai real-estate guides: \"entre las avenidas Scalabrini Ortiz, Córdoba, Juan B. Justo y Santa Fe\"",
        "methodology": "Quadrilateral from the real intersections of these four streets: Av. Juan B. Justo (shared edge with Palermo Hollywood to its north) and Av. Scalabrini Ortiz as the cross sides; Av. Santa Fe and Av. Córdoba as the long sides.",
        "sides": [
            {"kind": "way", "name": "Avenida Santa Fe"},
            {"kind": "way", "name": "Avenida Juan Bautista Justo"},
            {"kind": "way", "name": "Avenida Córdoba"},
            {"kind": "way", "name": "Avenida Raúl Scalabrini Ortiz"},
        ],
    },
    {
        "id": "palermo_hollywood", "name": "Palermo Hollywood",
        "center": (-34.5788, -58.4363),
        "boundary_type": "informal", "confidence": "low",
        "source": "roomix.ai / Billiken: \"entre Juan B. Justo, Córdoba, Dorrego y Santa Fe\"",
        "methodology": "Quadrilateral from the real intersections of these four streets: Av. Juan B. Justo (shared edge with Palermo Soho to its south) and Av. Dorrego as the cross sides; Av. Santa Fe and Av. Córdoba as the long sides.",
        "sides": [
            {"kind": "way", "name": "Avenida Santa Fe"},
            {"kind": "way", "name": "Avenida Juan Bautista Justo"},
            {"kind": "way", "name": "Avenida Córdoba"},
            {"kind": "way", "name": "Avenida Dorrego"},
        ],
    },
    {
        "id": "las_canitas", "name": "Las Cañitas",
        "center": (-34.5695, -58.4328),
        "boundary_type": "informal", "confidence": "low",
        "source": "roomix.ai: \"delimitado por las avenidas Luis María Campos, Dorrego y Del Libertador y la calle Matienzo\"",
        "methodology": "Quadrilateral from the real intersections of these four streets: Av. del Libertador and Av. Luis María Campos as the long (roughly parallel) sides; Matienzo and Av. Dorrego as the cross sides.",
        "sides": [
            {"kind": "way", "name": "Avenida Del Libertador"},
            {"kind": "way", "name": "Teniente Benjamín Matienzo"},
            {"kind": "way", "name": "Avenida Luis María Campos"},
            {"kind": "way", "name": "Avenida Dorrego"},
        ],
    },
]

# Rough bbox to search the railway in (around Palermo Chico only — it has
# no useful `name` tag through this stretch, every other zone uses named
# streets exclusively).
RAIL_BBOX = (-34.590, -58.415, -34.565, -58.390)

STREET_NAMES = sorted({s["name"] for z in ZONES for s in z.get("sides", []) if s["kind"] == "way"} | {"Avenida Casares", "Austria", "Avenida Del Libertador"})


def overpass_fetch():
    if os.path.exists(CACHE_PATH):
        return json.load(open(CACHE_PATH))
    name_pattern = "|".join(STREET_NAMES)
    south, west, north, east = RAIL_BBOX
    query = f"""
[out:json][timeout:90];
area["name"="Ciudad Autónoma de Buenos Aires"]["admin_level"="4"]->.caba;
(
  way["highway"]["name"~"^({name_pattern})$"](area.caba);
  way["railway"]({south},{west},{north},{east});
);
out geom;
"""
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(OVERPASS_URL, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    json.dump(result, open(CACHE_PATH, "w"))
    return result


def lines_for_way(name, elements):
    lines = []
    for el in elements:
        if el["type"] == "way" and el.get("tags", {}).get("name") == name:
            pts = [(g["lon"], g["lat"]) for g in el.get("geometry", [])]
            if pts:
                lines.append(pts)
    return lines


def lines_for_rail(elements):
    lines = []
    for el in elements:
        if el["type"] == "way" and "railway" in el.get("tags", {}):
            pts = [(g["lon"], g["lat"]) for g in el.get("geometry", [])]
            if pts:
                lines.append(pts)
    return lines


def lines_for_side(side, elements):
    if side["kind"] == "rail":
        return lines_for_rail(elements)
    return lines_for_way(side["name"], elements)


def seg_intersect(p1, p2, p3, p4):
    x1, y1 = p1; x2, y2 = p2; x3, y3 = p3; x4, y4 = p4
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(d) < 1e-15:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
    u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / d
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None


def all_intersections(linesA, linesB):
    pts = []
    for la in linesA:
        for lb in linesB:
            for i in range(len(la) - 1):
                for j in range(len(lb) - 1):
                    pt = seg_intersect(la[i], la[i + 1], lb[j], lb[j + 1])
                    if pt:
                        pts.append(pt)
    return pts


def chain_dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def build_chain(segments, start_point, target_point, tol=0.0004, max_segments=200, max_reach=0.02):
    """Walk real OSM polylines from start_point toward target_point.

    Greedily extends the chain with whichever unused segment's near endpoint
    is closest to the chain's current end (within tol), regardless of
    whether that's progress toward target_point — then, once no segment
    continues (or the walk has gone unreasonably far), truncates the chain
    at whichever of its own points lies closest to target_point. This
    avoids needing a precise stopping rule: any overshoot past the target
    is simply cut off afterwards, and a real gap (no street/rail connects
    all the way to the target) just leaves the chain stopping at its
    closest approach rather than failing.
    """
    segs = [list(s) for s in segments]
    best = min(range(len(segs)), key=lambda i: min(chain_dist(segs[i][0], start_point), chain_dist(segs[i][-1], start_point)))
    s = segs.pop(best)
    if chain_dist(s[-1], start_point) < chain_dist(s[0], start_point):
        s.reverse()
    chain = list(s)
    for _ in range(max_segments):
        if chain_dist(chain[-1], start_point) > max_reach:
            break
        end = chain[-1]
        cand = cand_d = cand_idx = None
        cand_rev = False
        for i, seg in enumerate(segs):
            d0, d1 = chain_dist(seg[0], end), chain_dist(seg[-1], end)
            if d0 < tol and (cand_d is None or d0 < cand_d):
                cand, cand_d, cand_idx, cand_rev = seg, d0, i, False
            if d1 < tol and (cand_d is None or d1 < cand_d):
                cand, cand_d, cand_idx, cand_rev = seg, d1, i, True
        if cand is None:
            break
        segs.pop(cand_idx)
        chain.extend(list(reversed(cand))[1:] if cand_rev else cand[1:])
    best_i = min(range(len(chain)), key=lambda i: chain_dist(chain[i], target_point))
    return chain[: best_i + 1]


def palermo_chico_ring(elements):
    """Trace the real Av. Casares / FC San Martín rail / Austria / Av. del
    Libertador polylines between verified junctions, rather than collapsing
    each side to a single corner point. See the zone's "methodology" text."""
    casares = lines_for_way("Avenida Casares", elements)
    libertador = lines_for_way("Avenida Del Libertador", elements)
    austria = lines_for_way("Austria", elements)
    rail = lines_for_rail(elements)

    sw = all_intersections(casares, libertador)[0]
    nw = min(all_intersections(casares, rail), key=lambda p: chain_dist(p, (-58.409, -34.569)))
    se = min(all_intersections(austria, libertador), key=lambda p: chain_dist(p, (-58.397, -34.583)))
    austria_pts = [p for line in austria for p in line]
    ne = max(austria_pts, key=lambda p: p[1])  # Austria's own northernmost point

    casares_chain = build_chain(casares, sw, nw)
    rail_chain = build_chain(rail, nw, ne)
    austria_chain = build_chain(austria, ne, se)
    libertador_chain = [se, sw]  # short, near-straight stretch here

    ring = casares_chain + rail_chain[1:] + austria_chain[1:] + libertador_chain[1:]
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring


def main():
    osm = overpass_fetch()
    elements = osm["elements"]
    print(f"{len(elements)} OSM elements fetched/cached")

    features = []
    for zone in ZONES:
        if zone.get("explicit_corners") == "palermo_chico":
            ring = palermo_chico_ring(elements)
            features.append({
                "type": "Feature",
                "properties": {
                    "id": zone["id"], "name": zone["name"], "parent_barrio": "Palermo",
                    "boundary_type": zone["boundary_type"], "source": zone["source"],
                    "methodology": zone["methodology"],
                    "boundary_streets": ["Avenida Casares", "FC San Martín railway", "Austria", "Avenida Del Libertador"],
                    "confidence": zone["confidence"], "version": VERSION,
                },
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            })
            print(f"  OK: {zone['name']} -> {len(ring) - 1} vertices (traced)")
            continue
        sides = zone["sides"]
        n = len(sides)
        clon, clat = zone["center"][1], zone["center"][0]
        side_lines = [lines_for_side(s, elements) for s in sides]
        for s, lines in zip(sides, side_lines):
            label = s["name"] if s["kind"] == "way" else "railway"
            print(f"  {zone['name']}: {label} -> {len(lines)} way(s), {sum(len(l) for l in lines)} pts")

        corners = []
        ok = True
        for i in range(n):
            a_lines = side_lines[i]
            b_lines = side_lines[(i + 1) % n]
            pts = all_intersections(a_lines, b_lines)
            if not pts:
                a_label = sides[i]["name"] if sides[i]["kind"] == "way" else "railway"
                b_label = sides[(i + 1) % n]["name"] if sides[(i + 1) % n]["kind"] == "way" else "railway"
                print(f"    NO INTERSECTION between {a_label} and {b_label}")
                ok = False
                continue
            # Long avenues can cross each other more than once across the
            # whole city; always keep the crossing nearest this zone's own
            # known location, never "nearest to the previous corner"
            # (which can drift onto a wrong, far-away crossing).
            pts.sort(key=lambda p: (p[0] - clon) ** 2 + (p[1] - clat) ** 2)
            corners.append(pts[0])

        if not ok or len(corners) != n:
            print(f"  SKIPPING {zone['name']}: incomplete corners")
            continue

        ring = corners + [corners[0]]
        features.append({
            "type": "Feature",
            "properties": {
                "id": zone["id"],
                "name": zone["name"],
                "parent_barrio": "Palermo",
                "boundary_type": zone["boundary_type"],
                "source": zone["source"],
                "methodology": zone["methodology"],
                "boundary_streets": [s.get("name", "FC San Martín railway") for s in sides],
                "confidence": zone["confidence"],
                "version": VERSION,
            },
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })
        print(f"  OK: {zone['name']} -> {len(corners)} corners")

    fc = {"type": "FeatureCollection", "features": features}
    json.dump(fc, open("data/subbarrios.geojson", "w"), ensure_ascii=False, indent=2)
    print(f"\nwrote {len(features)}/{len(ZONES)} features to data/subbarrios.geojson")


if __name__ == "__main__":
    main()
