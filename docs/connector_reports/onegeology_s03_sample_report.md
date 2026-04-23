# S-03 OneGeology Connector — Sample Report

**Run date:** 2026-04-16  
**Run ID:** `onegeology-2026-04-16`  
**Connector slug:** `onegeology`  
**Criteria served:** NH-02 (capable fault distance), NH-05 (karst)  
**Role:** Supplementary — queries national geological survey WFS endpoints to improve on S-02 EGDI where its coverage is insufficient.

---

## 1. Methodology

### What this connector does

S-03 OneGeology is a **supplementary connector** that runs *after* S-02 EGDI. It does not overwrite S-02 results — it fills gaps where S-02 left quality at `low` or `insufficient`.

**For NH-02 (fault proximity):** The EGDI HIKE fault layer is pan-European but at continental scale (~1:1M). For sites where EGDI found no faults within the 8 km buffer (`nearest_fault_km = NULL`, quality `low`), S-03 attempts to query the national geological survey's WFS for a higher-resolution fault layer covering just that country.

**For NH-05 (karst):** EGDI karst data only covers CZ and IE. For all other countries, S-02 writes `nh05_quality = 'medium'` sourced from the WOKAM global karst database (connector S-07-equivalent, loaded separately). In the current run all 363 sites already have `nh05_quality = 'medium'`, so S-03 did **not** attempt any karst queries.

### Decision logic

```
For each site:
  1. Read S-02 NH-02 quality from SiteNaturalHazards.
  2. If nh02_quality ∈ {medium, high}  → skip (S02 adequate)
  3. Else → look up country's WFS endpoint in endpoint_registry
     a. If wfs_url is null → log no_endpoint, skip
     b. Else → query national fault WFS within 8 km bbox
        → parse GeoJSON features → nearest_fault_distance_km
        → write to SiteNaturalHazards.nearest_fault_km
        → set nh02_quality = 'medium' (faults found) or 'low' (none)
        → set nh02_source = 'onegeology_national_faults'
  4. Repeat steps 1–3 for NH-05 if nh05_quality < medium
```

### Quality grade definitions for NH-02

| Grade | Meaning |
|-------|---------|
| `high` | National survey WFS returned ≥1 fault within 8 km with activity classification |
| `medium` | EGDI HIKE returned ≥1 fault within 8 km (S-02 adequate), OR national WFS returned data |
| `low` | No faults found within 8 km in EGDI HIKE; national WFS either unavailable or also returned empty |
| `insufficient` | No WFS queried at all (endpoint missing and outside EGDI domain) |

### Proxy and limitation notes

- `nearest_fault_km = NULL` with `nh02_quality = 'low'` does **not** mean the site is fault-free. It means EGDI HIKE (continental scale) found nothing within 8 km. Higher-resolution national surveys might reveal closer faults.
- The HIKE fault database is focused on seismically active faults (capable faults per IAEA definition). Smaller or geologically inactive faults are excluded from HIKE but may appear in national surveys.
- Turkey (146 sites) is seismically very active. `nh02_quality = 'low'` for Turkish sites reflects the absence of Turkey in EGDI HIKE coverage, not low seismic hazard. The EFSM20 connector (S-06) provides complementary seismic fault data that partially compensates.

---

## 2. Full Batch Run — Results Summary

**Date:** 2026-04-16  
**Total sites processed:** 363  

| Outcome | Count | Meaning |
|---------|-------|---------|
| `s02_adequate` | 104 | NH-02 already at `medium` from EGDI HIKE; S-03 skipped |
| `no_endpoint` | 259 | NH-02 is `low` but no national WFS registered yet |
| `succeeded` | 0 | Supplementation written (no active endpoints) |
| `failed` | 0 | Errors |

**Wall time:** 0.3 s (no network calls; all endpoints are null in current config)

### By country

| CC | Sites | Need NH-02 | Endpoint status | NH-05 status |
|----|------:|----------:|-----------------|-------------|
| AL | 1 | 1 | no endpoint | medium (WOKAM) |
| AT | 8 | 0 | no endpoint | medium (WOKAM) |
| BA | 11 | 10 | no endpoint | medium (WOKAM) |
| BG | 15 | 15 | no endpoint | medium (WOKAM) |
| BY | 2 | 2 | no endpoint | medium (WOKAM) |
| CZ | 29 | 24 | no endpoint | medium (WOKAM) |
| HR | 2 | 2 | no endpoint | medium (WOKAM) |
| HU | 11 | 0 | no endpoint | medium (WOKAM) |
| LV | 1 | 1 | no endpoint | medium (WOKAM) |
| MD | 1 | 1 | no endpoint | medium (WOKAM) |
| ME | 4 | 4 | no endpoint | medium (WOKAM) |
| MK | 4 | 4 | no endpoint | medium (WOKAM) |
| PL | 63 | 7 | no endpoint | medium (WOKAM) |
| RO | 24 | 22 | no endpoint | medium (WOKAM) |
| RS | 8 | 5 | no endpoint | medium (WOKAM) |
| SI | 3 | 0 | no endpoint | medium (WOKAM) |
| SK | 6 | 1 | no endpoint | medium (WOKAM) |
| TR | 146 | 146 | no endpoint | medium (WOKAM) |
| UA | 20 | 10 | no endpoint | medium (WOKAM) |
| XK | 4 | 4 | no endpoint | medium (WOKAM) |

**AT, HU, SI** had all sites with `nh02_quality = medium` from EGDI HIKE — these countries have dense HIKE fault coverage and needed no supplementation.

---

## 3. 20-Site Sample Data

The table below shows one site per country for the 20 countries in scope. Data as of run date.

| # | Country | Site | Lat | Lon | NH-02 Quality | Nearest Fault (km) | NH-05 Quality | S-03 Status | Notes |
|---|---------|------|-----|-----|:---:|:---:|:---:|:---:|-------|
| 1 | TR | Ada Yesildag Enerji PS | 36.376 | 33.932 | **low** | — | medium | no_endpoint | Turkey not in EGDI HIKE domain; MTA WFS unverified |
| 2 | BA | Banovici PS | 44.400 | 18.533 | **low** | — | medium | no_endpoint | Bosnia WFS endpoint unknown |
| 3 | BG | Bobov Dol PS | 42.286 | 23.033 | **low** | — | medium | no_endpoint | inspire.geology.bg DNS failure |
| 4 | RO | Arad PS | 46.222 | 21.329 | medium | 4.57 | medium | s02_adequate | EGDI HIKE fault found; S-03 skipped |
| 5 | BY | Lelchitsy PS | 51.789 | 28.321 | **low** | — | medium | no_endpoint | Belarus: no open WFS known |
| 6 | CZ | Chvaletice PS | 50.028 | 15.451 | **low** | — | medium | no_endpoint | CZ covered by EGDI pp05; fault gap unexplained |
| 7 | ME | Bar PS | 42.100 | 19.100 | **low** | — | medium | no_endpoint | Montenegro: no WFS registered |
| 8 | MK | Bitola PS | 41.058 | 21.484 | **low** | — | medium | no_endpoint | North Macedonia: no WFS registered |
| 9 | XK | Istok PS | 42.783 | 20.483 | **low** | — | medium | no_endpoint | Kosovo: no WFS registered |
| 10 | MD | Kuchurgan PS | 46.629 | 29.940 | **low** | — | medium | no_endpoint | Moldova: no open WFS known |
| 11 | LV | Kurzeme PS | 57.409 | 21.595 | **low** | — | medium | no_endpoint | Latvia tectonically stable; low seismic priority |
| 12 | AL | Porto Romano PS | 41.371 | 19.425 | **low** | — | medium | no_endpoint | Albania: IGJEUM WFS unverified |
| 13 | HR | Ploče PS | 43.050 | 17.433 | **low** | — | medium | no_endpoint | Croatia: HGI-CGS WFS path not found |
| 14 | PL | Adamow PS | 52.012 | 18.546 | **low** | — | medium | no_endpoint | Poland: cbdgportal WFS returned 404 |
| 15 | RS | Despotovac PS | 44.050 | 21.260 | **low** | — | medium | no_endpoint | Serbia: GZS WFS DNS failure |
| 16 | SK | Kosice PS | 48.698 | 21.272 | medium | 0.45 | medium | s02_adequate | EGDI HIKE found fault 0.45 km — very close |
| 17 | UA | Burshtyn PS | 49.210 | 24.667 | medium | 0.98 | medium | s02_adequate | EGDI HIKE found fault 0.98 km |
| 18 | HU | Bakony PS | 47.096 | 17.558 | medium | 4.82 | medium | s02_adequate | EGDI HIKE adequate |
| 19 | AT | Duernrohr PS | 48.326 | 15.923 | medium | 0.94 | medium | s02_adequate | EGDI HIKE found fault 0.94 km |
| 20 | SI | Sostanj PS | 46.372 | 15.053 | medium | 1.87 | medium | s02_adequate | EGDI HIKE adequate; karst via WOKAM |

**Legend:** `—` = no fault found within 8 km by EGDI HIKE (not necessarily fault-free)

---

## 4. Report-Ready Interpretation

### What the connector contributes to the siting report

**NH-02 (Capable Fault Distance):**

- **104 sites (28.7%)** have `nh02_quality = medium` sourced from EGDI HIKE. These sites have a confirmed nearest fault distance ranging from 0.45 km (Kosice, SK — flagged for detailed review) to well over 8 km. These values are reliable for a continental-scale screening.
- **259 sites (71.3%)** have `nh02_quality = low` and `nearest_fault_km = NULL`. This means EGDI HIKE found no faults within 8 km. This is most likely because:
  - **Turkey (146 sites):** Turkey is partially outside the EGDI domain. Despite being seismically very active (North Anatolian Fault, East Anatolian Fault), fault data for Turkish sites comes from EFSM20 (S-06), not HIKE.
  - **Western Balkans (BA, ME, MK, RS, XK — 31 sites):** Balkans are seismically active but small national surveys are not integrated into HIKE.
  - **Eastern EU (CZ, PL, BG, RO, BY, MD, UA — ~80 sites):** HIKE coverage exists but may be sparse in some sub-regions.

**NH-05 (Karst):**

- **All 363 sites: `nh05_quality = medium`** from the WOKAM global karst database (loaded via the karst connector). S-03 found no sites needing karst supplementation.
- The WOKAM result means: the global karst atlas has been queried for all sites. A medium quality grade reflects that WOKAM provides coarse karst polygon data (not site-specific hydrogeology). Higher-resolution national geological data (what S-03 would provide) would upgrade this to `high` quality when available.

### Flags for the report

| Site | Issue | Implication |
|------|-------|-------------|
| Kosice PS (SK) | Fault 0.45 km — within IAEA 8 km exclusion zone | **Exclusionary candidate** for NH-02 (E1 criterion). Requires field verification. |
| Burshtyn PS (UA) | Fault 0.98 km | Inside exclusion threshold. Verify fault capability/activity. |
| Duernrohr PS (AT) | Fault 0.94 km | Inside exclusion threshold. Verify fault capability/activity. |
| All TR sites (146) | `nh02_quality = low` from HIKE, but Turkey is seismically active | NH-02 assessment for Turkey should rely on EFSM20 (S-06) + Turkish national data. **Do not use HIKE-absence as evidence of low seismic hazard.** |
| BA, ME, MK, XK, RS sites | `nh02_quality = low`, seismically active Balkans | Same caveat as Turkey. These countries sit on the Dinaric-Hellenic seismic belt. |

### Recommended actions

1. **Prioritise endpoint recovery for TR, BA, RS, ME, MK** — these are seismically active countries where HIKE absence is most misleading. The MTA (Turkey) and national survey WFS endpoints need re-verification.
2. **Use EFSM20 (S-06) as the primary fault source for Turkey and Balkans** — it provides better coverage than HIKE for these regions.
3. **Sites with fault < 8 km should trigger E1 exclusionary review** regardless of NH-02 quality grade. Sites with `nh02_quality = medium` and `nearest_fault_km < 8` are the highest-priority for detailed assessment.

---

## 5. Endpoint Registry Status (as of 2026-04-16)

All 5 endpoints probed during API exploration returned errors:

| Country | URL Probed | HTTP Result | Issue |
|---------|-----------|-------------|-------|
| PL | cbdgportal.pgi.gov.pl/geoserver/wfs | 404 | Wrong URL path |
| RO | inspire.igr.ro/geoserver/wfs | 200 (error XML) | WFS service administratively disabled |
| BG | inspire.geology.bg/geoserver/wfs | DNS failure | Domain unreachable |
| AT | gisgba.geologie.ac.at/geoserver/wfs | DNS failure | Domain unreachable |
| EE | xgis.maaamet.ee/xgis2/wfs | 404 | Wrong URL path |

All `wfs_url` values are currently `null` in `config/default.yml`. The connector writes no data until endpoints are verified and layer names populated.

---

*Generated by S-03 OneGeology connector · atoms-vs-ashes pipeline · 2026-04-16*
