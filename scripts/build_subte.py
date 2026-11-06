#!/usr/bin/env python3
"""Merge the official SBASE subte line/station GeoJSON (downloaded from
data.buenosaires.gob.ar, dataset "subte-estaciones") into one
data/subte.geojson the map can load as a single toggleable layer.

Source files (not committed, re-downloadable from the dataset page):
  data/subte_lineas.geojson     — LineString segments, properties.nombre = "Linea X"
  data/subte_estaciones.geojson — Point stations, properties.linea = "X", properties.estacion = name
"""
import json

LINE_COLORS = {
    "A": "#00A9E0",
    "B": "#E4002B",
    "C": "#0033A0",
    "D": "#00A650",
    "E": "#92278F",
    "H": "#FFC20E",
}


def line_letter(nombre):
    return nombre.replace("Linea ", "").strip()


def main():
    lines = json.load(open("data/subte_lineas.geojson"))
    stations = json.load(open("data/subte_estaciones.geojson"))

    features = []
    for f in lines["features"]:
        letter = line_letter(f["properties"]["nombre"])
        features.append({
            "type": "Feature",
            "properties": {"kind": "line", "linea": letter, "color": LINE_COLORS.get(letter, "#888")},
            "geometry": f["geometry"],
        })
    for f in stations["features"]:
        letter = f["properties"]["linea"]
        features.append({
            "type": "Feature",
            "properties": {
                "kind": "station",
                "linea": letter,
                "color": LINE_COLORS.get(letter, "#888"),
                "name": f["properties"]["estacion"],
            },
            "geometry": f["geometry"],
        })

    fc = {"type": "FeatureCollection", "features": features}
    json.dump(fc, open("data/subte.geojson", "w"), ensure_ascii=False, indent=2)
    print(f"wrote {len(features)} features ({len(lines['features'])} line segments, {len(stations['features'])} stations) to data/subte.geojson")


if __name__ == "__main__":
    main()
