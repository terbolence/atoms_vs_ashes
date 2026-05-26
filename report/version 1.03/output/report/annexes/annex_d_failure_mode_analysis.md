<!-- man_hours: 4.1 -->

# Annex D: Failure-Mode Analysis

**What this annex adds.** Annex D carries the failure-mode breakdown for the NuScale VOYGR-6 reference case. Chapter 4 Section 4.4 summarises the dominant exclusion drivers, while Chapter 5 interprets country and site consequences. This annex gives the supporting counts, mechanism split, and compound-failure distribution.

## Population and survivorship

The analysis covers the full local candidate universe for the NuScale VOYGR-6 reference case. Each row corresponds to one site evaluation. Of 363 site evaluations, 26 survive every exclusionary gate and every safety floor. The remaining 337 are excluded before any composite ranking or national sensitivity conclusion is stated.

| Outcome             | Site evaluations | Share of universe |
| ------------------- | ---------------: | ----------------: |
| Survived every gate |               26 |             7.2 % |
| Failed any gate     |              337 |            92.8 % |
| Universe            |              363 |           100.0 % |

Safety-floor activity dominates the exclusion picture. About 91 per cent of failed evaluations are caught by the safety floor, either alone or together with a hard-expression trigger on the same criterion.

## Per-criterion failure breakdown

The counts below are unique site-evaluation counts. A site that fails the same criterion by both the hard expression and the safety floor is counted once in the `Hard and floor` column, not twice. The `Share of failures` column expresses each criterion's contribution against the 337 failed evaluations; percentages sum to more than 100 per cent because some sites fail on several criteria.

| Criterion | Name                                      | Hard fails | Floor fails | Hard and floor | Total failed | Share of failures |
| --------- | ----------------------------------------- | ---------: | ----------: | -------------: | -----------: | ----------------: |
| EP-01     | Emergency-plan feasibility                |         57 |         210 |              0 |          267 |            79.2 % |
| NH-04     | Geotechnical, slope stability             |          3 |         161 |              0 |          164 |            48.7 % |
| NH-05     | Subsidence, karst, mining, oil and gas    |        100 |         103 |             99 |          104 |            30.9 % |
| NH-02     | Seismic surface rupture                   |         50 |          38 |              0 |           88 |            26.1 % |
| NS-08     | Ecological sensitivity                    |          0 |           4 |              0 |            4 |             1.2 % |
| NH-03     | Geotechnical, settlement and liquefaction |          0 |           1 |              0 |            1 |             0.3 % |

Emergency-planning feasibility is the most frequent failure driver. Slope stability is the second driver and is almost entirely a safety-floor issue. Subsidence and karst carry the highest share of compound hard-and-floor failures because the geological indicators tend to co-activate. Surface-rupture screening remains a material filter. Ecological sensitivity and settlement-liquefaction together account for less than 2 per cent of the failed evaluations.

## Per-country failure breakdown

The table below gives survival rate, hard-only, floor-only, and compound counts by country. ISO codes follow ISO 3166-1 alpha-2. Survival rate is the share of sites within the country that cleared every exclusionary gate.

| ISO            | Country                                  | Sites | Survived | Survival rate | Hard only | Hard and floor | Floor only | Sites with at least one survivor |
| -------------- | ---------------------------------------- | ----: | -------: | ------------: | --------: | -------------: | ---------: | -------------------------------: |
| TR             | Türkiye                                  |   146 |       15 |        10.3 % |        14 |             26 |         91 |                               15 |
| PL             | Poland                                   |    63 |        4 |         6.3 % |         8 |             20 |         31 |                                4 |
| CZ             | Czechia                                  |    29 |        0 |         0.0 % |         0 |             29 |          0 |                                0 |
| RO             | Romania                                  |    24 |        4 |        16.7 % |         3 |              3 |         14 |                                4 |
| UA             | Ukraine                                  |    20 |        0 |         0.0 % |         0 |             18 |          2 |                                0 |
| BG             | Bulgaria                                 |    15 |        0 |         0.0 % |         1 |              7 |          7 |                                0 |
| BA             | Bosnia and Herzegovina                   |    11 |        0 |         0.0 % |         0 |             11 |          0 |                                0 |
| HU             | Hungary                                  |    11 |        0 |         0.0 % |         0 |             11 |          0 |                                0 |
| AT             | Austria                                  |     8 |        0 |         0.0 % |         0 |              2 |          6 |                                0 |
| RS             | Serbia                                   |     8 |        2 |        25.0 % |         1 |              2 |          3 |                                2 |
| SK             | Slovakia                                 |     6 |        0 |         0.0 % |         0 |              6 |          0 |                                0 |
| ME             | Montenegro                               |     4 |        0 |         0.0 % |         0 |              3 |          1 |                                0 |
| MK             | North Macedonia                          |     4 |        0 |         0.0 % |         0 |              0 |          4 |                                0 |
| XK             | Kosovo                                   |     4 |        0 |         0.0 % |         2 |              2 |          0 |                                0 |
| SI             | Slovenia                                 |     3 |        0 |         0.0 % |         0 |              3 |          0 |                                0 |
| Outside roster | Country outside current published roster |     2 |        1 |        50.0 % |         0 |              0 |          1 |                                1 |
| HR             | Croatia                                  |     2 |        0 |         0.0 % |         0 |              2 |          0 |                                0 |
| AL             | Albania                                  |     1 |        0 |         0.0 % |         0 |              1 |          0 |                                0 |
| LV             | Latvia                                   |     1 |        0 |         0.0 % |         0 |              0 |          1 |                                0 |
| MD             | Moldova                                  |     1 |        0 |         0.0 % |         0 |              1 |          0 |                                0 |

The country view shows that surviving sites concentrate in Türkiye, Poland, Romania, Serbia, and one country outside the current published roster within the local failure artefact. Published country-profile treatment remains controlled by Chapter 5 scope decisions and the current report roster; this annex is a methodology audit surface rather than a country-selection instruction.

## Compound versus single-criterion failures

A failed site can be caught by several exclusionary criteria at the same time. The distribution below counts the number of distinct criteria that fail for each excluded evaluation.

| Distinct criteria failed | Site evaluations | Share of failed |
| -----------------------: | ---------------: | --------------: |
|                        1 |              141 |          41.8 % |
|                        2 |              115 |          34.1 % |
|                        3 |               68 |          20.2 % |
|                        4 |               12 |           3.6 % |
|                        5 |                1 |           0.3 % |

About 42 per cent of exclusions are single-criterion and about 58 per cent are compound. Compound exclusions matter because a single-criterion fail can sometimes be re-examined with targeted Stage 3 evidence, whereas multi-criterion fails more often signal a systemic site-suitability problem.

## Hard-expression versus safety-floor split

The project rubric treats a criterion as hard when the exclusionary expression triggers and as a floor when the 0-10 ranking score sits below the criterion pass mark of 5.0. For the NuScale VOYGR-6 reference case, the split across failed evaluations is:

| Mechanism                                 | Site evaluations |
| ----------------------------------------- | ---------------: |
| Hard expression only                      |               29 |
| Safety floor only                         |              161 |
| Both hard and floor on the same criterion |              147 |

The dominance of the safety-floor path confirms that most exclusions are caused by screening scores below the minimum acceptable band on critical criteria. This is the behaviour the dual gate is designed to produce: critical weaknesses remove a site from ranking even when a single value does not cross the strongest hard-expression threshold.

## Reading the annex with the main body

Chapter 4 Section 4.4 names the top exclusion drivers and interprets their screening significance. Chapter 5 carries the country and site narrative for candidates that remain in scope. Annex D adds the count basis, mechanism split, and compound-failure distribution. A reviewer can trace a disputed failure through the mechanism in this annex, the threshold rule in Annex B, and the evidence limitations in Annex E.

## Evidence basis

This annex is drawn from the generated NuScale VOYGR-6 failure-mode artefact and the exclusionary-floors artefact listed in Annex F.
