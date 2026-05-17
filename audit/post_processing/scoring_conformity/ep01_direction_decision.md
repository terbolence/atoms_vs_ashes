<!-- man_hours: 0.85 -->
# EP-01 direction decision — A / B / C

**Status: SUPERSEDED on 2026-05-16 by the exclusionary-sweep §O review.**

## 2026-05-16 supersession note

The Option B decision recorded below (2026-05-13) was a **no-op at the
engine layer**. During the exclusionary-sweep §O review for EP-01 we
discovered that the EP-01 hand-written `bands:` block was being
silently overridden by the spec-path compiler whenever the criterion
declared a `band_recipe` and the recipe pivot was resolvable:

```python
# src/atoms_vs_ashes/criterion_spec/compiler.py:168-177
if template.band_recipe is not None:
    pivot = _band_recipe_pivot(template, crit_overrides, smr_key)
    if pivot is not None:
        bands = derive_bands_from_recipe(template.band_recipe, ...)
        # ↑ replaces template.bands wholesale
```

EP-01's recipe (`kind: score_percent_higher_is_better, fail_code: E8`)
plus the E8 default value of 30 (via `threshold_metadata.yaml`)
yielded engine bands keyed off pivot 30:

| score range | engine condition (recipe) | hand-written YAML (FB-LL-12) |
| ---: | --- | --- |
| `[9, 10]` | `composite >= 82.5` | `composite >= 85` |
| `[7, 8]`  | `composite >= 65`   | `composite >= 70` |
| `[5, 6]`  | `composite >= 30`   | `composite >= 42` |
| `[3, 4]`  | `composite >= 22.5` | `composite >= 35` |
| `[1, 2]`  | `composite >= 15`   | `composite >= 30` |
| `[0, 0]`  | `composite < 15`    | `composite < 30`  |

At Timelkam (composite ≈ 44) the **engine** therefore returned 5.5 — the
canonical reviewer #112 expectation — because composite 44 falls into the
recipe band `[5, 6]` (`>= 30`), not because of the FB-LL-12 edit. The
FB-LL-12 edit changed the YAML descriptor text but not the runtime score
at Timelkam (it would have agreed to within a small margin since both
ladders accept composite 44 at `[5, 6]`).

The cohort-level "33 of 361 sites shift up one band" claim should also be
re-read as documentation drift, not an engine-behaviour delta — the
recipe-derived ladder had been live for the entire window between the
recipe being wired and the 2026-05-16 sweep, so the cohort was already
banded according to the recipe ladder when the FB-LL-12 replay was run.

## 2026-05-16 resolution (Option A in the exclusionary-sweep chat)

User signed off on "embrace the recipe":

- Hand-written EP-01 bands in both
  `config/scoring_specs/ep_emergency_planning.yaml` and
  `config/scoring_rubrics/ep_emergency_planning.yaml` are now rewritten
  to mirror what the recipe derives (`>= 82.5 / 65 / 30 / 22.5 / 15 / < 15`),
  closing the silent-shadowing trap and aligning the spec-path and
  rubric-path engine outputs.
- `band_recipe.score5_pivot: 30` is now explicit on the recipe so the
  pivot is self-documenting (no need to chase the value through
  `threshold_metadata.yaml`).
- E8 opts in to `derive_expr_from_recipe: true` and carries
  `pass_mark: 5.0`; the drift guard now locks the E8 exclusion
  expression (`ep01_composite_score < 30`) to the same pivot the bands
  use. Any future single-knob edit moves bands, exclusion expression,
  and safety-floor pass-mark together.
- The wider drift class (any criterion that declares both `band_recipe`
  and hand-written `bands:`) is tracked under IMPROVEMENTS.md IMP-0003
  for HI-02 / HI-03 / HI-06 / NH-01 / NH-08 / NH-09 / NH-11 audit, and
  IMP-0006 for the validator-side fix.

For the audit trail of this decision see
`audit/conversations/2026-05-16_ep01-exclusionary-sweep-band-recipe.md`
and `experts/quality/lessons_learned.md::LL-035`.

---
*Original 2026-05-13 Option B decision and A/B/C options preserved below
for the record — but read them through the supersession note above.*

## Context

Reviewer comment #112 (Timelkam) expected the EP-01 score to **rise**
relative to the canonical May-2 value of 5.5. After the SP-D rubric
tightening (removal of the implicit 5.5 default and the introduction of
the 5/4/3/2/1 ladder at the 55/40/30 composite-score breakpoints), the
Timelkam EP-01 score **dropped** to 3.5 — the direction opposite to the
reviewer's expectation.

Current rubric (`ep_emergency_planning.yaml` lines 17–23):

```yaml
bands:
  - [9, 10]: ep01_composite_score >= 85
  - [7, 8]:  ep01_composite_score >= 70
  - [5, 6]:  ep01_composite_score >= 55
  - [3, 4]:  ep01_composite_score >= 40  ← Timelkam (composite ≈ 44) lands here
  - [1, 2]:  ep01_composite_score >= 30
  - [0]:     ep01_composite_score < 30 or nearest_trauma_center_km > 60
fail_conditions:
  - E8: exclude, ep01_composite_score < 30 or nearest_trauma_center_km > 60
```

Anchor evidence:

- Timelkam composite ≈ 44 → falls into `[3, 4]` (40–54 range) → score 3.5.
- Canonical May-2 run: 5.5 (under the legacy "default to 5.5 if no signal"
  rule that the SP-D rework explicitly removed).
- Reviewer #112 read 5.5 as too low and wanted higher; the new ladder
  moves the same composite to **lower** because composite 44 is closer to
  the E8 exclusion boundary (30) than to the project pass-mark (55).

## Options

### A. Accept the new direction (the SP-D ladder stands)

Keep the rubric as-is. The new ladder is **internally consistent** with
the composite-score generator and with the E8 exclusion boundary at 30.
Timelkam's 3.5 score is the rubric's honest answer for a composite of 44.

Document the divergence from reviewer #112 in
`report/output/feedback/responses/feedback_responses.md` and explain that
the canonical 5.5 was a defaulting artefact, not a quantitative finding.

Pros:
- Zero scoring change; no re-run cost.
- The current ladder is auditable end-to-end (no implicit defaults).
- Re-banding to satisfy a single anchor risks distorting the curve for
  the other 360 sites.

Cons:
- Reviewer #112 disagreement persists.
- Reads as "we tightened the rubric and it cost Timelkam".

### B. Soften the pass-mark to satisfy the reviewer's direction

Move the `[5, 6]` boundary down so a composite of 44 lands at or just
above 5. For example:

```yaml
- [5, 6]: ep01_composite_score >= 42
- [3, 4]: ep01_composite_score >= 35
- [1, 2]: ep01_composite_score >= 30
```

Pros:
- Timelkam moves from 3.5 to 5.5 (matches the canonical value the
  reviewer anchored to).
- Cohort-level impact contained: any composite in 42–55 rises by one band.

Cons:
- Cohort-level drift: 33 of 361 sites (≈ 9%) currently sit in the
  42–55 composite range and would shift up one band. The composite cohort
  median is in this window, so this is a non-trivial re-banding.
- The pass-mark boundary loses its alignment with the SP-D rebanding
  notes ("project pass-mark = composite ≥ 55"). The semantic anchor for
  what "passing the IAEA/CSF feasibility filter" means becomes weaker.

### C. Add a soft pass-mark via the LLM verdict / sub-band override

Keep the numeric ladder as-is but add a sub-band override that lets the
LLM verdict promote a borderline composite (40–54) one band when the
reviewer rationale is captured in the verdict text. For example:

```yaml
- {score_range: [5, 6], condition_expr: "ep01_composite_score >= 40 and llm_verdict_E8 == 'pass'", descriptor: "40-54 with LLM-verified feasibility narrative."}
- {score_range: [3, 4], condition_expr: "ep01_composite_score >= 40", descriptor: "40-54; numeric only."}
```

Pros:
- Preserves the numeric ladder for the cohort.
- Allows site-by-site escalation where a reviewer rationale supports it.
- Aligns with the EP-01 design intent (EP-01 is a composite that already
  blends numeric and qualitative signals).

Cons:
- Adds a new dependency on LLM verdict propagation.
- The `llm_verdict_E8 == 'pass'` predicate needs a defined contract: who
  writes it, when, and against which rubric.
- Risk of the LLM channel becoming a backdoor for ad-hoc score lifts.

## Recommendation (engineering view, non-binding)

Option **A** preserves the rubric's analytical integrity at the cost of
keeping the disagreement with reviewer #112 visible. Option **B** is the
"satisfy the reviewer" choice but reshuffles ~9% of the cohort. Option C
is the most principled but requires new pipework that this milestone may
not have time for.

## Decision required

User to choose **A**, **B**, or **C** (or "leave open, defer to SP-G"). No
edit lands until the user signs off. The recommended A also requires a
note in `feedback_responses.md` explaining the reasoning to the reviewer.
