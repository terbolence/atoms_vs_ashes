# NS-01 — cooling source river names

_Generated 2026-04-20 19:00 UTC by `scripts/run_curation01_cooling_river_names.py` (phase=id)._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 1.

## Phase 1 — `cooling_source_hyriv_id` backfill

- Rows updated this run: **363**
- Rows already populated: **0**

| Country | Site | hyriv id |
|---|---|---:|
| AL | Porto Romano Power Station | 20581859 |
| AT | Duernrohr power station | 20416147 |
| AT | Enns Power Station | 20419131 |
| AT | Mellach power station | 20457204 |
| AT | Riedersbach power station | 20425304 |
| AT | St Andrae power station | 20461305 |
| AT | Timelkam power station | 20425630 |
| AT | Voitsberg power station | 20454467 |


---

# NS-01 — cooling source river names

_Generated 2026-04-20 19:07 UTC by `scripts/run_curation01_cooling_river_names.py` (phase=harvest)._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 1.

## Phase Harvest — name resolution from local audit cache

Source: every `*.json` file under `data/raw_responses/overpass/` whose Overpass query mentions `waterway`. The audit's waterway query filters for navigable waterways (`boat=yes` / `CEMT` / `motorboat=yes`), so this only resolves the small subset of sites whose cooling source happens to be a major navigable river.

- Named waterway features in cache: **3275**
- Sites still on `HYRIV-*` at start of phase: **363**
- Sites resolved this phase: **10**

| Country | Site | Before | After | OSM kind | Dist (km) |
|---|---|---|---|---|---:|
| AL | Porto Romano Power Station | `HYRIV-20581859` | `Rruga Miqësia` | `river` | 3.74 |
| AT | Duernrohr power station | `HYRIV-20416147` | `Danube` | `river` | 6.41 |
| AT | Mellach power station | `HYRIV-20457204` | `AB VERBUND-Austrian Thermal Power` | `river` | 0.11 |
| AT | Riedersbach power station | `HYRIV-20425304` | `SLB Bürmoos – Ostermiething` | `river` | 1.17 |
| AT | St Andrae power station | `HYRIV-20461305` | `Süd Autobahn` | `river` | 0.15 |
| AT | Timelkam power station | `HYRIV-20425630` | `AB Energie Oberösterreich` | `river` | 0.06 |
| AT | Voitsberg power station | `HYRIV-20454467` | `Tunnel Voitsberg` | `river` | 0.89 |
| AT | Zeltweg power station | `HYRIV-20444840` | `Pyhrn Autobahn` | `river` | 0.26 |
| UA | Chernihiv power station | `HYRIV-20337938` | `Desna` | `river` | 9.51 |
| UA | Darnytska power station | `HYRIV-20363380` | `Dnipro River` | `river` | 5.72 |


---

# NS-01 — cooling source river names

_Generated 2026-04-20 19:07 UTC by `scripts/run_curation01_cooling_river_names.py` (phase=harvest)._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 1.

## Phase Harvest — name resolution from local audit cache

Source: every `*.json` file under `data/raw_responses/overpass/` whose Overpass query mentions `waterway`. The audit's waterway query filters for navigable waterways (`boat=yes` / `CEMT` / `motorboat=yes`), so this only resolves the small subset of sites whose cooling source happens to be a major navigable river.

- Named waterway features in cache: **17**
- Sites still on `HYRIV-*` at start of phase: **363**
- Sites resolved this phase: **3**

| Country | Site | Before | After | OSM kind | Dist (km) |
|---|---|---|---|---|---:|
| AT | Duernrohr power station | `HYRIV-20416147` | `Danube` | `river` | 6.41 |
| UA | Chernihiv power station | `HYRIV-20337938` | `Desna` | `river` | 9.51 |
| UA | Darnytska power station | `HYRIV-20363380` | `Dnipro River` | `river` | 5.72 |


---

# NS-01 — cooling source river names

_Generated 2026-04-20 19:08 UTC by `scripts/run_curation01_cooling_river_names.py` (phase=harvest)._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 1.

## Phase Harvest — name resolution from local audit cache

Source: every `*.json` file under `data/raw_responses/overpass/` whose Overpass query mentions `waterway`. The audit's waterway query filters for navigable waterways (`boat=yes` / `CEMT` / `motorboat=yes`), so this only resolves the small subset of sites whose cooling source happens to be a major navigable river.

- Named waterway features in cache: **17**
- Sites still on `HYRIV-*` at start of phase: **363**
- Sites resolved this phase: **1**
- Sites with no named-waterway hit in guard radius: **305**
- Sites where HydroRIVERS distance exceeded 12 km guard: **57**

| Country | Site | Before | After | OSM kind | Dist (km) |
|---|---|---|---|---|---:|
| AT | Duernrohr power station | `HYRIV-20416147` | `Naarnsporn` | `canal` | 2.18 |


---

# NS-01 — cooling source river names

_Generated 2026-04-20 19:09 UTC by `scripts/run_curation01_cooling_river_names.py` (phase=harvest)._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 1.

## Phase Harvest — name resolution from local audit cache

Source: every `*.json` file under `data/raw_responses/overpass/` whose Overpass query mentions `waterway`, filtered per-element on `tags.waterway in {river, canal, stream}` and `tags.name`. The audit's waterway query is restricted to navigable waterways (`boat=yes` / `CEMT` / `motorboat=yes`), so this phase only resolves the small subset of sites whose cooling source happens to be a major navigable river (Danube, Dnieper, etc.). All other HYRIV-* placeholders are deferred to the live `--phase=names` Overpass lookup.

**Note on distance**: Overpass returns each way's centroid, not the nearest point on the polyline. We cap at 12 km centroid distance and additionally skip sites where HydroRIVERS itself reports the cooling source > 12 km away. This means a few real river hits will be missed by harvest and re-resolved by phase 2 instead.

- Named waterway features in cache: **17**
- Sites still on `HYRIV-*` at start of phase: **363**
- Sites resolved this phase: **3**
- Sites with no named-waterway hit in guard radius: **303**
- Sites where HydroRIVERS distance exceeded 12 km guard: **57**

| Country | Site | Before | After | OSM kind | Dist (km) |
|---|---|---|---|---|---:|
| AT | Duernrohr power station | `HYRIV-20416147` | `Danube` | `river` | 6.41 |
| UA | Chernihiv power station | `HYRIV-20337938` | `Desna` | `river` | 9.51 |
| UA | Darnytska power station | `HYRIV-20363380` | `Dnipro River` | `river` | 5.72 |


---

# NS-01 — cooling source river names

_Generated 2026-04-20 20:38 UTC by `scripts/run_curation01_cooling_river_names.py` (phase=harvest)._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 1.

## Phase Harvest — name resolution from local audit cache

Source: every `*.json` file under `data/raw_responses/overpass/` whose Overpass query mentions `waterway`, filtered per-element on `tags.waterway in {river, canal, stream}` and `tags.name`. The audit's waterway query is restricted to navigable waterways (`boat=yes` / `CEMT` / `motorboat=yes`), so this phase only resolves the small subset of sites whose cooling source happens to be a major navigable river (Danube, Dnieper, etc.). All other HYRIV-* placeholders are deferred to the live `--phase=names` Overpass lookup.

**Note on distance**: Overpass returns each way's centroid, not the nearest point on the polyline. We cap at 12 km centroid distance and additionally skip sites where HydroRIVERS itself reports the cooling source > 12 km away. This means a few real river hits will be missed by harvest and re-resolved by phase 2 instead.

- Named waterway features in cache: **30**
- Sites still on `HYRIV-*` at start of phase: **363**
- Sites resolved this phase: **7**
- Sites with no named-waterway hit in guard radius: **299**
- Sites where HydroRIVERS distance exceeded 12 km guard: **57**

| Country | Site | Before | After | OSM kind | Dist (km) |
|---|---|---|---|---|---:|
| AT | Duernrohr power station | `HYRIV-20416147` | `Danube` | `river` | 6.41 |
| UA | Chernihiv power station | `HYRIV-20337938` | `Desna` | `river` | 9.51 |
| UA | Darnytska power station | `HYRIV-20363380` | `Dnipro River` | `river` | 5.72 |
| UA | Ladyzhyn power station | `HYRIV-20406481` | `Southern Bug` | `river` | 1.27 |
| UA | Luganskaya power station | `HYRIV-20405449` | `Aidar` | `river` | 11.37 |
| UA | Prydniprovska power station | `HYRIV-20414886` | `Dnieper River` | `river` | 5.95 |
| UA | Trypilska power station | `HYRIV-20369998` | `Dnieper River` | `river` | 1.92 |


---

# NS-01 — cooling source river names

_Generated 2026-04-20 20:39 UTC by `scripts/run_curation01_cooling_river_names.py` (phase=harvest)._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 1.

## Phase Harvest — name resolution from local audit cache

Source: every `*.json` file under `data/raw_responses/overpass/` whose Overpass query mentions `waterway`, filtered per-element on `tags.waterway in {river, canal, stream}` and `tags.name`. The audit's waterway query is restricted to navigable waterways (`boat=yes` / `CEMT` / `motorboat=yes`), so this phase only resolves the small subset of sites whose cooling source happens to be a major navigable river (Danube, Dnieper, etc.). All other HYRIV-* placeholders are deferred to the live `--phase=names` Overpass lookup.

**Note on distance**: Overpass returns each way's centroid, not the nearest point on the polyline. We cap at 12 km centroid distance and additionally skip sites where HydroRIVERS itself reports the cooling source > 12 km away. This means a few real river hits will be missed by harvest and re-resolved by phase 2 instead.

- Named waterway features in cache: **30**
- Sites still on `HYRIV-*` at start of phase: **363**
- Sites resolved this phase: **7**
- Sites with no named-waterway hit in guard radius: **299**
- Sites where HydroRIVERS distance exceeded 12 km guard: **57**

| Country | Site | Before | After | OSM kind | Dist (km) |
|---|---|---|---|---|---:|
| AT | Duernrohr power station | `HYRIV-20416147` | `Danube` | `river` | 6.41 |
| UA | Chernihiv power station | `HYRIV-20337938` | `Desna` | `river` | 9.51 |
| UA | Darnytska power station | `HYRIV-20363380` | `Dnipro River` | `river` | 5.72 |
| UA | Ladyzhyn power station | `HYRIV-20406481` | `Southern Bug` | `river` | 1.27 |
| UA | Luganskaya power station | `HYRIV-20405449` | `Aidar` | `river` | 11.37 |
| UA | Prydniprovska power station | `HYRIV-20414886` | `Dnieper River` | `river` | 5.95 |
| UA | Trypilska power station | `HYRIV-20369998` | `Dnieper River` | `river` | 1.92 |


---

# NS-01 — cooling source river names

_Generated 2026-04-20 21:13 UTC by `scripts/run_curation01_cooling_river_names.py` (phase=names)._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 1.

## Phase 2 — Overpass name resolution

- Mirrors used: https://overpass.kumi.systems/api/interpreter, https://overpass-api.de/api/interpreter, https://overpass.private.coffee/api/interpreter, https://maps.mail.ru/osm/tools/overpass/api/interpreter
- Rows attempted: **3**
- Rows resolved (real name written): **0**
- Rows with no named waterway in 2 km (HYRIV-* preserved): **3**
- Rows skipped: every mirror returned a transient error (re-run later): **0**


---

# NS-01 — cooling source river names

_Generated 2026-04-20 21:37 UTC by `scripts/run_curation01_cooling_river_names.py` (phase=names)._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 1.

## Phase 2 — Overpass name resolution

Per-site dynamic radius: ladder = (500, 1000, 2000) m plus, when HydroRIVERS reports the cooling source > 2 km away, an extra step at `ceil(cooling_distance_km*1000) + 500` m, hard-capped at **15000 m**. Among returned candidates we prefer river > canal > stream, and when several rivers are returned we pick the one whose centroid distance is closest to HydroRIVERS' own `cooling_distance_km` (so a wide search around Brăila-Chișcani picks the Danube ~4 km away rather than a small stream that happens to clip the disk).

- Rows attempted: **177**
- Rows resolved (real name written): **117**
- Rows with no named waterway in dynamic radius (HYRIV-* preserved): **19**
- Rows skipped because HydroRIVERS distance > 15000 m cap (HYRIV-* preserved to avoid picking a wrong nearby river): **41**
- Rows skipped due to Overpass error: **0**

### Resolved samples (first 30)

| Country | Site | Before | After | OSM kind | Dist (km) |
|---|---|---|---|---|---:|
| AL | Porto Romano Power Station | `HYRIV-20581859` | `Erzeni` | `river` | 14.12 |
| BG | Deven power station | `HYRIV-20543094` | `Провадийска река` | `river` | 3.89 |
| BG | Ruse Iztok power station | `HYRIV-20527851` | `Danube` | `river` | 4.68 |
| PL | Belchatow power station | `HYRIV-20341498` | `Widawka` | `river` | 2.94 |
| PL | Chorzow Elcho power station | `HYRIV-20364732` | `Bytomka` | `river` | 6.87 |
| PL | Gorzow power station | `HYRIV-20303260` | `Kłodawka` | `river` | 2.57 |
| PL | Jaworzno power station | `HYRIV-20369110` | `Przemsza` | `river` | 3.59 |
| RO | Arad power station | `HYRIV-20477064` | `Mureș` | `river` | 8.15 |
| RO | Brăila-Chișcani Thermal Power Plant | `HYRIV-20498107` | `Danube` | `river` | 42.21 |
| RS | Kolubara B power station | `HYRIV-20515540` | `Турија` | `river` | 3.92 |
| RS | Kostolac power station | `HYRIV-20509482` | `Млава` | `river` | 4.94 |
| SK | Trebisov power station | `HYRIV-20407115` | `Ondava` | `river` | 6.79 |
| TR | Afşin-Elbistan power stations | `HYRIV-20649967` | `Hurman Çayı` | `river` | 5.49 |
| TR | Ağan power station | `HYRIV-20606276` | `Biga Çayı` | `river` | 11.94 |
| TR | Albayrak Varaka Paper power station | `HYRIV-20622867` | `Atnos Çayı` | `river` | 5.18 |
| TR | Aliağa Enka power station | `HYRIV-20643835` | `Gediz River` | `river` | 16.13 |
| TR | Alpu power station | `HYRIV-20618923` | `Porsuk Çayı` | `river` | 14.52 |
| TR | Amasra Bartın power station | `HYRIV-20577134` | `Bartın Çayı` | `river` | 9.32 |
| TR | Ant Enerji power station | `HYRIV-20669430` | `Kamişdere` | `stream` | 4.94 |
| TR | Avdan power station | `HYRIV-20659722` | `Kozlupınar Deresi` | `stream` | 2.05 |
| TR | Bandırma Elektrik power station | `HYRIV-20609429` | `Aesepus River` | `river` | 9.36 |
| TR | Bandırma III power station | `HYRIV-20630057` | `Yağcılı Çayı` | `stream` | 9.10 |
| TR | Bandırma Karat power station | `HYRIV-20608612` | `Çamaşır Deresi` | `stream` | 1.50 |
| TR | Barbaros-1 power station | `HYRIV-20572413` | `Sarmısak Çayı` | `river` | 9.20 |
| TR | Biga power station | `HYRIV-20606276` | `Biga Çayı` | `river` | 14.42 |
| TR | Bingöl power station | `HYRIV-20627547` | `Peri River` | `river` | 8.13 |
| TR | Bolu Göynük power station | `HYRIV-20609440` | `Gökdere` | `stream` | 2.68 |
| TR | Burnaz power station | `HYRIV-20687224` | `Karasu Çayı` | `river` | 14.37 |
| TR | Bursa power station | `HYRIV-20616967` | `Kuz Dere` | `stream` | 4.72 |
| TR | Çan (18 Mart) power station | `HYRIV-20614452` | `Biga Çayı` | `river` | 5.52 |
| TR | Çan-2 power station | `HYRIV-20614832` | `Biga Çayı` | `river` | 7.90 |
| TR | Çankırı Orta power station | `HYRIV-20599955` | `Devrez Çayı` | `river` | 1.60 |
| TR | Çayırhan power station | `HYRIV-20612772` | `Aladağ Çayı` | `river` | 5.59 |
| TR | Çebi Enerji power station | `HYRIV-20591429` | `Kınıklı Deresi` | `stream` | 1.75 |
| TR | Cenal power station | `HYRIV-20606276` | `Biga Çayı` | `river` | 8.48 |
| TR | Çırpılar power station | `HYRIV-20617970` | `Aesepus River` | `river` | 4.47 |
| TR | Deniz power station | `HYRIV-20643835` | `Gediz River` | `river` | 16.13 |
| TR | Dinar power station | `HYRIV-20654688` | `Büyük Menderes` | `stream` | 5.22 |
| TR | DOSAB cogeneration plant | `HYRIV-20608160` | `Nilüfer River` | `river` | 4.46 |
| TR | Enyat Samsun power station | `HYRIV-20590635` | `Tersakan Çayı` | `river` | 2.00 |
| TR | Eren-1 power station | `HYRIV-20579375` | `Teke Çayı` | `stream` | 3.18 |
| TR | Ergene power station | `HYRIV-20585927` | `Ergene Nehri` | `river` | 4.00 |
| TR | Eti Maden Bandirma power station | `HYRIV-20608612` | `Çamaşır Deresi` | `stream` | 2.08 |
| TR | Filyos power station | `HYRIV-20579031` | `Filyos Çayı` | `river` | 4.07 |
| TR | Gebze Çolakoğlu power station | `HYRIV-20596929` | `Dilderesi` | `river` | 4.42 |
| TR | Gönen power station | `HYRIV-20612510` | `Aesepus River` | `river` | 5.82 |
| TR | Güneybatı Anadolu power station | `HYRIV-20670722` | `Sarıçay` | `river` | 3.28 |
| TR | Güreci power station | `HYRIV-20608817` | `Lapseki` | `stream` | 0.87 |
| TR | Habaş power station | `HYRIV-20639291` | `Güzelhisar Çayı` | `stream` | 9.40 |
| TR | Hakan Kömür power station | `HYRIV-20676428` | `Ceyhan River` | `river` | 9.84 |
