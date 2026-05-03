# Per-Country Top-5 Site Candidates

_Reference SMR: NuScale VOYGR-6 | Scoring run: `score-214bab4e` | Sensitivity run: `sens-7b609bd0`_

## What this list is for

This document lists the top-5 candidate sites in each in-scope country, ranked mechanically against the NuScale VOYGR-6 reference envelope. The ranking sorts full-pass sites first (highest composite score, then highest Monte-Carlo top-10 % hit rate), then avoidance-flag sites by the same rule, then exclusionary-fail sites where a country has fewer than 5 ranked candidates. The columns mirror the GUI Results / Sites ledger so the table reads the same as the screen view: status uses the same Full pass / Avoidance flag / Hard-fail labels, the composite column shows the baseline value, and the MC band column shows the 5th–95th percentile range from the 10 000-iteration sensitivity run.

The intent is operational: this is the input for hand-picking which sites to advance to a full site profile in the next pass. You return a `sites = { Country: [Site1, Site2, ...] }` map of the candidates you want profiled and the next pass produces the per-site profile artefacts for each, on the same template as the Romania - Turceni prototype.

Countries with no exclusionary-pass site (Albania, Slovenia, Kosovo) are out of scope for this list and are handled in `consolidated_failure_section.md`. Within an eligible country, the table intentionally surfaces avoidance-flag and even hard-fail candidates when there are fewer than 5 fully clean sites; the status column makes the screening verdict explicit so you can decide whether the candidate is worth a profile or whether the slot stays empty.

## Per-country candidate tables

### Austria (AT)

_Country pool: 0 full pass, 6 avoidance flag, 2 hard-fail (8 total ranked)._

| #   | Site                      | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                         |
| --- | ------------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | ------------------------------------------------- |
| 1   | Timelkam power station    | Avoidance flag | 6.07      | 4.37 – 6.46 | A             | 100 %    | 66            | 1             | Avoidance flag on NS-02; band-A despite the flag. |
| 2   | Voitsberg power station   | Avoidance flag | 5.89      | 4.38 – 6.32 | D             | 6 %      | 330           | 2             | Avoidance flag on NS-02.                          |
| 3   | Riedersbach power station | Avoidance flag | 5.81      | 4.31 – 6.23 | D             | 19 %     | 220           | 3             | Avoidance flag on NS-02, NS-05.                   |
| 4   | Enns Power Station        | Avoidance flag | 5.51      | 4.17 – 5.98 | H             | 6 %      | 800           | 4             | Avoidance flag on HI-03, NS-05.                   |
| 5   | Duernrohr power station   | Avoidance flag | 5.42      | 4.13 – 5.89 | G             | 6 %      | 802           | 5             | Avoidance flag on HI-03, NS-05.                   |

### Bosnia and Herzegovina (BA)

_Country pool: 0 full pass, 6 avoidance flag, 5 hard-fail (11 total ranked)._

| #   | Site                          | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                         |
| --- | ----------------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | ------------------------------------------------- |
| 1   | Gacko Thermal Power Plant     | Avoidance flag | 5.97      | 4.24 – 6.46 | A             | 100 %    | 650           | 1             | Avoidance flag on NS-02; band-A despite the flag. |
| 2   | Banovici power station        | Avoidance flag | 5.38      | 4.04 – 5.88 | D             | 0 %      | 350           | 2             | Avoidance flag on NS-02.                          |
| 3   | Stanari Thermal Power Plant   | Avoidance flag | 5.16      | 3.94 – 5.74 | D             | 0 %      | 300           | 3             | Avoidance flag on NS-02.                          |
| 4   | Miljevina power station       | Avoidance flag | 5.01      | 3.89 – 5.50 | H             | 0 %      | 220           | 4             | Avoidance flag on NS-02.                          |
| 5   | Kamengrad Thermal Power Plant | Avoidance flag | 4.94      | 3.86 – 5.50 | H             | 0 %      | 430           | 5             | Avoidance flag on HI-01, NS-02, NS-05.            |

### Bulgaria (BG)

_Country pool: 0 full pass, 6 avoidance flag, 9 hard-fail (15 total ranked)._

| #   | Site                          | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                                |
| --- | ----------------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | -------------------------------------------------------- |
| 1   | Maritsa Iztok-2 power station | Avoidance flag | 6.03      | 4.35 – 6.42 | D             | 19 %     | 2,162         | 1             | Avoidance flag on HI-01.                                 |
| 2   | Bobov Dol power station       | Avoidance flag | 6.00      | 4.33 – 6.42 | D             | 25 %     | 1,030         | 2             | Avoidance flag on HI-01.                                 |
| 3   | Vidin Works power station     | Avoidance flag | 5.76      | 4.23 – 6.26 | A             | 100 %    | 120           | 3             | Avoidance flag on HI-01, NS-02; band-A despite the flag. |
| 4   | Lom Power Station             | Avoidance flag | 5.58      | 4.12 – 5.96 | H             | 0 %      | 400           | 4             | Avoidance flag on NS-02, NS-05.                          |
| 5   | Maritsa 3 power station       | Avoidance flag | 5.34      | 4.02 – 5.84 | H             | 0 %      | 120           | 5             | Avoidance flag on NS-02.                                 |

### Belarus (BY)

_Country pool: 0 full pass, 1 avoidance flag, 1 hard-fail (2 total ranked)._

| #   | Site                    | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                                |
| --- | ----------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | -------------------------------------------------------- |
| 1   | Lelchitsy power station | Avoidance flag | 5.43      | 3.98 – 5.87 | A             | 88 %     | 400           | 1             | Avoidance flag on NS-02, NS-05; band-A despite the flag. |
| 2   | Zelwa power station     | Hard-fail      | —         | —           | H             | 12 %     | 1,000         | —             | Exclusionary fail on NS-08.                              |

_Note: only 2 ranked candidate(s) available in this country._

### Czechia (CZ)

_Country pool: 0 full pass, 23 avoidance flag, 6 hard-fail (29 total ranked)._

| #   | Site                     | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                         |
| --- | ------------------------ | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | ------------------------------------------------- |
| 1   | Tusimice power station   | Avoidance flag | 6.09      | 4.37 – 6.47 | A             | 94 %     | 800           | 1             | Avoidance flag on HI-01; band-A despite the flag. |
| 2   | Pocerady power station   | Avoidance flag | 5.97      | 4.29 – 6.38 | C             | 75 %     | 1,000         | 2             | Avoidance flag on HI-01.                          |
| 3   | Ledvice power station    | Avoidance flag | 5.90      | 4.26 – 6.28 | B             | 94 %     | 990           | 3             | Avoidance flag on HI-01.                          |
| 4   | Chvaletice power station | Avoidance flag | 5.83      | 4.26 – 6.30 | C             | 75 %     | 820           | 4             | Avoidance flag on HI-01.                          |
| 5   | Melnik power station     | Avoidance flag | 5.74      | 4.19 – 6.20 | C             | 69 %     | 1,070         | 5             | Avoidance flag on HI-01.                          |

### Croatia (HR)

_Country pool: 1 full pass, 0 avoidance flag, 1 hard-fail (2 total ranked)._

| #   | Site                 | Status    | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                                |
| --- | -------------------- | --------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | -------------------------------------------------------- |
| 1   | Plomin power station | Full pass | 5.13      | 3.93 – 5.64 | A             | 100 %    | 842           | 1             | National rank-1 fully clear candidate; band-A stability. |
| 2   | Ploče power station  | Hard-fail | —         | —           | —             | —        | 800           | —             | Exclusionary fail on NH-02.                              |

_Note: only 2 ranked candidate(s) available in this country._

### Hungary (HU)

_Country pool: 2 full pass, 8 avoidance flag, 1 hard-fail (11 total ranked)._

| #   | Site                        | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                                |
| --- | --------------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | -------------------------------------------------------- |
| 1   | Mohacs power station        | Full pass      | 6.47      | 4.62 – 6.89 | A             | 100 %    | 1,200         | 1             | National rank-1 fully clear candidate; band-A stability. |
| 2   | Torony power station        | Full pass      | 6.01      | 4.34 – 6.40 | D             | 6 %      | 600           | 2             | Rank-2 fully clear candidate; band-D stability.          |
| 3   | Borsod power station        | Avoidance flag | 5.98      | 4.39 – 6.40 | C             | 56 %     | 420           | 3             | Avoidance flag on HI-03, NS-02.                          |
| 4   | Tiszapalkonya power station | Avoidance flag | 5.81      | 4.31 – 6.30 | D             | 0 %      | 265           | 4             | Avoidance flag on HI-03, NS-02.                          |
| 5   | Matra power station         | Avoidance flag | 5.12      | 3.99 – 5.51 | H             | 0 %      | 1,384         | 5             | Avoidance flag on HI-01, HI-03, NS-05.                   |

### Latvia (LV)

_Country pool: 0 full pass, 1 avoidance flag, 0 hard-fail (1 total ranked)._

| #   | Site                  | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                                       |
| --- | --------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | --------------------------------------------------------------- |
| 1   | Kurzeme power station | Avoidance flag | 5.82      | 4.32 – 6.28 | A             | 100 %    | 435           | 1             | Avoidance flag on HI-01, NS-02, NS-05; band-A despite the flag. |

_Note: only 1 ranked candidate(s) available in this country._

### Moldova (MD)

_Country pool: 0 full pass, 1 avoidance flag, 0 hard-fail (1 total ranked)._

| #   | Site                    | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                         |
| --- | ----------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | ------------------------------------------------- |
| 1   | Kuchurgan power station | Avoidance flag | 5.66      | 4.07 – 6.15 | A             | 100 %    | 1,400         | 1             | Avoidance flag on HI-01; band-A despite the flag. |

_Note: only 1 ranked candidate(s) available in this country._

### Montenegro (ME)

_Country pool: 0 full pass, 1 avoidance flag, 3 hard-fail (4 total ranked)._

| #   | Site                   | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                          |
| --- | ---------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | ---------------------------------- |
| 1   | Bar power station      | Avoidance flag | 4.44      | 3.59 – 4.82 | D             | 6 %      | 800           | 1             | Avoidance flag on NH-01, NS-05.    |
| 2   | Berane power station   | Hard-fail      | —         | —           | A             | 94 %     | 110           | —             | Exclusionary fail on EP-01.        |
| 3   | Maoce Power Station    | Hard-fail      | —         | —           | —             | —        | 500           | —             | Exclusionary fail on NH-02.        |
| 4   | Pljevlja power station | Hard-fail      | —         | —           | —             | —        | 479           | —             | Exclusionary fail on NH-02, NS-08. |

_Note: only 4 ranked candidate(s) available in this country._

### North Macedonia (MK)

_Country pool: 0 full pass, 3 avoidance flag, 1 hard-fail (4 total ranked)._

| #   | Site                   | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                                |
| --- | ---------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | -------------------------------------------------------- |
| 1   | Bitola power station   | Avoidance flag | 5.53      | 4.10 – 5.94 | A             | 100 %    | 699           | 1             | Avoidance flag on HI-01, NH-01; band-A despite the flag. |
| 2   | Negotino power station | Avoidance flag | 4.90      | 3.83 – 5.31 | H             | 0 %      | 300           | 2             | Avoidance flag on HI-01, NS-02, NS-05.                   |
| 3   | Oslomej power station  | Avoidance flag | 4.51      | 3.66 – 4.93 | H             | 0 %      | 254           | 3             | Avoidance flag on NH-01, NS-02.                          |
| 4   | Mariovo power station  | Hard-fail      | —         | —           | H             | 0 %      | 300           | —             | Exclusionary fail on NS-08.                              |

_Note: only 4 ranked candidate(s) available in this country._

### Poland (PL)

_Country pool: 2 full pass, 38 avoidance flag, 23 hard-fail (63 total ranked)._

| #   | Site                     | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                         |
| --- | ------------------------ | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | ------------------------------------------------- |
| 1   | Opole power station      | Full pass      | 6.58      | 4.67 – 7.08 | A             | 100 %    | 3,332         | 2             | Rank-2 fully clear candidate; band-A stability.   |
| 2   | Dolna Odra power station | Full pass      | 5.95      | 4.38 – 6.42 | B             | 88 %     | 1,792         | 8             | Rank-8 fully clear candidate; band-B stability.   |
| 3   | Polaniec power station   | Avoidance flag | 6.79      | 4.77 – 7.21 | A             | 100 %    | 1,882         | 1             | Avoidance flag on HI-01; band-A despite the flag. |
| 4   | Turów power station      | Avoidance flag | 6.33      | 4.45 – 6.83 | B             | 94 %     | 2,754         | 3             | Avoidance flag on HI-01.                          |
| 5   | Puchaczow power station  | Avoidance flag | 6.31      | 4.54 – 6.70 | B             | 100 %    | 800           | 4             | Avoidance flag on HI-01.                          |

### Romania (RO)

_Country pool: 3 full pass, 15 avoidance flag, 4 hard-fail (22 total ranked)._

| #   | Site                      | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                                |
| --- | ------------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | -------------------------------------------------------- |
| 1   | Turceni power station     | Full pass      | 6.35      | 4.49 – 6.73 | A             | 100 %    | 2,640         | 1             | National rank-1 fully clear candidate; band-A stability. |
| 2   | Rovinari power station    | Full pass      | 5.83      | 4.23 – 6.24 | D             | 38 %     | 1,920         | 2             | Rank-2 fully clear candidate; band-D stability.          |
| 3   | Braila power station      | Full pass      | 5.82      | 4.34 – 6.24 | B             | 94 %     | 850           | 3             | Rank-3 fully clear candidate; band-B stability.          |
| 4   | Romag Termo power station | Avoidance flag | 5.44      | 4.16 – 5.83 | D             | 12 %     | 1,065         | 4             | Avoidance flag on HI-03.                                 |
| 5   | Giurgiu power station     | Avoidance flag | 5.39      | 4.18 – 5.79 | D             | 0 %      | 150           | 5             | Avoidance flag on NS-02, RI-04.                          |

### Serbia (RS)

_Country pool: 0 full pass, 7 avoidance flag, 1 hard-fail (8 total ranked)._

| #   | Site                       | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                                |
| --- | -------------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | -------------------------------------------------------- |
| 1   | Kolubara A power station   | Avoidance flag | 5.65      | 4.15 – 6.06 | B             | 81 %     | 271           | 1             | Avoidance flag on NS-02.                                 |
| 2   | Kolubara B power station   | Avoidance flag | 5.50      | 4.09 – 5.92 | D             | 38 %     | 725           | 2             | Avoidance flag on NS-02.                                 |
| 3   | Morava power station       | Avoidance flag | 5.40      | 4.07 – 5.78 | A             | 81 %     | 120           | 3             | Avoidance flag on NS-02, NS-05; band-A despite the flag. |
| 4   | Kostolac power station     | Avoidance flag | 5.30      | 4.00 – 5.88 | D             | 19 %     | 1,360         | 4             | Avoidance flag on HI-01.                                 |
| 5   | Nikola Tesla power station | Avoidance flag | 5.28      | 4.01 – 5.74 | C             | 56 %     | 3,816         | 5             | Avoidance flag on HI-01, RI-04.                          |

### Slovakia (SK)

_Country pool: 1 full pass, 4 avoidance flag, 1 hard-fail (6 total ranked)._

| #   | Site                                  | Status         | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                         |
| --- | ------------------------------------- | -------------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | ------------------------------------------------- |
| 1   | Vojany I power station                | Full pass      | 5.57      | 4.03 – 5.98 | D             | 0 %      | 660           | 2             | Rank-2 fully clear candidate; band-D stability.   |
| 2   | Novaky power station                  | Avoidance flag | 6.22      | 4.29 – 6.59 | A             | 100 %    | 472           | 1             | Avoidance flag on HI-01; band-A despite the flag. |
| 3   | Trebisov power station                | Avoidance flag | 5.13      | 3.85 – 5.47 | H             | 0 %      | 885           | 3             | Avoidance flag on HI-01, NS-05.                   |
| 4   | Martinska power station               | Avoidance flag | 5.12      | 3.85 – 5.50 | H             | 0 %      | 32            | 4             | Avoidance flag on HI-01, NS-02, RI-04.            |
| 5   | U.S. Steel Kosice Works power station | Avoidance flag | 4.84      | 3.74 – 5.19 | H             | 0 %      | 208           | 5             | Avoidance flag on HI-01, NS-02, NS-05.            |

### Türkiye (TR)

_Country pool: 16 full pass, 90 avoidance flag, 40 hard-fail (146 total ranked)._

| #   | Site                          | Status    | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                                |
| --- | ----------------------------- | --------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | -------------------------------------------------------- |
| 1   | Konya Karapınar power station | Full pass | 6.52      | 4.32 – 6.92 | A             | 100 %    | 1,000         | 1             | National rank-1 fully clear candidate; band-A stability. |
| 2   | Akdeniz Enerji power station  | Full pass | 6.28      | 4.34 – 6.77 | A             | 100 %    | 1,600         | 3             | Rank-3 fully clear candidate; band-A stability.          |
| 3   | Yeşilovacık power station     | Full pass | 6.21      | 4.29 – 6.70 | A             | 100 %    | 1,254         | 6             | Rank-6 fully clear candidate; band-A stability.          |
| 4   | Eren-1 power station          | Full pass | 6.05      | 4.22 – 6.46 | A             | 100 %    | 490           | 8             | Rank-8 fully clear candidate; band-A stability.          |
| 5   | METES power station           | Full pass | 5.99      | 4.20 – 6.48 | B             | 100 %    | 2,000         | 11            | Rank-11 fully clear candidate; band-B stability.         |

### Ukraine (UA)

_Country pool: 11 full pass, 6 avoidance flag, 3 hard-fail (20 total ranked)._

| #   | Site                     | Status    | Composite | MC band     | National band | Top-10 % | Capacity (MW) | National rank | Rationale                                                |
| --- | ------------------------ | --------- | --------- | ----------- | ------------- | -------- | ------------- | ------------- | -------------------------------------------------------- |
| 1   | Zmiivska power station   | Full pass | 6.09      | 4.03 – 6.47 | B             | 94 %     | 2,270         | 1             | National rank-1 fully clear candidate; band-B stability. |
| 2   | Ladyzhyn power station   | Full pass | 5.99      | 4.20 – 6.48 | B             | 100 %    | 1,800         | 3             | Rank-3 fully clear candidate; band-B stability.          |
| 3   | Dobrotvir power station  | Full pass | 5.99      | 4.20 – 6.40 | D             | 31 %     | 1,110         | 2             | Rank-2 fully clear candidate; band-D stability.          |
| 4   | Burshtyn power station   | Full pass | 5.81      | 4.05 – 6.31 | D             | 6 %      | 3,166         | 5             | Rank-5 fully clear candidate; band-D stability.          |
| 5   | Kryvorizka power station | Full pass | 5.57      | 3.86 – 5.92 | D             | 0 %      | 2,925         | 7             | Rank-7 fully clear candidate; band-D stability.          |

## Status legend

- **Full pass** - site clears both the exclusionary and avoidance screens against the NuScale VOYGR-6 reference envelope.
- **Avoidance flag** - site clears the exclusionary screen but is flagged on at least one avoidance criterion (remediable through Stage 3 work or programme-level study).
- **Hard-fail** - site is removed at the exclusionary screen; included in the country list only when the country has fewer than 5 ranked candidates above this status, so the user can see what would otherwise be blank rows.

## National stability band reference

Bands A through H are computed from the 10 000-iteration Monte-Carlo audit of the full criterion-weight set:

- **A** - rank-stable under every weight set the audit considered.
- **B / C / D** - rank-stable under most weight sets; some perturbations move the site within the national top quartile.
- **E / F** - sensitive to weight choice; the site's national rank is volatile.
- **G / H** - rank-fragile; the site's position depends materially on the specific weight set.

## Criterion code reference

- **EP-01** Emergency Planning Feasibility
- **HI-01** Aircraft Crash
- **HI-03** Toxic/Gas Releases
- **NH-01** Seismic: Ground Motion
- **NH-02** Seismic: Surface Rupture
- **NS-02** Grid Connection
- **NS-05** Site Footprint Adequacy
- **NS-08** Ecological Sensitivity
- **RI-04** Population Density at EPZ Radii
