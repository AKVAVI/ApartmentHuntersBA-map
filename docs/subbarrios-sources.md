# Sub-barrios: sources, methodology, and known uncertainties

**v2 (2026-11-06).** Scope cut to four Palermo sub-neighborhoods — Palermo
Chico, Palermo Soho, Palermo Hollywood, Las Cañitas — per explicit decision.
All Belgrano sub-barrios (Belgrano R, Belgrano C, Bajo Belgrano) from v1 were
removed: the layer, its filter options, and each object's classification.
The official Belgrano **barrio** boundary and its listings are untouched —
only the extra sub-barrio layer for it is gone, to be revisited later.

The v1 approach (convex hull of OSM points pooled within a radius of this
project's own listings) was also replaced. It had two real problems: the
polygon depended on where *our* listings happened to be rather than on the
neighborhood's actual geography, and independently-hulled zones could
overlap, which v1's classifier then "resolved" by picking whichever
polygon was smallest — silently making up an answer instead of reporting
the conflict. v2 builds each zone from the real intersections of its named
boundary streets (`scripts/build_subbarrios_v2.py`), and the classifier
(`scripts/classify_subbarrios.py`) stops and reports it if a point ever
matches more than one zone, instead of guessing.

## What's here

`data/subbarrios.geojson` — four polygons, one per zone, each with:
`id`, `name`, `parent_barrio` ("Palermo" for all four right now),
`boundary_type`, `source`, `methodology`, `boundary_streets`, `confidence`,
`version`. None of these are official city boundaries — see confidence
per zone below.

## Per-zone sources and construction

### Palermo Chico — `boundary_type: informal_google`, confidence: medium

Unlike the other three, Google Maps draws an actual neighborhood polygon
for "Palermo Chico" (confirmed by viewing it directly, 2026-11-06) — it is
registered there as a distinct place, not just a text label. This project
has no rights to redistribute Google's own polygon data, so instead its
four sides were read off the map and rebuilt from real street/rail
geometry:

- **West:** Av. Casares
- **North:** the FC San Martín railway embankment (not a street)
- **South:** Av. del Libertador
- **East:** Austria

Three corners are real street×street or street×rail intersections (Av.
Casares × FC San Martín rail for NW, Av. Casares × Av. del Libertador for
SW, Austria × Av. del Libertador for SE). Austria turns out **not** to
reach the railway anywhere near here — their actual crossing is several
blocks south, near Canal Siete — so forcing that "intersection" produced a
self-intersecting (bowtie) shape on the first attempt. The NE corner is
instead Austria's own northernmost mapped point (a real OSM coordinate,
not invented), standing in for where the boundary plausibly cuts across
between the railway and Austria's end. Verified: 4 vertices, no
self-intersection, ~0.75 km².

Earlier (v1) sources described a different, conflicting definition for
"Palermo Chico" (Billiken/Wikipedia: bounded by Av. del Libertador, Cavia
and Tagle, with Av. Figueroa Alcorta running through the middle) — kept
here as a documented alternative, not used, since the empirical Google
boundary was judged more reliable once it was confirmed to exist.
APH3 ("Ámbito Gran Bourg y Palermo Chico," the legally protected heritage
zone of the same name) is smaller and sits inside roughly the same area,
but is a different, narrower legal concept — not reused here.

### Palermo Soho — `boundary_type: informal`, confidence: low

**Source:** Mudafy.com.ar / roomix.ai: "entre las avenidas Scalabrini
Ortiz, Córdoba, Juan B. Justo y Santa Fe." No official boundary exists;
Google Maps shows no polygon for it either (only a "shopping district"
highlight around Plaza Serrano, which is a density overlay, not a
neighborhood outline).

**Construction:** a real quadrilateral from the actual intersections of
these four avenues. Av. Santa Fe and Av. Córdoba run roughly parallel
(the two long sides); Av. Juan B. Justo and Av. Scalabrini Ortiz are the
cross sides. Verified: 4 vertices, no self-intersection, ~1.77 km².

### Palermo Hollywood — `boundary_type: informal`, confidence: low

**Source:** roomix.ai / Billiken: "entre Juan B. Justo, Córdoba, Dorrego y
Santa Fe." Same caveats as Soho — no official or Google-drawn boundary.

**Construction:** real quadrilateral; Av. Santa Fe and Av. Córdoba are the
long sides, Av. Juan B. Justo and Av. Dorrego the cross sides. **Av. Juan
B. Justo is the shared edge with Palermo Soho** (Soho to its south,
Hollywood to its north) — consistently stated across sources, and the
reason the two zones come out adjacent rather than overlapping: verified,
zero edge-crossings between the two polygons. Verified: 4 vertices, no
self-intersection, ~1.19 km².

### Las Cañitas — `boundary_type: informal`, confidence: low

**Source:** roomix.ai: "delimitado por las avenidas Luis María Campos,
Dorrego y Del Libertador y la calle Matienzo" (full OSM name: "Teniente
Benjamín Matienzo" — "Matienzo" alone matched only one unrelated 7-point
stub). An expat guide gives a conflicting cross street ("Ortega y Gasset"
instead of Matienzo) — not used; Matienzo is the more frequently cited one.

**Construction:** real quadrilateral; Av. del Libertador and Av. Luis
María Campos are the long sides, Matienzo and Av. Dorrego the cross sides.
Verified: 4 vertices, no self-intersection, ~0.47 km².

## Validation performed

For all four zones, before classifying anything (script output
reproducible by re-running `build_subbarrios_v2.py`):
- Each ring has no self-intersecting edges (checked every non-adjacent
  edge pair for a crossing).
- Every pair of the four zones has **zero** edge-crossings — they don't
  overlap, by construction (shared streets as edges, not independently
  fit shapes).
- Each zone's area is within a plausible neighborhood scale (0.47–1.77 km²).

## Classification

`scripts/classify_subbarrios.py` does point-in-polygon against each
object's existing `lat`/`lng` — never assigned by hand, never by
proximity/area heuristics. An object outside all four zones gets
`sub_barrio: ""` (left unassigned, not guessed). Since the zones don't
overlap, a point matching more than one would mean the polygons
themselves are broken — the script treats that as an error to report and
fix, not something to silently resolve.

Current result: 23/66 objects matched (Palermo Hollywood 10, Palermo Soho
8, Las Cañitas 3, Palermo Chico 2); 0 ambiguous.

## Reproducing / extending this

1. `scripts/build_subbarrios_v2.py` — edit the `ZONES` list to adjust a
   zone's boundary streets, or add a new one (give it 4 streets arranged
   as two parallel "long" sides and two parallel "cross" sides, so each
   adjacent pair has a real intersection — not 4 arbitrary streets, which
   can fail to close into a simple quadrilateral, as Palermo Chico did on
   the first attempt).
2. `scripts/classify_subbarrios.py` — re-run after any boundary change.
3. Bump the zone's `version` field when its geometry changes, so old
   classifications are never confused with new ones.

## Still out of scope

- **Belgrano sub-barrios** (Belgrano R, Belgrano C, Bajo Belgrano) — removed
  in v2 per decision 2026-11-06; may return later with the same rigor.
- **Palermo Viejo, Palermo Nuevo, Palermo Botánico, Barrio River** — were in
  v1's scope and researched there (see git history), not carried into v2
  because the scope was explicitly cut to four zones.
