#!/usr/bin/env python3
"""Geocode EstateArg object addresses via Nominatim (OSM), with on-disk cache.

Usage: python3 scripts/geocode.py
Reads data/objects_raw.json, writes data/geocode_cache.json (cache) and
data/objects.json (objects with lat/lng filled in, approx flag set when
the match came from a district-level fallback rather than the exact address).
"""
import json
import re
import time
import urllib.parse
import urllib.request
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE_DIR, "data", "objects_raw.json")
CACHE_PATH = os.path.join(BASE_DIR, "data", "geocode_cache.json")
OUT_PATH = os.path.join(BASE_DIR, "data", "objects.json")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "EstateArgMap/1.0 (contact: lukomorie1@gmail.com)"

# District/barrio centroids used as a last-resort fallback when an address
# cannot be geocoded at all (approximate, hand-picked near each barrio's center).
DISTRICT_FALLBACK = {
    "villa crespo": (-34.5995, -58.4390),
    "recoleta": (-34.5890, -58.3974),
    "palermo": (-34.5780, -58.4290),
    "palermo hollywood": (-34.5780, -58.4380),
    "palermo soho": (-34.5880, -58.4280),
    "palermo viejo": (-34.5850, -58.4300),
    "palermo chico": (-34.5790, -58.4040),
    "las cañitas": (-34.5630, -58.4460),
    "colegiales": (-34.5740, -58.4500),
    "belgrano": (-34.5630, -58.4560),
    "belgrano r": (-34.5600, -58.4650),
    "belgrano c": (-34.5650, -58.4530),
    "belgrano chico": (-34.5610, -58.4530),
    "bajo belgrano": (-34.5590, -58.4620),
    "barrio norte": (-34.5940, -58.3990),
    "saavedra": (-34.5520, -58.4890),
    "boedo": (-34.6290, -58.4190),
}


def clean_address(address, district):
    a = address
    # drop parenthetical notes like "(Torre QUO)" or "(на границе)"
    a = re.sub(r"\([^)]*\)", "", a)
    # drop trailing clarifications after " / "
    a = a.strip()
    # intersections: "X y Av. Y" -> keep as-is, Nominatim handles "X and Y" poorly in es;
    # try "X esquina Y" style which free-form search tends to match better
    a = re.sub(r"\s+y\s+", " esquina ", a, flags=re.IGNORECASE)
    a = a.replace("Av.", "Avenida")
    return a.strip()


def normalize_district(district):
    d = district.lower()
    d = re.sub(r"\([^)]*\)", "", d)
    d = d.split("/")[0].strip()
    return d


def nominatim_search(query):
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "ar",
    }
    url = NOMINATIM_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None


def main():
    objs = json.load(open(RAW_PATH, encoding="utf-8"))

    cache = {}
    if os.path.exists(CACHE_PATH):
        cache = json.load(open(CACHE_PATH, encoding="utf-8"))

    for o in objs:
        if o.get("address") and "нет точного адреса" not in o["address"]:
            addr = clean_address(o["address"], o["district"])
            queries = [
                f"{addr}, {normalize_district(o['district']).title()}, Ciudad Autónoma de Buenos Aires, Argentina",
                f"{addr}, Ciudad Autónoma de Buenos Aires, Argentina",
            ]
        else:
            addr = None
            queries = []

        cache_key = o["id"]
        if cache_key in cache and cache[cache_key].get("lat") and not cache[cache_key].get("stale"):
            result = cache[cache_key]
        else:
            result = {"lat": None, "lng": None, "approx": True, "query": None}
            for query in queries:
                print(f"geocoding {o['id']}: {query}")
                try:
                    hit = nominatim_search(query)
                except Exception as e:
                    print(f"  error: {e}")
                    hit = None
                time.sleep(1.1)  # Nominatim usage policy: max 1 req/sec
                if hit:
                    result = {"lat": hit[0], "lng": hit[1], "approx": False, "query": query}
                    break
            cache[cache_key] = result
            json.dump(cache, open(CACHE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

        if result.get("lat") is None:
            # fallback to district centroid
            d = normalize_district(o["district"])
            fallback = DISTRICT_FALLBACK.get(d)
            if fallback:
                result = {"lat": fallback[0], "lng": fallback[1], "approx": True, "query": query}
                print(f"  fallback to district centroid for {o['id']} ({d})")
            else:
                print(f"  NO MATCH and no fallback for {o['id']} (district={o['district']!r})")

        o["lat"] = result.get("lat")
        o["lng"] = result.get("lng")
        o["coords_approx"] = bool(result.get("approx", True))

    json.dump(objs, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    missing = [o["id"] for o in objs if o["lat"] is None]
    approx = [o["id"] for o in objs if o["coords_approx"]]
    print(f"\nDone. {len(objs)} objects, {len(missing)} missing coords, {len(approx)} approx/fallback.")
    if missing:
        print("missing:", missing)


if __name__ == "__main__":
    main()
