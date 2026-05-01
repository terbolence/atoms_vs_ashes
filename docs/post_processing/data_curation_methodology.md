# Post-Processing Data Curation — Methodology

> Algorithms, parameters, and exclusion rules used by the
> `scripts/run_curation0[1-5]_*.py` backfill scripts.
> Each section corresponds to one curation task in the
> `post-processing curation step 1` plan.

Last updated: 2026-04-20.

---

## Task 1 — Cooling source river names

**Goal:** replace the synthetic `HYRIV-{id}` placeholders in
`site_infrastructure_v2.cooling_source_name` with real river names where
possible, while always preserving the HydroRIVERS reach id in a separate
column.

**Source columns:**

| Column | Role |
|--------|------|
| `cooling_source_name` | display name; today often `HYRIV-NNNNNNNN` |
| `cooling_source_hyriv_id` (new) | numeric reach id, never lost |

**Algorithm:**

1. Select all rows where `cooling_source_name LIKE 'HYRIV-%'`.
2. Parse the trailing integer; persist it to `cooling_source_hyriv_id`.
3. Query Overpass at the site's coordinates for nearby named waterways:
   - Radius ladder: 500 m, 1 km, 2 km (stop at first hit).
   - Filter: `way["waterway"~"river|canal|stream"]["name"]`.
   - Preference order: `waterway=river` first, then `canal`, then `stream`.
4. If a name is found:
   - Update `cooling_source_name` to the OSM `name` tag (or `name:en` when
     present and the local name is in non-Latin script).
   - Track `before` and `after` for the audit report.
5. If no name is found:
   - Leave `cooling_source_name` unchanged. Coverage never decreases.

**Why Overpass (not the HydroRIVERS shapefile alone):** HydroRIVERS' own
`RIVER_NAME` attribute is missing for most European reaches, so re-reading the
shape would not help. OSM has dense, vetted river name coverage in Europe.

**Forward fix:** the HydroRIVERS connector now writes
`cooling_source_hyriv_id` on every successful match, regardless of whether
`RIVER_NAME` was present.

**Output report:**
`audit/post_processing/02_data_verification/2_5_targeted_checks/20260420_2_5_3_cooling_river_names.md`

---

## Task 2 — NS-04 favourable area (hectares)

**Goal:** add a numeric `favourable_area_ha` next to the existing
`favourable_land_pct`, derived from data already on the row, and flag rows
where the value is implausibly small for the plant footprint.

**Inputs (per row):**

| Source | Field | Notes |
|--------|-------|------|
| `site_infrastructure_v2.ns04_comment` | text built by `build_ns04_comment` | semi-colon-separated; CORINE / WorldCover comments contain the buildable line |
| `site_infrastructure_v2.favourable_land_pct` | 0–100 | percentage of the analysis disk classified favourable |
| `sites.site_area_ha` | hectares | declared / OSM plant footprint |

**Comment regexes (Unicode dash tolerated):**

```
buildable_re = r"Buildable\s*\([^)]+,\s*0\s*[\u2013\-]\s*1\s*km\):\s*([0-9]+(?:\.[0-9]+)?)\s*ha"
fav_pct_re   = r"Suitability:\s*([0-9]+(?:\.[0-9]+)?)\s*%\s*fav"
```

**Algorithm and methods (stored in `favourable_area_method`):**

1. **`comment_buildable_x_fav_pct`** — preferred path.
   - Parse `Buildable (..., 0–1 km): B ha` and `Suitability: F% fav` from
     `ns04_comment`.
   - `favourable_area_ha = round(B × F / 100, 2)`.
   - Justification: the `Buildable` figure already excludes water,
     built-up, infrastructure, and obvious no-go pixels within a 1 km buffer.
     Multiplying by the favourable land percentage further restricts to
     pixels classified as land-use-favourable for siting.
2. **`buffer_x_pct`** — fallback when only `favourable_land_pct` is available
   (e.g. Copernicus DEM has rewritten `ns04_comment` to terrain-only text).
   - Analysis disk = π × (1 km)² × 100 ha/km² ≈ 314.159 ha.
   - `favourable_area_ha = round(314.159 × favourable_land_pct / 100, 2)`.
3. **`pct_x_site_area`** — secondary fallback when neither comment nor
   `favourable_land_pct` is available, but `dominant_class_pct` is.
   - Treated as low-confidence; recorded with method = `pct_x_site_area` only
     when `sites.site_area_ha` is set and `favourable_land_pct` is also set.
   - `favourable_area_ha = round(site_area_ha × favourable_land_pct / 100, 2)`.
4. **`none`** — leave NULL when none of the above applies.

**Sanity flag rule (review queue, NOT auto-fix):**

A row is flagged when **all** of the following hold:

- `favourable_area_ha` is computed (not NULL),
- `favourable_area_ha < 1.0` ha,
- `sites.site_area_ha > 50` ha (i.e. the plant itself is large).

Each flagged row gets a hypothesised cause based on `dominant_land_class`
and the comment shape:

| Hypothesis | Trigger |
|-----------|---------|
| `dominant_water` | `dominant_land_class` matches water classes (`5xx`, `WaterBodies`, etc.) |
| `dem_overwrote_landcover_comment` | `ns04_comment` has no `Buildable` / `Suitability` lines but `favourable_land_pct` is set |
| `mid_river_or_offshore` | `dominant_land_class` matches `5xx` AND `dominant_class_pct > 80` |
| `unknown` | none of the above match |

**Forward fix:** CORINE and WorldCover writers compute `favourable_area_ha`
and `favourable_area_method` directly when they build the comment; the
backfill is therefore only needed once.

**Merged DB site-area resolution:** after API and LLM promotion, run
`src/scripts/resolve_site_area_merged.py` to set the merged `sites.site_area_ha`
from the best available signal: LLM footprint >10 ha, then API footprint >10 ha,
then `favourable_area_ha` >10 ha. If every signal is below 1 ha, the script
clears the merged area and records "area could not be identified".

**Output report:**
`audit/post_processing/02_data_verification/2_5_targeted_checks/20260420_2_5_1_favourable_area_review.md`

---

## Task 3 — NH-03 quality vs source split, "low" disambiguation

**Goal:** stop overloading `nh03_quality` with provenance tags
(`zhu_global_1km`, `egdi_*`, …). Move provenance to `nh03_source` and use
`nh03_quality` strictly as an evidence-confidence enum.

**Vocabulary contract (after backfill):**

| Column | Meaning | Allowed values |
|--------|--------|----------------|
| `liquefaction_suscept` | hazard class from the source raster | `very_low`, `low`, `moderate`, `high`, `very_high` |
| `nh03_quality` | confidence in our derived value | `high`, `medium`, `low`, `no_data` |
| `nh03_source` (new) | which dataset produced the row | `zhu_global_1km`, `egdi_lithology`, `soilgrids`, `combined` |
| `nh03_comment` | audit trace (raw raster value, lookup details) | free text |

**Backfill rules:**

For every existing row, the backfill walks the `nh03_quality` and
`nh03_comment` columns and decides:

1. If `nh03_quality` is one of the known source tags
   (`zhu_global_1km`, `egdi_lithology`, `soilgrids`, etc.):
   - Copy the tag to `nh03_source`.
   - Recompute `nh03_quality` from row state:
     - Zhu, raw raster value 1–5 with class set → `medium`.
     - Zhu, raw raster value 0 / unmapped → `no_data`.
     - EGDI with mapped lithology class → `medium`.
     - EGDI without mapped lithology class → `low`.
     - SoilGrids contribution alone (no Zhu, no EGDI evidence) → `low`.
2. If `nh03_quality` is already `high|medium|low|no_data`:
   - Leave the value as-is.
   - Try to infer `nh03_source` from `nh03_comment` (`Source: Zhu …` →
     `zhu_global_1km`, etc.); leave NULL if undecidable.

**Why "low" was confusing:**

Before this task, three different things could appear as the literal string
`low`:

- `liquefaction_suscept = 'low'` — the **hazard class** (raster value 2 in
  Zhu).
- `nh03_quality = 'low'` written by EGDI when lithology was missing — meant
  **low evidence quality**.
- An informal reading of the comment line `Raw raster value: 2; Class: low;
  …`.

After the split, only the second occurrence remains, and it lives next to a
non-overlapping `nh03_source` value, so the meaning is unambiguous.

**Forward fix:** Zhu, EGDI and SoilGrids batch writers now set
`nh03_source` separately and constrain `nh03_quality` to the four allowed
values.

---

## Task 4 — Bearing capacity sanity check

**Goal:** confirm `bearing_capacity_kpa` values are within the expected
Terzaghi-style range and not affected by a unit (kPa vs Pa) bug.

**Source:** `connectors/soilgrids/models.py::estimate_bearing_capacity`,
which uses a USDA-class-keyed table (`BEARING_CAPACITY_TABLE`, base 50–200
kPa) scaled by bulk density / 1.5 and clamped to ×0.6–×1.5.

**Audit (read-only):**

For every row with `bearing_capacity_kpa IS NOT NULL`, the script computes:

- min / max / median of `bearing_capacity_kpa` per `soil_type` bucket;
- count of rows with value `< 30 kPa` (below any plausible lower bound);
- count of rows with value `> 250 kPa` (above table maximum × clamp);
- count of rows with non-NULL value but NULL `soil_type` (orphan);
- 5 anchor sites cross-checked manually against published tables.

**Decision gate:** the methodology entry below is updated based on the
audit's outcome. If everything is in band, no code change is shipped; the
report explains the apparent low values (clay-dominated textures yield
30–90 kPa, which is consistent with the table). If outliers exist, a
follow-up curation issue is opened.

**Output report:**
`audit/post_processing/02_data_verification/2_5_targeted_checks/20260420_2_5_5_bearing_capacity_audit.md`

---

## Task 5 — NH-11 annual precipitation column

**Goal:** expose the annual precipitation total directly on the row.

`extreme_precip_mm` is **max-daily** and stays untouched. The new
`mean_annual_precip_mm` column holds the climatological annual total
(mm/year) that ERA5 already computes but only stores inside `nh11_comment`.

**Comment format produced by `copernicus_era5/batch.py`:**

```
ERA5 precipitation (ref 1991-2020) | annual=623mm | max_daily=42.1mm | snow_days=… | snow_months=… | SPI12_min=… | DSI=… | freezing_days=… | source=copernicus_era5
```

**Backfill regex:**

```
annual_re = r"annual=(\d+)mm"
```

**Backfill rule:** for every row with `mean_annual_precip_mm IS NULL` and
`nh11_comment IS NOT NULL`, run the regex; on a match, write the integer
value (mm/year) into `mean_annual_precip_mm`.

**Plausibility flag:** the backfill warns (does not fail) on values
< 100 mm/year or > 5000 mm/year.

**Forward fix:** the ERA5 batch writer now sets
`mean_annual_precip_mm = precip.mean_annual_precip_mm` next to the comment
build, so future runs do not depend on the regex.

NOAA-only rows do not include the annual figure; their
`mean_annual_precip_mm` stays NULL.

---

## Common conventions

- All curation scripts use SQLAlchemy via `Settings().database.url` and
  commit per row.
- All updates are **merge-only**: a non-NULL column is never overwritten
  with NULL. Same pattern as the OSM transport persistence guard.
- Each script supports `--dry-run` (no writes) and `--limit N` (cap
  processed rows for spot-checking).
- Each script writes its review report under
  `audit/post_processing/02_data_verification/2_5_targeted_checks/` with a
  `YYYYMMDD_2_5_<n>_<slug>.md` filename.
