<!-- man_hours: 0.6 -->
# Ranking BF/NH Criteria Documentation

**Date:** 2026-05-16
**Session ID:** subagent-ranking-bf-nh-docs

## Objective
Document the accepted plan's ranking-criteria sweep for BF-02 and NH-01 through NH-14 under `criteria/ranking/`, using only local source-of-truth files and the local merged DB.

## Key Decisions
- Documentation-only run: no live API calls, enrichment runs, web calls, remote calls, scoring specs, rubrics, tests, or code were changed.
- Criteria with material current-behavior issues were marked `decision-needed` in their own files rather than presented as finalized.
- Current compiled scoring behavior from `config/scoring_specs/` was documented where it differs from hand-written rubric text.

## Files Changed
- `criteria/ranking/BF-02 — Land and nuclear-island footprint.md` — ranking-state documentation.
- `criteria/ranking/NH-01 — Seismic ground motion PGA.md` — ranking-state documentation.
- `criteria/ranking/NH-02 — Seismic surface rupture capable faults.md` — ranking-state documentation.
- `criteria/ranking/NH-03 — Geotechnical settlement and liquefaction.md` — ranking-state documentation.
- `criteria/ranking/NH-04 — Geotechnical slope stability.md` — ranking-state documentation.
- `criteria/ranking/NH-05 — Subsidence karst mining oil and gas.md` — ranking-state documentation.
- `criteria/ranking/NH-06 — Foundation conditions.md` — ranking-state documentation.
- `criteria/ranking/NH-07 — Volcanism.md` — ranking-state documentation.
- `criteria/ranking/NH-08 — Coastal flooding storm surge and tsunami.md` — ranking-state documentation.
- `criteria/ranking/NH-09 — River flooding.md` — ranking-state documentation.
- `criteria/ranking/NH-10 — Extreme winds.md` — ranking-state documentation.
- `criteria/ranking/NH-11 — Extreme precipitation rain snow and drought.md` — ranking-state documentation.
- `criteria/ranking/NH-12 — Extreme temperatures.md` — ranking-state documentation.
- `criteria/ranking/NH-13 — Forest and wildfire.md` — ranking-state documentation.
- `criteria/ranking/NH-14 — Combined hazards.md` — ranking-state documentation.
- `audit/man_hours_registry.yml` — man-hours entries for created/updated documentation.
- `audit/conversations/2026-05-16_ranking-bf-nh-criteria-docs.md` — conversation audit log.

## Outcome
Completed — 15 assigned ranking criterion docs were created or updated; decision-needed criteria are listed in their files and should be resolved before YAML/code changes.
