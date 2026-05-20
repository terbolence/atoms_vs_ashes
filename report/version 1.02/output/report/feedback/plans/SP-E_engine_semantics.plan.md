<!-- man_hours: 3.0 -->
---
sub_plan: SP-E
title: Missing-evidence fallback semantics in scoring engine + renderer
specialist_prompts:
  primary: experts/connectors/senior_software_engineer.md
  supporting:
    - experts/scoring/suitable_sites_scoring_audit.md
    - experts/connectors/software_architect.md
mandatory_reads_first:
  - experts/quality/lessons_learned.md
  - report/output/feedback/plans/feedback_lessons_learnt.md
  - src/atoms_vs_ashes/scoring/bands.py
  - src/atoms_vs_ashes/scoring/composite.py
  - src/scripts/_site_profile_markdown.py
honors_feedback_lessons: [FB-LL-01, FB-LL-02]
gates: [feedback_lessons_learnt.md sign_off]
comment_ids: [102, 105, 107, 108, 109, 117, 575, 580, 581, 583]
---

# SP-E — Missing-evidence fallback semantics

## Status (2026-05-09)

**Landed (renderer + acceptance tests).** Engine semantics for case (b) are unchanged because the existing flow (`evaluate_bands` returns score=5.0 + `notes=["unscored"]` -> `quality_flag_for` maps to `"unscored"` -> `composite.py` skips via `unscored_weight += w` and applies the pessimistic `UNSCORED_FALLBACK_SCORE = 3.0` envelope) was already meeting the FB-LL-01 / FB-LL-02 acceptance test before this stage. Switching `BandResult.score` to `Optional[float]` would have been an invasive refactor with no behavioural change at the composite level.

The renderer was the gap. Two production-path bugs fixed:

1. `_verdicts_and_scores_by_family` in `src/scripts/_site_profile_markdown.py` was not propagating `quality_flag` or the matched-band descriptor onto the per-criterion dict, so the unscored vs scored branch in `_family_section` was always dead code in production (only test stubs ever set `quality_flag`). It now reads `quality_flag` from the bundle's `ranking_scores` row and parses the matched-band descriptor out of `RankingScore.justification` JSON ("band" key, written by `_ranking_row.build_ranking_justification`).
2. `_family_section` now produces three distinct strings keyed off the score band:
   - **(a) pass-mark band match (4.5 <= score <= 6.5)**: appends `" - pass-mark band: <descriptor>"` after the score so the bullet labels itself rather than reading as an unqualified midpoint.
   - **(b) genuinely unscored** (existing): `"no native score (unscored - no band matched), ..., Evidence: not measured at this site (criterion remains unscored)"`.
   - **(c) favourable-by-default (score >= 8.0)**: appends `" - favourable: <descriptor>"` so high-band matches read as positive evidence rather than ambiguous high numbers.

Tests: 94 passed (89 scoring + 5 renderer; two new tests cover the favourable and pass-mark branches with descriptors). Engine itself is untouched; the SP-E pure-function intent is met by stricter renderer code paths and the descriptor plumbing.

The renderer + engine must distinguish three cases that today all collapse to "score 5.x with `Evidence: values not in measurement tables`":

| Case | Score | Render shape | Composite participation |
| --- | --- | --- | --- |
| (a) Band matched, pass-mark band is the verdict | 5.5 (current) | "score 5.5/10 — pass-mark band matched: <descriptor>" | full weight |
| (b) No band matched (genuinely unscored) | None | "no native score (unscored — no band matched, evidence: <signals or 'absent'>)" | excluded; counted toward unscored fraction |
| (c) Low-hazard branch matched (favourable-by-default) | high (8-10) | "score 9.0/10 — favourable: <e.g. 'no airport within 30 km AND no military within 60 km'>" | full weight |

Cases (a) and (c) come from rubric edits in SP-D. Case (b) is the engine + renderer change owned here.

## Engine changes ([`src/atoms_vs_ashes/scoring/bands.py`](../../../../src/atoms_vs_ashes/scoring/bands.py))

1. `evaluate_bands` returns `score=None` (Optional[float]) when no band matches AND no `default` band is present, instead of `score=5.0`. The `notes=["unscored"]` flag is retained.
2. The `BandResult` dataclass updates `score: Optional[float]`. All consumers must handle None.
3. [`src/atoms_vs_ashes/scoring/composite.py`](../../../../src/atoms_vs_ashes/scoring/composite.py) skips None-score criteria from the weighted average and increments `unscored_weight` accordingly. The existing `UNSCORED_FRACTION_WARN` / `UNSCORED_FRACTION_HARD` thresholds and `UNSCORED_FALLBACK_SCORE = 3.0` pessimistic logic continue to work.
4. The `quality_flag` for unscored remains `unscored`.

## Renderer changes ([`src/scripts/_site_profile_markdown.py`](../../../../src/scripts/_site_profile_markdown.py))

`_family_section()` (lines 312-355):

1. When `score is None`, emit `no native score (unscored — no band matched)` instead of `5.0/10 (MC 5.0-5.0)`.
2. When `signals` is empty, emit `Evidence: not measured at this site` (or similar) instead of `Evidence: values not in measurement tables`. The wording change is a credibility fix (FB-LL-02).
3. When the matched band carries a `descriptor` string, append it after the score: `score 9.0/10 — <descriptor>` so favourable matches read as favourable rather than ambiguous.

## Tests (pure-function before any rerun)

- Unit tests on `evaluate_bands`: no-match returns score=None; favourable-band match returns the band score; pass-mark band match returns the pass-mark midpoint.
- Snapshot test on `_family_section` for each of the three cases above.
- Integration test against a synthetic site bundle showing all three cases co-occurring in one family.

## Acceptance

- No site profile bullet anywhere asserts a numeric score on the same line as `Evidence: values not in measurement tables`.
- Composite scores correctly exclude None-score criteria from the weighted average.
- Existing tests pass; new tests cover the three cases.
- The `_site_profile_markdown.py` `--regenerate-fixtures` path produces deterministic markdown.

## Cross-links

- T3 in master plan.
- FB-LL-01 (favourable-default semantics), FB-LL-02 (no number with no evidence).
- Promoted-LL candidate "pass-mark midpoint asserts a numeric score with no evidence" (close-out todo).

## Out of scope

- Rubric edits (SP-D).
- Connector data fixes (SP-F) — silent false negatives that should be data instead of unscored.
