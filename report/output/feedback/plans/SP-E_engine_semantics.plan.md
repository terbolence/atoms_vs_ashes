<!-- man_hours: 2.5 -->
---
sub_plan: SP-E
title: Missing-evidence fallback semantics in scoring engine + renderer
specialist_prompts:
  primary: prompts/seniorSoftwareEngineer.md
  supporting:
    - prompts/coal_to_nuclear_suitable_sites_scoring_audit.md
    - prompts/softwareArchitect.md
mandatory_reads_first:
  - prompts/lessons_learned.md
  - report/output/feedback/plans/feedback_lessons_learnt.md
  - src/atoms_vs_ashes/scoring/bands.py
  - src/atoms_vs_ashes/scoring/composite.py
  - src/scripts/_site_profile_markdown.py
honors_feedback_lessons: [FB-LL-01, FB-LL-02]
gates: [feedback_lessons_learnt.md sign_off]
comment_ids: [102, 105, 107, 108, 109, 117, 575, 580, 581, 583]
---

# SP-E — Missing-evidence fallback semantics

The renderer + engine must distinguish three cases that today all collapse to "score 5.x with `Evidence: values not in measurement tables`":

| Case | Score | Render shape | Composite participation |
| --- | --- | --- | --- |
| (a) Band matched, pass-mark band is the verdict | 5.5 (current) | "score 5.5/10 — pass-mark band matched: <descriptor>" | full weight |
| (b) No band matched (genuinely unscored) | None | "no native score (unscored — no band matched, evidence: <signals or 'absent'>)" | excluded; counted toward unscored fraction |
| (c) Low-hazard branch matched (favorable-by-default) | high (8-10) | "score 9.0/10 — favorable: <e.g. 'no airport within 30 km AND no military within 60 km'>" | full weight |

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
3. When the matched band carries a `descriptor` string, append it after the score: `score 9.0/10 — <descriptor>` so favorable matches read as favorable rather than ambiguous.

## Tests (pure-function before any rerun)

- Unit tests on `evaluate_bands`: no-match returns score=None; favorable-band match returns the band score; pass-mark band match returns the pass-mark midpoint.
- Snapshot test on `_family_section` for each of the three cases above.
- Integration test against a synthetic site bundle showing all three cases co-occurring in one family.

## Acceptance

- No site profile bullet anywhere asserts a numeric score on the same line as `Evidence: values not in measurement tables`.
- Composite scores correctly exclude None-score criteria from the weighted average.
- Existing tests pass; new tests cover the three cases.
- The `_site_profile_markdown.py` `--regenerate-fixtures` path produces deterministic markdown.

## Cross-links

- T3 in master plan.
- FB-LL-01 (favorable-default semantics), FB-LL-02 (no number with no evidence).
- Promoted-LL candidate "pass-mark midpoint asserts a numeric score with no evidence" (close-out todo).

## Out of scope

- Rubric edits (SP-D).
- Connector data fixes (SP-F) — silent false negatives that should be data instead of unscored.
