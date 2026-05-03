# Region-Wide Top-5 Site Recommendations

_Reference SMR: NuScale VOYGR-6 | Scoring run: `score-214bab4e` | Sensitivity run: `sens-7b609bd0`_

## Framing

This document ranks the five strongest brownfield coal-to-nuclear candidates across the 17 in-scope Central, Eastern, and Southern European countries that retain at least one exclusionary-pass site against the NuScale VOYGR-6 reference envelope. The ranking is mechanical: the top-5 are drawn from the union of every country's full-pass pool (`passed_exclusionary` AND `passed_avoidance`), sorted by baseline composite score and then by national top-10 % hit rate from the 10 000-iteration Monte Carlo audit. The list is a screening-stage shortlist: it identifies the sites where Stage 3 characterization would produce the largest near-term return on investment for the host country and the regional programme as a whole. It does not approve, license, or recommend procurement at any site, and it does not weigh national policy, vendor preference, or financing instruments.

A site that does not appear on this list is not deprecated; it may carry a binding national-programme rationale (a country's only viable lead, a strategic grid corridor, or a fast-follower role) that this region-wide cut does not reward. Country-level reads remain the right place to discuss those nuances.

Across the 17 in-scope countries, 36 brownfield sites pass both screens. The top 5 are concentrated in 5 different countries (Poland, Türkiye, Hungary, Romania, Türkiye), and all five sit in the band-A national stability bracket with a 100 % top-10 % hit rate. The second-tier watch list extends the candidate pool to capture the strongest sites that just missed the cut.

## Ranked top-5

| Rank | Site | Country | Composite (MC bracket) | National band | Top-10 % rate | Capacity (MW) | One-line rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Opole power station | Poland | 6.580 (4.672 - 7.075) | A | 100 % | 3 332 | Largest brownfield footprint in the region with the highest baseline composite, anchors Poland's two-site lead pool, dominant grid weight in southern Poland. |
| 2 | Konya Karapınar power station | Türkiye | 6.518 (4.317 - 6.918) | A | 100 % | 1 000 | Türkiye's national rank-1 brownfield candidate; band-A under every weight set the audit considered, leads the deepest brownfield pool in the region. |
| 3 | Mohacs power station | Hungary | 6.467 (4.619 - 6.887) | A | 100 % | 1 200 | Hungary's rank-1 fully clear candidate; the only Hungarian site with both band-A stability and an unqualified avoidance pass, anchors a credible two-site Hungarian programme. |
| 4 | Turceni power station | Romania | 6.347 (4.489 - 6.733) | A | 100 % | 2 640 | Romania's rank-1 fully clear candidate with the second-largest brownfield footprint in the top-5; the prototype site for the Atoms vs Ashes screening method, well-instrumented for Stage 3 sequencing. |
| 5 | Akdeniz Enerji power station | Türkiye | 6.280 (4.344 - 6.774) | A | 100 % | 1 600 | Türkiye's national rank-3 brownfield candidate; band-A and 100 % top-10 % rate, second-region anchor that geographically diversifies a Turkish fleet plan against the Konya Karapınar inland lead. |

## Second-tier watch list

These sites just missed the cut and are the natural fast-follower set if any of the top-5 fail to advance through Stage 3 characterization, or if a host country wishes to extend its national programme beyond the leader.

- **Yeşilovacık power station (Türkiye)** - composite 6.209 (4.286 - 6.703), band A, 100 % top-10 %, 1 254 MW. Deciding gap: virtually tied with Akdeniz Enerji on stability profile but slightly lower baseline composite; Türkiye-internal rank-6 against deep domestic competition.
- **Zmiivska power station (Ukraine)** - composite 6.086 (4.033 - 6.474), band B, 93.8 % top-10 %, 2 270 MW. Deciding gap: not band A, and the wartime grid and population context inflates the residual risk register beyond a near-term programme; treated separately under the occupied-territory caveat.
- **Eren-1 power station (Türkiye)** - composite 6.055 (4.225 - 6.462), band A, 100 % top-10 %, 490 MW. Deciding gap: the smallest brownfield footprint in the top-10 limits the grid-replacement weight relative to its higher-MW Turkish peers.
- **Torony power station (Hungary)** - composite 6.010 (4.339 - 6.396), band D, 6.3 % top-10 %, 600 MW. Deciding gap: rank-stable as Hungary's second fully clear candidate, but the band-D rank profile means the Stage 3 weight-set audit may demote it in some weight choices; remains the natural fast follower for Mohacs.
- **METES power station (Türkiye)** - composite 5.989 (4.198 - 6.484), band B, 100 % top-10 %, 2 000 MW. Deciding gap: large brownfield footprint and 100 % top-10 % rate but band B rather than band A; a strong third-wave Turkish candidate after Konya Karapınar, Akdeniz Enerji, and Yeşilovacık.

## What this list does and does not do

This shortlist is the input to the next step of work, not the output. The next pass produces full site profiles (snapshot, criterion-by-criterion data ledger, residual risk register, stability and sensitivity read) for each top-5 site, on the same template as the Romania - Turceni prototype. The watch-list sites become candidates for the second pass after the user reviews this list. Stage 3 characterization remains the right framework to confirm or refute every recommendation here.

The composite scores quoted above are baseline values from the canonical 10 000-iteration Monte Carlo run; the brackets are the 5th and 95th percentile composite scores from that run. The national stability bands and top-10 % hit rates use the same audit. All sites listed here are documented in their respective country profile and country bundle JSON for full traceability.
