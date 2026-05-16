<!-- man_hours: 0.4 -->
# Scoring Criteria System Prompt — Authoring Session

**Date:** 2026-05-16
**Session ID:** 2ceed5be-aa1c-4854-b9e2-16dd75d60005

## Objective

Distil the matrix-first review pattern proven on NH-03 into a reusable system prompt covering all 48 scoring criteria, then encode it as `prompts/ScoringCriteriaSystemPrompt.md` for future criterion review and amendment work.

The user requested the prompt explicitly handle:

- All four phase types (`basic_filter`, `exclusionary`, `avoidance`, `ranking`) and four fail-condition actions (`exclude`, `avoidance_penalty`, `screen_flag`, `review_flag`).
- End-to-end app-flow propagation from YAML through compiler / runtime / engine / preview / GUI / report docs.
- IAEA (SSR-1, SSG-9 / 18 / 21 / 35 / 79, NS-G-3.6, GSG-10) and EPRI 3002023910 four-step methodology validation.
- Action-driven UI popover labels (the screenshot-evidenced label dispatch between `Pass mark`, `Score boundary (mark 5)`, and `Flag threshold`).
- Specialist-prompt routing (architect, engineer, auditor, sitingExpert, IAEA/EPRI matrix author, runAPIs, lessons learned).

## Key Decisions

- **Matrix-first ritual is non-negotiable.** Encoded as a 10-step workflow (§D) that hard-blocks edits before user sign-off on the decision artifacts.
- **Four-artifact dispatcher** (§C3) replaces the NH-03-shaped single matrix. Each phase combo maps deterministically to a set of artifacts (truth table, score-curve boundary table, avoidance penalty sheet, basic-filter cutoff sheet, soft-flag register).
- **Phase-aware test contract, DB dry-run shape, and popover labels** — all dispatch off the same phase model so the system handles all 48 criteria without reshaping each.
- **EPRI ↔ phase ↔ action validation gate** (§H) catches phase-tier drift between code and `docs/expert_siting_criteria_evaluation_matrix.md`.
- **GUI popover placement correction (§I3) is explicitly out of scope** for any criterion change run — surfaced as a known backlog item requiring its own GUI-template-realignment plan.
- **NH-03 final state embedded as worked example** (§P) for calibration.

## Files Changed

- `prompts/ScoringCriteriaSystemPrompt.md` — new, 404 lines (under the 500-line markdown limit).
- `audit/man_hours_registry.yml` — added `prompts/ScoringCriteriaSystemPrompt.md` at 8.0 h, AI Prompts & Tooling.
- `audit/man_hours_summary.md` — regenerated (432 files, 1566.5 h total).
- `audit/conversations/2026-05-16_scoring-criteria-system-prompt.md` — this log.

## Outcome

Completed. The prompt is ready to use; no follow-up actions required.

The recommended next step (when the user is ready) is to exercise the prompt on a non-NH-03 phase combo — e.g., pick an `[avoidance, ranking]` criterion (HI-01, NH-08) or a pure `[ranking]` one (NH-10, RI-02) — to confirm the dispatcher / artifact specs hold up in practice and to harvest any first-use lessons into `prompts/lessons_learned.md`.
