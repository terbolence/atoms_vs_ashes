<!-- man_hours: 1.0 -->

# Site Area Coverage — All Sites (Post-Write, n=361)

**Source:** `audit/post_processing/06_scoring/20260517_site_area_confidence.csv`
**DB write run ID:** `site_area_resolve_v2_20260517T112800Z`
**Generated from:** post-write merged DB read-only audit (`audit_site_area_confidence.py`).

Usable value threshold: **>= 1 ha**. "Neither" = both `site_area_ha` and `favourable_area_ha` are null, zero, or below 1 ha.
`favourable_area_ha` was not updated by the site-area apply script.

---

## Executive summary

| Metric | Current DB after write | Current recommendation rerun |
| --- | ---: | ---: |
| Sites in audit | 361 | 361 |
| Both `site_area_ha` and favourable >= 1 ha | 332 | 332 |
| `site_area_ha` only (no favourable) | 29 | 29 |
| Favourable only (no `site_area_ha`) | 0 | 0 |
| **Neither metric >= 1 ha** | **0** | **0** |
| `unidentified` / null recommendation | — | 0 |

**Conclusion:** The DB now has **0** site(s) lacking both `site_area_ha` and `favourable_area_ha`; **29** site(s) still lack a usable favourable envelope but now have `site_area_ha`.

### Recommendation source mix after write

| Source | Count |
| --- | ---: |
| `buildable_area_inference` | 238 |
| `llm_web_observation` | 63 |
| `favourable_envelope_inference` | 42 |
| `osm_polygon` | 7 |
| `capacity_bounded_inference` | 7 |
| `contiguous_capped_inference` | 4 |

### Recommendation confidence mix after write

| Confidence | Count |
| --- | ---: |
| review | 208 |
| low | 83 |
| medium | 54 |
| high | 16 |

## A. Current DB: neither `site_area_ha` nor favourable >= 1 ha (0)

_None._



## B. Current DB: `site_area_ha` only — favourable below 1 ha (29)

| CC | Plant | Status | Current `site_area_ha` | Favourable envelope | Recommended `site_area_ha` | Recommendation source | Confidence | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AT | Zeltweg power station | retired | 39.04 | 0 | 39.04 | buildable_area_inference | review | S3;S4;S6;S7 |
| CZ | Mostecka Power Station | cancelled | 6.65 | 0 | 6.65 | capacity_bounded_inference | review | S8 |
| HR | Ploče power station | cancelled | 238.74 | 0 | 238.74 | buildable_area_inference | review | S8 |
| MK | Bitola power station | operating | 145.73 | 0 | 25 | llm_web_observation | medium | S6 |
| MK | Mariovo power station | cancelled | 151.22 | 0 | 151.22 | buildable_area_inference | review | S7;S8 |
| PL | Legnica Power Station | cancelled | 6.25 | 0 | 6.25 | capacity_bounded_inference | review | S8 |
| PL | Lodz-2 power station | retired | 6.39 | 0 | 6.39 | buildable_area_inference | low | — |
| PL | Szczecin power station | operating | 9.61 | 0 | 9.61 | buildable_area_inference | low | — |
| RO | Bucharest North East power station | cancelled | 1.9 | 0 | 1.9 | buildable_area_inference | review | S8 |
| RO | Galati Power Station | cancelled | 22.3 | 0 | 22.3 | llm_web_observation | medium | S8 |
| TR | Ağan power station | cancelled | 32.65 | 0.65 | 32.65 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Babadere power station | cancelled | 224.39 | 0 | 224.39 | buildable_area_inference | review | S7;S8 |
| TR | Biga power station | cancelled | 31.04 | 0 | 31.04 | buildable_area_inference | review | S7;S8 |
| TR | Evrese power station | cancelled | 11.23 | 0 | 11.23 | buildable_area_inference | review | S8 |
| TR | Güreci power station | cancelled | 151.51 | 0 | 151.51 | buildable_area_inference | review | S7;S8 |
| TR | Irmak power station | cancelled | 1.58 | 0 | 1.58 | capacity_bounded_inference | review | S8 |
| TR | Karaburun power station | cancelled | 36.4 | 0.36 | 36.4 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Kirazlıdere power complex | cancelled | 1.86 | 0 | 1.86 | capacity_bounded_inference | review | S7;S8 |
| TR | Kireçlik power station | cancelled | 3.82 | 0 | 3.82 | capacity_bounded_inference | review | S7;S8 |
| TR | Lüminer Enerji power station | cancelled | 12.8 | 0 | 12.8 | capacity_bounded_inference | review | S8 |
| TR | Namal power station | cancelled | 151.51 | 0 | 151.51 | buildable_area_inference | review | S7;S8 |
| TR | Naren Karabiga power station | cancelled | 15.3 | 0 | 15.3 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Tekirdağ Malkara power station | shelved | 79.64 | 0.55 | 79.64 | contiguous_capped_inference | review | S3;S7 |
| TR | Trakya Emba power station | cancelled | 24.38 | 0.49 | 24.38 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Yenidere power station | shelved | 14.84 | 0.59 | 14.84 | buildable_area_inference | review | S3;S4;S7 |
| TR | Zafer power station | cancelled | 5.34 | 0 | 5.34 | capacity_bounded_inference | review | S7;S8 |
| TR | Çan (18 Mart) power station | operating | 81.2 | 0 | 81.2 | buildable_area_inference | low | — |
| TR | Çan-2 power station | operating | 28.48 | 0 | 28.48 | osm_polygon | medium | — |
| TR | Şevketiye Lapseki power station | cancelled | 254.45 | 0 | 254.45 | buildable_area_inference | review | S7;S8 |



## C. Current DB: favourable only — no `site_area_ha` >= 1 ha (0)

_None._



## D. Rerun recommendations: neither `site_area_ha` nor favourable >= 1 ha (0)

_None._



## E. Full site register (all 361)

| CC | Plant | Status | Current `site_area_ha` | Favourable envelope | Recommended `site_area_ha` | Recommendation source | Confidence | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AL | Porto Romano Power Station | cancelled | 64 | 42.12 | 64 | contiguous_capped_inference | review | S3;S4;S8 |
| AT | Duernrohr power station | retired | 120 | 288.97 | 120 | llm_web_observation | medium | — |
| AT | Enns Power Station | cancelled | 41.49 | 41.49 | 41.49 | favourable_envelope_inference | review | S8 |
| AT | Mellach power station | retired | 12 | 142.13 | 12 | llm_web_observation | medium | — |
| AT | Riedersbach power station | retired | 18 | 90.15 | 18 | llm_web_observation | medium | — |
| AT | St Andrae power station | retired | 39.03 | 112.86 | 39.03 | buildable_area_inference | review | S6;S7 |
| AT | Timelkam power station | retired | 30.65 | 150.39 | 30.65 | buildable_area_inference | review | S6;S7 |
| AT | Voitsberg power station | retired | 24.5 | 22.13 | 24.5 | llm_web_observation | high | S4;S7 |
| AT | Zeltweg power station | retired | 39.04 | 0 | 39.04 | buildable_area_inference | review | S3;S4;S6;S7 |
| BA | Banovici power station | cancelled | 55.98 | 6.16 | 55.98 | buildable_area_inference | review | S3;S4;S7;S8 |
| BA | Bugojno Thermal Power Project | cancelled | 109.02 | 109.02 | 109.02 | favourable_envelope_inference | review | S8 |
| BA | Gacko Thermal Power Plant | operating | 96.78 | 127.09 | 96.78 | buildable_area_inference | review | S6 |
| BA | Glinica power station | cancelled | 94.12 | 26.35 | 94.12 | buildable_area_inference | review | S3;S4;S7;S8 |
| BA | Kakanj Thermal Power Plant | operating | 42 | 16.6 | 8.3 | favourable_envelope_inference | low | — |
| BA | Kamengrad Thermal Power Plant | cancelled | 89.84 | 89.84 | 89.84 | favourable_envelope_inference | review | S8 |
| BA | Kongora Thermal Power Plant | cancelled | 228.22 | 75.31 | 228.22 | buildable_area_inference | review | S3;S4;S7;S8 |
| BA | Miljevina power station | cancelled | 106.24 | 6.37 | 106.24 | buildable_area_inference | review | S3;S4;S7;S8 |
| BA | Stanari Thermal Power Plant | operating | 269 | 53.76 | 269 | llm_web_observation | medium | — |
| BA | Tuzla Thermal Power Plant | operating | 130 | 36.39 | 130 | llm_web_observation | medium | S3;S4 |
| BA | Ugljevik power station | operating | 47.15 | 40.61 | 47.15 | osm_polygon | medium | — |
| BG | Bobov Dol power station | operating | 63 | 206.43 | 63 | llm_web_observation | high | S4 |
| BG | Brikel power station | operating | 40 | 116.39 | 16.8 | buildable_area_inference | low | — |
| BG | Deven power station | operating | 27.26 | 176.64 | 27.26 | buildable_area_inference | low | — |
| BG | Lom Power Station | cancelled | 146.29 | 146.29 | 146.29 | favourable_envelope_inference | review | S8 |
| BG | Maritsa 3 power station | mothballed | 18.87 | 159.18 | 18.87 | buildable_area_inference | low | — |
| BG | Maritsa Iztok-1 power station | operating | 57.27 | 103.79 | 55 | llm_web_observation | medium | — |
| BG | Maritsa Iztok-2 power station | operating | 512 | 177.54 | 512 | llm_web_observation | high | — |
| BG | Maritsa Iztok-3 power station | operating | 300 | 298.4 | 300 | llm_web_observation | medium | — |
| BG | Maritsa Iztok-4 power station | cancelled | 124.34 | 298.4 | 124.34 | buildable_area_inference | review | S8 |
| BG | Republika power station | operating | 232.26 | 177.83 | 232.26 | buildable_area_inference | review | S6;S7 |
| BG | Ruse Iztok power station | operating | 32 | 274.91 | 31.99 | buildable_area_inference | low | — |
| BG | Sliven power station | operating | 15.13 | 238.72 | 15.13 | buildable_area_inference | review | S6 |
| BG | Svilosa power station | retired | 172 | 77.14 | 172 | llm_web_observation | medium | S7 |
| BG | Varna power station | retired | 100 | 73.54 | 12.26 | buildable_area_inference | low | — |
| BG | Vidin Works power station | mothballed | 130 | 169.46 | 130 | llm_web_observation | medium | S4;S7 |
| BY | Lelchitsy power station | cancelled | 11.01 | 134.06 | 11.01 | buildable_area_inference | review | S8 |
| BY | Zelwa power station | cancelled | 101.41 | 101.41 | 101.41 | favourable_envelope_inference | review | S8 |
| CZ | Chvaletice power station | operating | 93.87 | 110.28 | 66 | llm_web_observation | medium | S7 |
| CZ | Detmarovice power station | retired | 64 | 176.15 | 64 | llm_web_observation | medium | — |
| CZ | Hodonin power station | operating | 24.5 | 152.86 | 24.5 | buildable_area_inference | review | S6 |
| CZ | Karvina power station | operating | 81.16 | 78.67 | 81.16 | buildable_area_inference | review | S6;S7 |
| CZ | Kladno power station | operating | 12.73 | 129.02 | 12.73 | buildable_area_inference | review | S6 |
| CZ | Komorany power station | operating | 39.28 | 79.28 | 39.28 | buildable_area_inference | review | S6 |
| CZ | Ledvice power station | operating | 65 | 149.92 | 65 | llm_web_observation | high | S4;S7 |
| CZ | Malesice power station | operating | 189.19 | 260.45 | 189.19 | buildable_area_inference | low | S7 |
| CZ | Marianske Hory power station | retired | 49.32 | 69.1 | 49.32 | buildable_area_inference | low | — |
| CZ | Melnik power station | operating | 85.6 | 193.25 | 85.6 | llm_web_observation | high | S4 |
| CZ | Mondi Steti power station | operating | 180.77 | 176.4 | 180.77 | buildable_area_inference | review | S6;S7 |
| CZ | Mostecka Power Station | cancelled | 6.65 | 0 | 6.65 | capacity_bounded_inference | review | S8 |
| CZ | Olomouc power station | operating | 24.21 | 225.6 | 24.21 | buildable_area_inference | low | — |
| CZ | Opatovice power station | operating | 57.17 | 209.98 | 57.17 | buildable_area_inference | low | — |
| CZ | Plana Nad Luznici power station | retired | 10.59 | 163.09 | 10.59 | buildable_area_inference | low | — |
| CZ | Plzen CHP power station | operating | 123.88 | 166.82 | 123.88 | buildable_area_inference | review | S6;S7 |
| CZ | Plzenska energetika ELU III power station | operating | 154.51 | 206.01 | 154.51 | favourable_envelope_inference | low | — |
| CZ | Pocerady power station | operating | 90.76 | 270.27 | 90 | llm_web_observation | medium | S7 |
| CZ | Porici power station | operating | 24.51 | 84.28 | 24.51 | buildable_area_inference | low | — |
| CZ | Prerov power station | retired | 171.62 | 278.75 | 171.62 | buildable_area_inference | low | S7 |
| CZ | Pribram power station | operating | 41.44 | 159.32 | 41.44 | buildable_area_inference | low | — |
| CZ | Prunerov power station | operating | 300 | 91.04 | 300 | llm_web_observation | high | — |
| CZ | Sko-Energo power station | operating | 30.05 | 257.75 | 30.05 | buildable_area_inference | low | — |
| CZ | Tisova power station | operating | 37.5 | 125.83 | 37.5 | buildable_area_inference | low | — |
| CZ | Trebovice power station | operating | 38.58 | 191.51 | 38.58 | buildable_area_inference | review | S6 |
| CZ | Trinec-E3 power station | operating | 58.7 | 61.18 | 58.7 | buildable_area_inference | low | S7 |
| CZ | Tusimice power station | operating | 104.46 | 190.44 | 64 | llm_web_observation | medium | — |
| CZ | Vresova TPS power station | retired | 106.98 | 41.34 | 106.98 | buildable_area_inference | review | S6 |
| CZ | Zlin power station | operating | 11.63 | 124.27 | 11.63 | buildable_area_inference | low | — |
| HR | Plomin power station | operating | 30 | 7.49 | 21.14 | buildable_area_inference | low | — |
| HR | Ploče power station | cancelled | 238.74 | 0 | 238.74 | buildable_area_inference | review | S8 |
| HU | Bakony power station | retired | 6 | 129.35 | 6 | llm_web_observation | medium | S2;S4 |
| HU | Banhida-II power station | retired | 11 | 175.12 | 11 | llm_web_observation | medium | — |
| HU | Borsod power station | cancelled | 66.01 | 168.74 | 66.01 | buildable_area_inference | review | S7;S8 |
| HU | Matra power station | operating | 244 | 108.83 | 244 | llm_web_observation | high | — |
| HU | Matraterenye power station | cancelled | 98.54 | 98.54 | 98.54 | favourable_envelope_inference | review | S8 |
| HU | Mecsek Hills power station | cancelled | 3.54 | 2.39 | 3.54 | buildable_area_inference | review | S8 |
| HU | Mohacs power station | cancelled | 30.16 | 68.64 | 30.16 | buildable_area_inference | review | S7;S8 |
| HU | Oroszlány power station | mothballed | 61 | 150.46 | 61 | llm_web_observation | medium | — |
| HU | Pecs power station | retired | 6.5 | 169.93 | 84.97 | favourable_envelope_inference | low | S2 |
| HU | Tiszapalkonya power station | retired | 18.77 | 98.06 | 18.77 | buildable_area_inference | low | — |
| HU | Torony power station | cancelled | 135.32 | 89.3 | 135.32 | buildable_area_inference | review | S3;S4;S7;S8 |
| LV | Kurzeme power station | cancelled | 8.7 | 32.51 | 8.7 | buildable_area_inference | review | S8 |
| MD | Kuchurgan power station | mothballed | 200 | 80.65 | 200 | llm_web_observation | medium | — |
| ME | Bar power station | cancelled | 92.86 | 92.86 | 92.86 | favourable_envelope_inference | review | S8 |
| ME | Berane power station | cancelled | 277.03 | 72.02 | 277.03 | buildable_area_inference | review | S3;S4;S7;S8 |
| ME | Maoce Power Station | cancelled | 43.45 | 31.54 | 43.45 | buildable_area_inference | review | S8 |
| ME | Pljevlja power station | operating | 38 | 26.41 | 38 | llm_web_observation | medium | — |
| MK | Bitola power station | operating | 145.73 | 0 | 25 | llm_web_observation | medium | S6 |
| MK | Mariovo power station | cancelled | 151.22 | 0 | 151.22 | buildable_area_inference | review | S7;S8 |
| MK | Negotino power station | cancelled | 192.91 | 192.91 | 192.91 | favourable_envelope_inference | review | S6;S8 |
| MK | Oslomej power station | operating | 26 | 51.17 | 26 | llm_web_observation | high | — |
| PL | Adamow power station | retired | 158.87 | 211.82 | 158.87 | favourable_envelope_inference | low | — |
| PL | Bedzin power station | operating | 13.42 | 138.08 | 13.42 | buildable_area_inference | low | — |
| PL | Belchatow power station | operating | 500 | 101.68 | 500 | llm_web_observation | medium | S7 |
| PL | Bialystok power station | operating | 27.13 | 137.36 | 27.13 | buildable_area_inference | low | — |
| PL | Bielsko-Biala power station | operating | 63.06 | 61.84 | 63.06 | buildable_area_inference | low | S7 |
| PL | Blachownia power station | cancelled | 10.39 | 59.66 | 10.39 | buildable_area_inference | review | S8 |
| PL | Bydgoszcz power station | operating | 40.66 | 219.47 | 40.66 | buildable_area_inference | low | — |
| PL | Chorzow Elcho power station | operating | 169.89 | 198.53 | 169.89 | buildable_area_inference | low | S7 |
| PL | Czeczott power station | cancelled | 88.03 | 88.03 | 88.03 | favourable_envelope_inference | review | S8 |
| PL | Czestochowa CHP power station | operating | 48.45 | 64.6 | 48.45 | favourable_envelope_inference | low | — |
| PL | Dolna Odra power station | operating | 345 | 117.76 | 345 | llm_web_observation | high | — |
| PL | Gdansk-2 power station | operating | 143.61 | 130.68 | 143.61 | buildable_area_inference | low | S7 |
| PL | Gdynia-3 power station | operating | 141.25 | 142.88 | 141.25 | buildable_area_inference | low | S7 |
| PL | Gliwice Works power station | operating | 58.3 | 212.62 | 58.3 | buildable_area_inference | low | — |
| PL | Gorzow power station | operating | 22.65 | 282.6 | 22.65 | buildable_area_inference | low | — |
| PL | Gubin Power Project | cancelled | 38.76 | 38.76 | 38.76 | favourable_envelope_inference | review | S8 |
| PL | Halemba power station | cancelled | 59.94 | 62.27 | 59.94 | buildable_area_inference | review | S8 |
| PL | Jaworzno power station | operating | 175 | 63.5 | 175 | llm_web_observation | medium | — |
| PL | Katowice PKE power station | operating | 37.34 | 251.07 | 37.34 | buildable_area_inference | low | — |
| PL | Kedzierzyn CCS Project | cancelled | 7.65 | 7.65 | 7.65 | favourable_envelope_inference | review | S8 |
| PL | Konin power station | retired | 28.33 | 120.46 | 28.33 | buildable_area_inference | low | — |
| PL | Kozienice power station | operating | 400 | 15.45 | 400 | llm_web_observation | medium | S3;S7 |
| PL | Krakow-Leg power station | operating | 46.63 | 266.35 | 46.63 | buildable_area_inference | low | — |
| PL | Lagisza power station | operating | 48.44 | 114.34 | 48.44 | buildable_area_inference | low | — |
| PL | Laziska power station | operating | 43.16 | 193.66 | 43.16 | buildable_area_inference | low | — |
| PL | Leczna Power Station (Bogdanka SA) | cancelled | 75.29 | 75.29 | 75.29 | favourable_envelope_inference | review | S8 |
| PL | Leczna Power Station (Enea) | cancelled | 63.63 | 63.63 | 63.63 | favourable_envelope_inference | review | S8 |
| PL | Legnica Power Station | cancelled | 6.25 | 0 | 6.25 | capacity_bounded_inference | review | S8 |
| PL | Lodz-2 power station | retired | 6.39 | 0 | 6.39 | buildable_area_inference | low | — |
| PL | Lodz-3 power station | operating | 14.67 | 154 | 14.67 | buildable_area_inference | low | — |
| PL | Lodz-4 power station | operating | 50.7 | 168.08 | 50.7 | buildable_area_inference | low | — |
| PL | Lublin Power Station | cancelled | 25.3 | 141.4 | 25.3 | buildable_area_inference | review | S8 |
| PL | Miechowice power station | retired | 60.58 | 80.77 | 60.58 | favourable_envelope_inference | low | — |
| PL | Murcki-Staszic power station | cancelled | 5.97 | 29.15 | 5.97 | buildable_area_inference | review | S8 |
| PL | Opalenie power station | cancelled | 215.38 | 116.32 | 215.38 | buildable_area_inference | review | S3;S4;S7;S8 |
| PL | Opole power station | operating | 280 | 151.62 | 280 | llm_web_observation | medium | — |
| PL | Ostrołęka power station | operating | 27 | 111.53 | 27 | llm_web_observation | medium | S4 |
| PL | Patnow power station | operating | 140 | 52.3 | 53.08 | buildable_area_inference | low | — |
| PL | Piast Ruch Power Station | cancelled | 57.24 | 68.14 | 57.24 | buildable_area_inference | review | S8 |
| PL | Polaniec power station | operating | 188 | 114.42 | 188 | llm_web_observation | medium | — |
| PL | Pomorzany power station | operating | 80.95 | 107.93 | 80.95 | favourable_envelope_inference | low | — |
| PL | Poznan Karolin power station | operating | 125.38 | 167.17 | 125.38 | favourable_envelope_inference | low | — |
| PL | Puchaczow power station | cancelled | 280.55 | 249.73 | 280.55 | buildable_area_inference | review | S3;S4;S7;S8 |
| PL | Pulawy ZAP Works power station | operating | 273.47 | 118.72 | 273.47 | buildable_area_inference | low | S7 |
| PL | Pulawy power station (Grupa Azoty) | construction | 2.84 | 5.68 | 2.84 | favourable_envelope_inference | low | — |
| PL | Pulawy power station (Vattenfall) | cancelled | 5.68 | 5.68 | 5.68 | favourable_envelope_inference | review | S8 |
| PL | Pólnoc power station | cancelled | 209.76 | 209.76 | 209.76 | favourable_envelope_inference | review | S8 |
| PL | Rybnik power station | operating | 70.48 | 93.98 | 142 | llm_web_observation | medium | S6 |
| PL | Siechnice power station | retired | 81.51 | 108.68 | 81.51 | favourable_envelope_inference | low | — |
| PL | Siekierki power station | operating | 56.74 | 142.74 | 56.74 | osm_polygon | medium | — |
| PL | Siersza power station | operating | 70.3 | 27.43 | 70.3 | buildable_area_inference | low | S7 |
| PL | Skawina power station | operating | 50.6 | 199.78 | 50.6 | buildable_area_inference | low | — |
| PL | Stalowa Wola power station | retired | 45.54 | 169.77 | 45.54 | buildable_area_inference | low | — |
| PL | Swiecie Pulp Mill power station | operating | 59.23 | 78.97 | 59.23 | favourable_envelope_inference | low | — |
| PL | Szczecin power station | operating | 9.61 | 0 | 9.61 | buildable_area_inference | low | — |
| PL | Turów power station | operating | 164 | 92.22 | 164 | llm_web_observation | medium | S7 |
| PL | Tychy power station | operating | 14.09 | 186.93 | 14.09 | buildable_area_inference | low | — |
| PL | Wroclaw power station | operating | 17.64 | 34.2 | 17.64 | osm_polygon | medium | — |
| PL | ZW Nowa power station | operating | 314.13 | 266.99 | 314.13 | buildable_area_inference | low | S7 |
| PL | Zabrze power station | operating | 70.86 | 94.48 | 70.86 | favourable_envelope_inference | low | — |
| PL | Zarnowiec power station | cancelled | 114.66 | 114.66 | 114.66 | favourable_envelope_inference | review | S8 |
| PL | Zeran power station | operating | 25.72 | 97.41 | 25.72 | buildable_area_inference | low | — |
| PL | Zofiowka Mine power station | operating | 92.17 | 122.89 | 92.17 | favourable_envelope_inference | low | — |
| RO | Arad power station | retired | 70.86 | 295.27 | 3.6 | llm_web_observation | medium | S6 |
| RO | Bacau CHP power station | retired | 4.8 | 215.69 | 4.8 | llm_web_observation | medium | S2;S4;S7 |
| RO | Braila power station | retired | 41.78 | 179.76 | 41.78 | buildable_area_inference | low | — |
| RO | Brasov power station | retired | 50 | 236.5 | 50 | llm_web_observation | medium | S4 |
| RO | Bucharest North East power station | cancelled | 1.9 | 0 | 1.9 | buildable_area_inference | review | S8 |
| RO | Craiova II power station | operating | 120.84 | 134.75 | 120.84 | buildable_area_inference | review | S6;S7 |
| RO | Doicesti power station | cancelled | 40 | 49.32 | 40 | llm_web_observation | high | S8 |
| RO | FPCU Feldioara | operating | 345 | 314.1 | 345 | llm_web_observation | high | — |
| RO | Galati Power Station | cancelled | 22.3 | 0 | 22.3 | llm_web_observation | medium | S8 |
| RO | Giurgiu power station | retired | 140 | 138.82 | 140 | llm_web_observation | medium | S7 |
| RO | Govora power station | operating | 28.15 | 278.91 | 28.15 | llm_web_observation | medium | — |
| RO | Iasi-2 power station | retired | 64.11 | 245 | 64.11 | buildable_area_inference | review | S6 |
| RO | Isalnita power station | mothballed | 159.43 | 222.36 | 120 | llm_web_observation | medium | S7 |
| RO | Mintia-Deva power station | retired | 329.78 | 131.99 | 329.78 | llm_web_observation | high | — |
| RO | Oradea power station | retired | 11.23 | 279.19 | 11.23 | buildable_area_inference | review | S6 |
| RO | Paroseni power station | operating | 82.67 | 87.56 | 82.67 | buildable_area_inference | review | S6;S7 |
| RO | Romag Termo power station | cancelled | 80.94 | 169.31 | 80.94 | llm_web_observation | high | S4;S8 |
| RO | Rovinari power station | operating | 150 | 128.18 | 150 | llm_web_observation | medium | — |
| RO | Slatina power station | cancelled | 11.51 | 7.06 | 11.51 | contiguous_capped_inference | review | S3;S4;S7;S8 |
| RO | Suceava power station | retired | 75.56 | 247.28 | 75.56 | buildable_area_inference | review | S6 |
| RO | Turceni power station | operating | 173 | 235.12 | 173 | llm_web_observation | high | — |
| RO | Târgu Jiu Thermal Plant | cancelled | 9 | 7.47 | 9 | llm_web_observation | medium | S8 |
| RS | Despotovac power station | cancelled | 195.82 | 105.73 | 195.82 | buildable_area_inference | review | S3;S4;S7;S8 |
| RS | Kolubara A power station | operating | 51.45 | 77.92 | 51.45 | buildable_area_inference | low | — |
| RS | Kolubara B power station | cancelled | 51.45 | 79.22 | 51.45 | buildable_area_inference | review | S8 |
| RS | Kostolac power station | operating | 109 | 38.62 | 36.95 | buildable_area_inference | low | — |
| RS | Kovin power station | cancelled | 209.27 | 209.27 | 209.27 | favourable_envelope_inference | review | S8 |
| RS | Morava power station | operating | 12 | 115.02 | 12 | llm_web_observation | medium | — |
| RS | Nikola Tesla power station | operating | 300 | 64.72 | 300 | llm_web_observation | medium | — |
| RS | Štavalj Power Station | cancelled | 79.97 | 79.97 | 79.97 | favourable_envelope_inference | review | S8 |
| SI | Sostanj power station | operating | 108 | 46.44 | 76.89 | buildable_area_inference | low | S7 |
| SI | Te-Tol power station | operating | 12 | 119.56 | 89.67 | favourable_envelope_inference | low | — |
| SI | Trbovlje power station | retired | 12 | 3.64 | 12 | llm_web_observation | medium | — |
| SK | Kosice power station | operating | 64.19 | 209.67 | 64.19 | buildable_area_inference | review | S6 |
| SK | Martinska power station | retired | 252.87 | 228.51 | 252.87 | buildable_area_inference | review | S6 |
| SK | Novaky power station | retired | 20 | 217.32 | 20 | llm_web_observation | medium | S4;S7 |
| SK | Trebisov power station | cancelled | 33.63 | 33.63 | 33.63 | favourable_envelope_inference | review | S7;S8 |
| SK | U.S. Steel Kosice Works power station | operating | 11.95 | 301.06 | 11.95 | buildable_area_inference | review | S6 |
| SK | Vojany I power station | retired | 53 | 195.58 | 53 | llm_web_observation | high | S4 |
| TR | Ada Yesildag Enerji power station | cancelled | 14 | 138.7 | 14 | buildable_area_inference | review | S8 |
| TR | Ada Yumurtalık power station | cancelled | 171.87 | 179.92 | 171.87 | buildable_area_inference | review | S8 |
| TR | Adana Akdeniz power station | cancelled | 74.83 | 50.22 | 74.83 | buildable_area_inference | review | S8 |
| TR | Adana Ceyhan power station | cancelled | 19.4 | 241.5 | 19.4 | buildable_area_inference | review | S8 |
| TR | Afşin-Elbistan power stations | operating | 109.83 | 225.55 | 109.83 | osm_polygon | medium | — |
| TR | Akdeniz Enerji power station | cancelled | 229.17 | 55.01 | 229.17 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Aksa Akrilik power station | operating | 72.58 | 70.06 | 72.58 | buildable_area_inference | review | S3;S4 |
| TR | Albayrak Varaka Paper power station | operating | 76.74 | 168.34 | 76.74 | buildable_area_inference | low | — |
| TR | Aliağa Enka power station | cancelled | 11.75 | 74.07 | 11.75 | buildable_area_inference | review | S8 |
| TR | Alpu power station | cancelled | 314.05 | 273.27 | 314.05 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Amasra Bartın power station | cancelled | 11.35 | 1.26 | 11.35 | buildable_area_inference | review | S8 |
| TR | Ant Enerji power station | cancelled | 51.68 | 8.27 | 51.68 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Astoria Ceyhan power station | cancelled | 21.33 | 67.22 | 21.33 | buildable_area_inference | review | S8 |
| TR | Atakaş power station | cancelled | 41.26 | 67.62 | 41.26 | buildable_area_inference | review | S8 |
| TR | Atlas Enerji İskenderun power station | operating | 63.5 | 84.67 | 63.5 | osm_polygon | medium | — |
| TR | Avdan power station | cancelled | 163.91 | 163.91 | 163.91 | favourable_envelope_inference | review | S8 |
| TR | Ayas power station | cancelled | 74.83 | 54.21 | 74.83 | buildable_area_inference | review | S8 |
| TR | Ağan power station | cancelled | 32.65 | 0.65 | 32.65 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Babadere power station | cancelled | 224.39 | 0 | 224.39 | buildable_area_inference | review | S7;S8 |
| TR | Bandırma Elektrik power station | cancelled | 134.98 | 39.15 | 134.98 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Bandırma III power station | cancelled | 78.33 | 4.7 | 78.33 | buildable_area_inference | review | S7;S8 |
| TR | Bandırma Karat power station | cancelled | 78.67 | 78.67 | 78.67 | favourable_envelope_inference | review | S8 |
| TR | Barbaros-1 power station | cancelled | 199.39 | 55.83 | 199.39 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Biga power station | cancelled | 31.04 | 0 | 31.04 | buildable_area_inference | review | S7;S8 |
| TR | Bingöl power station | cancelled | 314.13 | 34.55 | 314.13 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Bolu Göynük power station | operating | 14.08 | 111.46 | 14.08 | buildable_area_inference | low | — |
| TR | Burnaz power station | cancelled | 109.28 | 13.12 | 109.28 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Bursa power station | cancelled | 268.72 | 42.99 | 268.72 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Cenal power station | operating | 93.05 | 45.77 | 93.05 | buildable_area_inference | low | — |
| TR | DETES 1 power station | cancelled | 23.37 | 9.9 | 23.37 | buildable_area_inference | review | S8 |
| TR | DOSAB cogeneration plant | cancelled | 11.2 | 240.29 | 11.2 | buildable_area_inference | review | S8 |
| TR | Demirtaş power station | cancelled | 261.56 | 162.19 | 261.56 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Deniz power station | cancelled | 255.45 | 74.07 | 255.45 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Diler (Akbayir) Elbistan power station | cancelled | 314.13 | 288.97 | 314.13 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Dinar power station | cancelled | 286.04 | 174.46 | 286.04 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | EMBA Hunutlu power station | operating | 74.83 | 72.65 | 74.83 | osm_polygon | medium | — |
| TR | Ece power station | cancelled | 261.56 | 162.19 | 261.56 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Enyat Samsun power station | cancelled | 170.75 | 170.75 | 170.75 | favourable_envelope_inference | review | S8 |
| TR | Eren-1 power station | cancelled | 311.81 | 249.44 | 311.81 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Ergene power station | cancelled | 226.32 | 226.32 | 226.32 | favourable_envelope_inference | review | S8 |
| TR | Eti Maden Bandirma power station | operating | 50.83 | 178 | 50.83 | buildable_area_inference | low | — |
| TR | Evrese power station | cancelled | 11.23 | 0 | 11.23 | buildable_area_inference | review | S8 |
| TR | Filyos power station | cancelled | 243.22 | 62.04 | 243.22 | buildable_area_inference | review | S8 |
| TR | Gebze Çolakoğlu power station | operating | 19.82 | 127.71 | 19.82 | buildable_area_inference | review | S3;S4 |
| TR | Gerze power station | cancelled | 137.19 | 24.7 | 137.19 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Gölovası power station | cancelled | 171.87 | 108.22 | 171.87 | buildable_area_inference | review | S8 |
| TR | Gönen power station | cancelled | 29.27 | 161.32 | 29.27 | buildable_area_inference | review | S3;S4;S8 |
| TR | Güney Akdeniz power station | cancelled | 46.27 | 8.33 | 46.27 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Güneybatı Anadolu power station | cancelled | 114.65 | 114.65 | 114.65 | contiguous_capped_inference | review | S3;S4;S8 |
| TR | Güreci power station | cancelled | 151.51 | 0 | 151.51 | buildable_area_inference | review | S7;S8 |
| TR | Gürmin Enerji Amasya power station | cancelled | 292.36 | 137.43 | 292.36 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | HEMA Amasra power station | cancelled | 11.35 | 1.17 | 11.35 | buildable_area_inference | review | S8 |
| TR | Habaş power station | cancelled | 87.42 | 88.67 | 87.42 | buildable_area_inference | review | S8 |
| TR | Hakan Enerji power station | cancelled | 171.87 | 93.71 | 171.87 | buildable_area_inference | review | S8 |
| TR | Hakan Kömür power station | cancelled | 19.4 | 241.5 | 19.4 | buildable_area_inference | review | S3;S4;S8 |
| TR | Hande power station | cancelled | 261.56 | 162.19 | 261.56 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Helvacı power station | cancelled | 165.65 | 44.74 | 165.65 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Ilgın power station | shelved | 313.95 | 291.93 | 313.95 | buildable_area_inference | review | S3;S4;S7 |
| TR | Irmak power station | cancelled | 1.58 | 0 | 1.58 | capacity_bounded_inference | review | S8 |
| TR | Iztek Ceyhan Komur power station | cancelled | 19.4 | 241.5 | 19.4 | buildable_area_inference | review | S8 |
| TR | Kahramanmaraş Anadolu power station | cancelled | 250 | 231.25 | 250 | buildable_area_inference | review | S8 |
| TR | Kandilli power station | cancelled | 7.23 | 1.99 | 7.23 | buildable_area_inference | review | S8 |
| TR | Kangal Etyemez power station | cancelled | 30.05 | 226.81 | 30.05 | buildable_area_inference | review | S8 |
| TR | Kangal power station | operating | 30.05 | 226.74 | 30.05 | buildable_area_inference | low | — |
| TR | Karaburun power station | cancelled | 36.4 | 0.36 | 36.4 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Karapinar Konya Şeker power station | cancelled | 312.24 | 243.52 | 312.24 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Kardemir Karabük Demir Çelik power station | operating | 19.41 | 18.14 | 19.41 | buildable_area_inference | low | — |
| TR | Kemerköy power station | operating | 42.17 | 14.48 | 42.17 | buildable_area_inference | low | — |
| TR | Kilikya power station | cancelled | 171.87 | 62.73 | 171.87 | buildable_area_inference | review | S8 |
| TR | Kipas MMP power station | operating | 268.7 | 163.91 | 268.7 | buildable_area_inference | review | S3;S4;S7 |
| TR | Kirazlıdere power complex | cancelled | 1.86 | 0 | 1.86 | capacity_bounded_inference | review | S7;S8 |
| TR | Kireçlik power station | cancelled | 3.82 | 0 | 3.82 | capacity_bounded_inference | review | S7;S8 |
| TR | Konya Karapınar power station | cancelled | 314.13 | 270.13 | 314.13 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Kütahya Domaniç power station | cancelled | 159.38 | 159.38 | 159.38 | favourable_envelope_inference | review | S8 |
| TR | Kınık power station | cancelled | 91.02 | 14.56 | 91.02 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Kıvanç power station | cancelled | 68.23 | 68.23 | 68.23 | favourable_envelope_inference | review | S8 |
| TR | Lüminer Enerji power station | cancelled | 12.8 | 0 | 12.8 | capacity_bounded_inference | review | S8 |
| TR | METES power station | cancelled | 138.8 | 11.1 | 138.8 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Meda power station | cancelled | 200.55 | 82.25 | 200.55 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Mersin Gülnar power station | cancelled | 54.2 | 54.2 | 54.2 | favourable_envelope_inference | review | S8 |
| TR | Mert power station | cancelled | 210.48 | 79.99 | 210.48 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Misis Adana power station | cancelled | 276.77 | 179.92 | 276.77 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Muğla power station | cancelled | 49.17 | 3.94 | 49.17 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Namal power station | cancelled | 151.51 | 0 | 151.51 | buildable_area_inference | review | S7;S8 |
| TR | Naren Karabiga power station | cancelled | 15.3 | 0 | 15.3 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Orhaneli power station | operating | 69.64 | 33.62 | 69.64 | buildable_area_inference | low | — |
| TR | Orta Anadolu power station | cancelled | 306.33 | 260.36 | 306.33 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Petkim power station | cancelled | 23.3 | 141.55 | 23.3 | buildable_area_inference | review | S8 |
| TR | Polat power station | operating | 11.03 | 164.05 | 11.03 | buildable_area_inference | low | — |
| TR | Saltukova power station | cancelled | 209.5 | 37.71 | 209.5 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Sanko Gölbaşı power station | cancelled | 304.63 | 91.38 | 304.63 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Sanko Yumurtalık power station | cancelled | 800.17 | 213.9 | 800.17 | buildable_area_inference | review | S8 |
| TR | Saray Tekirdağ power station | cancelled | 287.38 | 215.55 | 287.38 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Sarp Golvasi power station | cancelled | 297.11 | 231.74 | 297.11 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Sedef II TES power station | cancelled | 171.87 | 179.92 | 171.87 | buildable_area_inference | review | S8 |
| TR | Selena power station | cancelled | 35.18 | 47.88 | 35.18 | buildable_area_inference | review | S8 |
| TR | Seyitömer power station | operating | 67.42 | 128.62 | 67.42 | buildable_area_inference | low | — |
| TR | Silopi (Şırnak) power station | cancelled | 247.72 | 22.29 | 247.72 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Sinop Akfen power station | cancelled | 110.73 | 4.43 | 110.73 | buildable_area_inference | review | S7;S8 |
| TR | Soma Kolin power station | operating | 82.32 | 41.57 | 82.32 | buildable_area_inference | low | — |
| TR | Soma power station | operating | 215.06 | 96.8 | 215.06 | buildable_area_inference | review | S3;S4;S7 |
| TR | Star Refinery Socar power station | cancelled | 90.73 | 9.98 | 90.73 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Suluova power station | cancelled | 19.06 | 218.96 | 19.06 | buildable_area_inference | review | S8 |
| TR | Tekirdağ Malkara power station | shelved | 79.64 | 0.55 | 79.64 | contiguous_capped_inference | review | S3;S7 |
| TR | Teyo Tufanbeyli power station | cancelled | 273.94 | 273.94 | 273.94 | favourable_envelope_inference | review | S8 |
| TR | Tosyalı İskenderun power station | cancelled | 41.26 | 67.62 | 41.26 | buildable_area_inference | review | S8 |
| TR | Trakya Emba power station | cancelled | 24.38 | 0.49 | 24.38 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Tufanbeyli power station | operating | 311.98 | 143.52 | 311.98 | buildable_area_inference | review | S3;S4;S7 |
| TR | Tunçbilek power station | operating | 255.68 | 104.84 | 255.68 | buildable_area_inference | review | S3;S4;S7 |
| TR | Uluköy power station | cancelled | 303.64 | 112.33 | 303.64 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Umut power station | cancelled | 87.7 | 7.02 | 87.7 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Vize power station | cancelled | 104.05 | 15.6 | 104.05 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Yatağan power station | operating | 214.34 | 107.15 | 214.34 | buildable_area_inference | review | S3;S4;S7 |
| TR | Yenidere power station | shelved | 14.84 | 0.59 | 14.84 | buildable_area_inference | review | S3;S4;S7 |
| TR | Yeniköy power station | operating | 111.56 | 17.86 | 111.56 | buildable_area_inference | low | S7 |
| TR | Yeniyurt power station | cancelled | 72.33 | 13.01 | 72.33 | buildable_area_inference | review | S7;S8 |
| TR | Yeşilovacık power station | cancelled | 248.04 | 57.04 | 248.04 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Yumurtalık IC İçtaş power station | cancelled | 140.83 | 46.46 | 140.83 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Yunus Emre power station | operating | 299.77 | 164.89 | 299.77 | buildable_area_inference | review | S3;S4;S7 |
| TR | Yüksek Gölovası power station | cancelled | 297.11 | 231.74 | 297.11 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Yıldırım Elazığ power station | cancelled | 282.31 | 231.49 | 282.31 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | ZETES power stations | operating | 68.69 | 10.99 | 68.69 | buildable_area_inference | review | S3;S4;S7 |
| TR | Zafer power station | cancelled | 5.34 | 0 | 5.34 | capacity_bounded_inference | review | S7;S8 |
| TR | Zonguldak Modern power station | cancelled | 70.68 | 9.9 | 70.68 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Zorlu Akçakoca power station | cancelled | 147.65 | 31.02 | 147.65 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Zorlu Soma power station | cancelled | 283.65 | 153.14 | 283.65 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Çalışkan Ceyhan power station | cancelled | 35.9 | 102.79 | 35.9 | buildable_area_inference | review | S8 |
| TR | Çan (18 Mart) power station | operating | 81.2 | 0 | 81.2 | buildable_area_inference | low | — |
| TR | Çan-2 power station | operating | 28.48 | 0 | 28.48 | osm_polygon | medium | — |
| TR | Çankırı Orta power station | cancelled | 306.33 | 260.36 | 306.33 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Çankırı Yıldızlar power station | cancelled | 311.69 | 34.29 | 311.69 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Çatalağzı power station | operating | 20.71 | 17.76 | 20.71 | buildable_area_inference | low | — |
| TR | Çayırhan power station | operating | 28.73 | 178.92 | 28.73 | buildable_area_inference | low | — |
| TR | Çebi Enerji power station | cancelled | 64.35 | 265.18 | 64.35 | buildable_area_inference | review | S8 |
| TR | Çelikler Yumurtalık power station | cancelled | 224.66 | 89.88 | 224.66 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Çerkezköy power station | cancelled | 236.88 | 236.88 | 236.88 | favourable_envelope_inference | review | S8 |
| TR | Çoban Yıldız power station | operating | 230.66 | 269.1 | 230.66 | buildable_area_inference | low | — |
| TR | Çırpılar power station | cancelled | 204.99 | 36.9 | 204.99 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | İsken Sugözü power station | operating | 171.87 | 54.68 | 171.87 | buildable_area_inference | low | — |
| TR | İskenderun power station | cancelled | 254.8 | 152.88 | 254.8 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | İzdemir Enerji power station | operating | 11.75 | 134.05 | 11.75 | buildable_area_inference | low | — |
| TR | İÇDAŞ Bekirli power station | operating | 84.85 | 27.05 | 84.85 | buildable_area_inference | low | — |
| TR | İÇDAŞ Biga power station | operating | 11.38 | 59.42 | 11.38 | buildable_area_inference | review | S3;S4 |
| TR | Şevketiye Lapseki power station | cancelled | 254.45 | 0 | 254.45 | buildable_area_inference | review | S7;S8 |
| TR | Şırnak Galata power station | cancelled | 281.91 | 121.22 | 281.91 | buildable_area_inference | review | S3;S4;S7;S8 |
| TR | Şırnak Silopi (CİNER) power station | operating | 44.28 | 74.67 | 44.28 | buildable_area_inference | review | S3;S4 |
| UA | Burshtyn power station | mothballed | 250 | 38.83 | 250 | llm_web_observation | medium | S3;S4;S7 |
| UA | Cherkasy power station | operating | 183.43 | 99.04 | 183.43 | buildable_area_inference | review | S3;S4;S7 |
| UA | Chernihiv power station | retired | 119.42 | 23.88 | 119.42 | buildable_area_inference | review | S3;S4;S7 |
| UA | Darnytska power station | operating | 268.4 | 187.88 | 268.4 | buildable_area_inference | review | S3;S4;S7 |
| UA | Dobrotvir power station | mothballed | 215.13 | 77.44 | 215.13 | buildable_area_inference | review | S3;S4;S6;S7 |
| UA | Kalush power station | mothballed | 231.11 | 85.51 | 231.11 | buildable_area_inference | review | S3;S4;S7 |
| UA | Kramatorskaya power station | mothballed | 158.52 | 63.4 | 158.52 | buildable_area_inference | review | S3;S4;S7 |
| UA | Kryvorizka power station | mothballed | 456 | 48.2 | 456 | llm_web_observation | medium | S3;S4;S7 |
| UA | Kurakhov power station | retired | 297.76 | 205.48 | 138 | llm_web_observation | medium | S3;S4;S6;S7 |
| UA | Ladyzhyn power station | mothballed | 162 | 19.1 | 95.45 | buildable_area_inference | review | S3;S7 |
| UA | Luganskaya power station | mothballed | 139.53 | 18.14 | 139.53 | buildable_area_inference | review | S3;S4;S7 |
| UA | Myronivskyi power station | mothballed | 143.53 | 58.84 | 143.53 | buildable_area_inference | review | S3;S4;S6;S7 |
| UA | Prydniprovska power station | mothballed | 196 | 15.25 | 69.3 | buildable_area_inference | review | S3;S7 |
| UA | Slavyansk power station | mothballed | 99.13 | 15.86 | 99.13 | buildable_area_inference | low | S7 |
| UA | Starobesheve power station | operating | 160 | 16.61 | 79.12 | buildable_area_inference | review | S3;S7 |
| UA | Trypilska power station | mothballed | 281.3 | 50.46 | 281.3 | llm_web_observation | medium | S3;S7 |
| UA | Vuglegirska power station | mothballed | 288 | 55.51 | 168.19 | buildable_area_inference | review | S3;S4;S7 |
| UA | Zaporizhia power station | mothballed | 125 | 92.34 | 125 | llm_web_observation | medium | S3;S4;S7 |
| UA | Zmiivska power station | mothballed | 227 | 62.06 | 227 | llm_web_observation | medium | S3;S4;S7 |
| UA | Zuevskaya power station | operating | 237.45 | 54.6 | 237.45 | buildable_area_inference | review | S3;S4;S6;S7 |
| XK | Istok power station | cancelled | 203.25 | 62.99 | 203.25 | buildable_area_inference | review | S3;S4;S7;S8 |
| XK | Kosovo A power station | operating | 64 | 179.29 | 64 | llm_web_observation | high | S3;S4;S7 |
| XK | Kosovo B power station | operating | 283.64 | 181.5 | 57 | llm_web_observation | medium | S3;S4;S6;S7 |
| XK | Kosovo C power station | cancelled | 292.09 | 233.68 | 292.09 | buildable_area_inference | review | S3;S4;S7;S8 |

