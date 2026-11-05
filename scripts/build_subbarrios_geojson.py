#!/usr/bin/env python3
"""Assemble data/subbarrios.geojson from:
 - the APH3/APH4 convex hulls (hand-pasted below, produced by extract_aph_hulls.py)
 - data/subbarrios_informal_raw.json (produced by geocode_subbarrios.py)

Each feature carries the methodology/source/confidence fields the user's
spec asked for. See docs/subbarrios-sources.md for the full writeup.
"""
import json

VERSION = "1.0"

APH_HULLS = {
    "palermo_chico": [[-58.410897634969665, -34.58517185729061], [-58.41082256140543, -34.58522491029328], [-58.397828591778385, -34.58148522834687], [-58.39604477679406, -34.57892822563964], [-58.3979436017029, -34.577575388631296], [-58.40216661245149, -34.57483155505137], [-58.4024378199271, -34.575126743961555], [-58.403003381765856, -34.5757423183599], [-58.410897634969665, -34.58517185729061]],
    "belgrano_r": [[-58.465370724339486, -34.568073451037066], [-58.465077291191676, -34.568418334132076], [-58.46505193479721, -34.56844767607732], [-58.46495619708492, -34.56855844525252], [-58.4649492886172, -34.56856643202448], [-58.46491170609072, -34.56860976431368], [-58.46489733340638, -34.568626332803944], [-58.464113355851595, -34.568982128662576], [-58.462262002442884, -34.569417453208196], [-58.461406661411324, -34.56915259886565], [-58.46047467057925, -34.56868865696836], [-58.46036990879983, -34.568620146551936], [-58.46102362973591, -34.56753579442785], [-58.46108685461699, -34.5674632754535], [-58.46181525965914, -34.56687488521851], [-58.46523695944328, -34.56718155469672], [-58.46524412966624, -34.56718585435593], [-58.465370724339486, -34.568073451037066]],
}

OFFICIAL_FEATURES = [
    {
        "id": "palermo_chico", "name": "Palermo Chico", "parent_barrio": "Palermo",
        "boundary_type": "official_aph_hull",
        "source": "GCBA, dataset \"Áreas de Protección Histórica\" (data.buenosaires.gob.ar/dataset/areas-proteccion-historica), APH3 \"Ámbito Gran Bourg y Palermo Chico\" (Ley 536/2000, vigente en el Código Urbanístico, Ley 6099)",
        "methodology": "Convex hull of the 442 cataloged parcels tagged APH3 in the official per-parcel GeoJSON. This is a derived approximation of the legally protected area, not the exact polygon from the Código Urbanístico's plan annex (published only as a PDF plan, not open geodata).",
        "confidence": "high",
    },
    {
        "id": "belgrano_r", "name": "Belgrano R", "parent_barrio": "Belgrano",
        "boundary_type": "official_aph_hull",
        "source": "GCBA, dataset \"Áreas de Protección Histórica\", APH4 \"Entorno Estación Belgrano R\"",
        "methodology": "Convex hull of the 50 cataloged parcels tagged APH4 in the official per-parcel GeoJSON. Same caveat as Palermo Chico: a derived approximation, not the exact legal polygon. Note this APH covers only the area immediately around Belgrano R train station, which is smaller than the colloquial real-estate \"Belgrano R\" neighborhood.",
        "confidence": "high",
    },
]

INFORMAL_SOURCE_NOTES = {
    "palermo_soho": "Billiken (\"¿Sabías que hay diecinueve sub-barrios no oficiales dentro de Palermo?\", billiken.lat): \"queda al sur de la Avenida Juan B. Justo\"; cross-checked against Mudafy.com.ar, which bounds it by Av. Scalabrini Ortiz, Av. Córdoba, Av. Juan B. Justo and Av. Santa Fe.",
    "palermo_hollywood": "Billiken: \"queda al norte de la Avenida Juan B. Justo\"; cross-checked against a second real-estate guide bounding it by Av. Juan B. Justo, Av. Córdoba/Costa Rica/Honduras, Av. Dorrego and Av. Santa Fe.",
    "palermo_viejo": "Billiken: \"entre las avenidas Córdoba y Santa Fe, desde Dorrego hasta Scalabrini Ortiz.\" NOTE: English Wikipedia gives a different, non-overlapping box (Coronel Díaz / Córdoba / Scalabrini Ortiz / Güemes) for the same name — per user decision, the Billiken definition was used.",
    "palermo_nuevo": "Billiken: \"ubicado entre las calles Santa Fe, Sarmiento, Del Libertador y el ex-ferrocarril San Martín.\"",
    "las_canitas": "Billiken: \"entre la avenida Luis María Campos, Matienzo, Del Libertador y Dorrego.\"",
    "belgrano_c": "Roomix.ai neighborhood guide (qualitative only: \"torres de departamentos sobre Avenida Cabildo y la Plaza Manuel Belgrano\") combined with a real-estate market report bounding a Belgrano commercial zone by Av. Cabildo, Olazábal, Congreso and Conesa. Weakest-sourced polygon in this set.",
    "bajo_belgrano": "wander-argentina.com tourist guide: \"bounded by Avenida Cabildo to the north, Río de la Plata to the east, Avenida del Libertador to the south, and Avenida Libertador General San Martín to the west\" (also calls it \"Belgrano Chico\"). Internally a little inconsistent (two Libertador references) — used Av. Cabildo, Av. del Libertador, Av. Monroe and Av. Leopoldo Lugones as the four nearest named streets.",
}

METHOD_INFORMAL = (
    "No official boundary exists for this name. Polygon built by pulling the real OpenStreetMap "
    "line geometry of each boundary street named by the source, keeping only the points within "
    "~1-1.4km of this sub-barrio's own listings' centroid (or a manual estimate where no listings "
    "exist yet), and taking the convex hull of the pooled points. This hugs the named streets "
    "without depending on exact street-to-street intersections (most of these avenues don't "
    "literally cross near the area, or OSM splits them into many short way segments)."
)


def main():
    informal_raw = json.load(open("data/subbarrios_informal_raw.json"))
    features = []

    for f in OFFICIAL_FEATURES:
        ring = APH_HULLS[f["id"]]
        features.append({
            "type": "Feature",
            "properties": {**{k: v for k, v in f.items() if k != "parent_barrio" or True}, "version": VERSION},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })

    for sb_id, data in informal_raw.items():
        if not data.get("ring"):
            print(f"SKIP {sb_id}: no ring")
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "id": sb_id,
                "name": data["name"],
                "parent_barrio": data["parent_barrio"],
                "boundary_type": "informal",
                "source": INFORMAL_SOURCE_NOTES.get(sb_id, ""),
                "methodology": METHOD_INFORMAL,
                "boundary_streets": data["streets"],
                "confidence": "low",
                "version": VERSION,
            },
            "geometry": {"type": "Polygon", "coordinates": [data["ring"]]},
        })

    fc = {"type": "FeatureCollection", "features": features}
    json.dump(fc, open("data/subbarrios.geojson", "w"), ensure_ascii=False, indent=2)
    print(f"wrote {len(features)} features to data/subbarrios.geojson")


if __name__ == "__main__":
    main()
