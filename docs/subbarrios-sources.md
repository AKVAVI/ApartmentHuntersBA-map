# Sub-barrios: sources, methodology, and known uncertainties

This documents `data/subbarrios.geojson` — informal subdivisions of the
official Palermo and Belgrano barrios. Nothing here is an official city
boundary; see the per-feature `boundary_type`/`confidence` fields and the
notes below before treating any of this as authoritative.

## Why these exist at all

The City of Buenos Aires's open-data boundaries dataset (`data/barrios.geojson`)
only has 48 official barrios — "Palermo" and "Belgrano" are each a single
polygon. "Palermo Soho", "Belgrano R", "Las Cañitas" etc. are real-estate/
colloquial names with no administrative boundary. The city's own tourism
site confirms this directly (turismo.buenosaires.gob.ar, "La creatividad
porteña en los infinitos 'Palermos'") — it discusses the names as cultural
trivia and gives no street boundaries for any of them.

## Two tiers of boundary_type

### `official_aph_hull` (confidence: high)

Two of the ten requested areas coincide with a real, legally-protected
**APH** (*Área de Protección Histórica*) zone under the city's Código
Urbanístico:

- **Palermo Chico** → APH3, "Ámbito Gran Bourg y Palermo Chico" (Ley 536/2000)
- **Belgrano R** → APH4, "Entorno Estación Belgrano R"

The city publishes a GeoJSON of every individually cataloged building/parcel
("Áreas de Protección Histórica" dataset, data.buenosaires.gob.ar), each
tagged with which APH it falls in — but **not** a single polygon per APH
zone. The exact legal boundary only exists as a plan annex to the Código
Urbanístico, published as a PDF, not open geodata.

**Methodology:** took every parcel tagged APH3 (442 parcels) / APH4 (50
parcels) in that dataset and computed the convex hull of their footprints
(`scripts/extract_aph_hulls.py`). This is a derived approximation — real,
grounded in official per-building data, but a convex hull can be a slight
over-approximation if the true zone isn't convex. It is **not** the exact
line from the Código's plan annex.

**Caveat:** APH4 only covers the few blocks immediately around Belgrano R
train station — smaller than the colloquial real-estate "Belgrano R"
neighborhood, which real-estate sites describe as covering a wider area.
APH3 lines up reasonably well with the colloquial "Palermo Chico" (both
centered on the Thays-designed barrio-parque near MALBA/Av. Figueroa
Alcorta).

### `informal` (confidence: low)

The other seven have no official geometry at all, anywhere. For each,
I collected the boundary streets a source names, pulled those streets'
real line geometry from OpenStreetMap (Overpass API), kept only the
points within ~0.8–1.3km of the sub-barrio's own centroid (computed from
this project's already-geocoded listings where any exist), and took the
convex hull of the pooled points (`scripts/geocode_subbarrios.py`). This
hugs the named streets without depending on exact street×street
intersections — most of these avenues don't literally cross near the area,
or OSM splits them into dozens of short way segments.

| Sub-barrio | Boundary streets (as sourced) | Source | Conflicts / notes |
|---|---|---|---|
| Palermo Soho | Av. Scalabrini Ortiz, Av. Córdoba, Av. Juan B. Justo, Av. Santa Fe | Billiken ("al sur de Juan B. Justo"); Mudafy (full quad) | Billiken gives only one side; quad completed from Mudafy |
| Palermo Hollywood | Av. Juan B. Justo, Av. Córdoba, Av. Dorrego, Av. Santa Fe | Billiken ("al norte de Juan B. Justo") + a second real-estate guide | same as above |
| Palermo Viejo | Av. Córdoba, Av. Santa Fe, Av. Dorrego, Av. Scalabrini Ortiz | Billiken | **English Wikipedia gives a different box** (Coronel Díaz/Córdoba/Scalabrini Ortiz/Güemes) for the same name. Billiken's definition was used per explicit decision (2026-11-05) |
| Palermo Nuevo | Av. Santa Fe, Sarmiento, Av. del Libertador, ex-FFCC San Martín | Billiken | Fodor's describes a *different* "Palermo Nuevo" next to Palermo Botánico — name is used for two different areas depending on source |
| Las Cañitas | Av. Luis María Campos, Matienzo, Av. del Libertador, Av. Dorrego | Billiken | — |
| Belgrano C | Av. Cabildo, Olazábal, Congreso, Conesa | A market report's "Av. Cabildo, Olazábal, Congreso, Conesa" zone (not explicitly labeled "Belgrano C"); Roomix only gives qualitative description | **Weakest-sourced polygon in this set** — treat with particular caution |
| Bajo Belgrano | Av. Cabildo, Av. del Libertador, Av. Monroe, Av. Leopoldo Lugones | wander-argentina.com tourist guide | Source's own wording is internally inconsistent (names "Av. del Libertador" as both a south and a west boundary); only Av. del Libertador had OSM points within radius for the final hull, so this one is closer to a line buffer than a real quadrilateral |

## Excluded from this version

**Palermo Botánico** and **Barrio River** were researched and explicitly
excluded (decision 2026-11-05): no source gives any street boundary for
either, even approximately — Palermo Botánico is only ever described as
"around the Jardín Botánico", and sources can't even agree whether Barrio
River belongs to Belgrano or Núñez. Properties that fall in these areas
get no `sub_barrio` value rather than a guessed one.

## Reproducing / extending this

1. `scripts/extract_aph_hulls.py` — convex hulls for any further APH zone
   (point it at a fresh copy of the APH GeoJSON; the source file is ~250MB
   and is not committed).
2. `scripts/geocode_subbarrios.py` — add a new entry to `SUBBARRIOS_INFORMAL`
   with its boundary streets (OSM-exact names), a center (ideally the
   centroid of real listings already in that area), and a radius.
3. `scripts/build_subbarrios_geojson.py` — assembles the final
   `data/subbarrios.geojson`, embedding `source`/`methodology`/`confidence`
   per feature.
4. `scripts/classify_subbarrios.py` — re-run after any boundary change to
   refresh `sub_barrio` / `sub_barrio_boundary_version` on `data/objects.json`.

Each polygon's `version` field is `"1.0"` — bump it (and `sub_barrio_boundary_version`
on reclassified objects) whenever a polygon is redrawn, so old classifications
are never silently confused with new ones.
