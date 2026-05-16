# Ukraine Occupied-Territory Caveat Plan

This note defines the source and treatment for Ukraine before any detailed Ukraine site profiles are drafted. It is a planning and caveat artefact only.

## Current Project Data

The current NuScale VOYGR-6 screening database contains 20 Ukrainian site records: 11 full-pass records, 6 exclusionary-pass records with avoidance flags, and 3 hard-fail records. This makes Ukraine analytically relevant in the regional screening results, but not automatically profile-ready under current war conditions.

The leading Ukrainian records in the current database include Zmiivska, Dobrotvir, Ladyzhyn, Kalush, Burshtyn, Starobesheve, Kryvorizka, Vuglegirska, Kurakhov, and Myronivskyi. These should not be converted into detailed site profiles until the occupied-territory comparison and security caveats are complete.

## Recommended Occupied-Territory Source

Use the Institute for the Study of War's assessed control-of-terrain map as the primary report source:

- Primary source: Institute for the Study of War, "Assessed Control of Terrain in Ukraine", https://understandingwar.org/map/assessed-control-of-terrain-in-ukraine/
- Reason for selection: regularly updated, timestamped, public, and suitable for a policy-facing report when used with date and attribution.
- Required attribution: title, publisher, map date/time, access date, and URL.

Use DeepStateMAP only as a supplemental cross-check or, if explicit permission and licensing are acceptable, as a geospatial data source:

- Supplemental source: DeepStateMAP, https://deepstatemap.live/en/
- Potential geodata route: a daily GeoJSON mirror such as `cyterat/deepstate-map-data`, subject to verification of licensing, date, provenance, and suitability for publication.
- Use constraint: do not rely on an unofficial mirror in the final report unless the source, licence, and date are documented.

## Figure Method

The Ukraine figure should be a comparison figure, not a recommendation map:

1. Generate the project Ukraine candidate-site map from the local `sites` and `composite_rankings` tables, using the same three status classes as the Romania prototype: full pass, exclusionary pass with avoidance flag, and hard fail.
2. Place it beside or beneath the current occupied-territory/control-of-terrain source map.
3. If a licensed polygon layer is available, compute a simple overlay count of Ukrainian full-pass and top-10 candidate sites that fall inside occupied or active-conflict areas.
4. If only a static image is used, state the comparison qualitatively and avoid claiming exact geospatial counts.

No external geodata download or live web fetch should be run as part of the report build without explicit approval at implementation time.

## Report Caveat Wording

Ukraine should be treated as analytically important but practically improbable for near-term progression under current war conditions. The report should say that several Ukrainian records perform well under desk-study scoring, but that conflict, occupation, security, infrastructure damage, regulator access, emergency planning, and data currency prevent detailed site progression in the current phase.

Recommended wording:

> Ukraine includes several high-performing screening records, but the current war context prevents these records from being treated as practical near-term progression candidates. The report therefore presents Ukraine only with explicit conflict and occupied-territory caveats. Detailed Ukrainian site profiles should be deferred until post-war review, updated territorial-control mapping, physical site access, regulator engagement, and infrastructure-condition evidence are available.

## Stop Rule

Do not draft detailed Ukraine site profiles in the first Chapter 5 pass. Include only the caveat section, the project candidate-site map, and the occupied-territory comparison after a defensible source and map date are selected.
