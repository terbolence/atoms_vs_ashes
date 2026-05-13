#!/usr/bin/env python
# man_hours: 1.8
"""Build the Ovidiu-comment scoring conformity matrix.

Reads the canonical triage YAML
(``report/output/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml``)
and writes a per-comment conformity matrix (CSV + Markdown) under
``audit/post_processing/scoring_conformity/``.

The per-comment conformity status is assigned from the
``CONFORMITY_ASSIGNMENTS`` constant in this module, which is hand-curated
against the current state of the repository:

- rubric / spec YAMLs in ``config/scoring_rubrics`` and ``config/scoring_specs``;
- renderer code in ``src/scripts/_site_profile_markdown.py``;
- connector enrichment evidence in ``audit/post_processing/{hi01_preview,
  hi06_fix04_preview, sp_f_log_replay}``;
- the rework execution audit log
  (``audit/conversations/2026-05-09_feedback-rework-execution.md``).

Statuses
--------
- ``implemented``
- ``partially_implemented``
- ``deferred_by_reviewer_or_policy``
- ``not_implemented``
- ``not_applicable_ack``
- ``needs_clarification``

This is a local-only script. No network calls, no DB writes.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRIAGE_PATH = (
    PROJECT_ROOT
    / "report/output/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml"
)
OUT_DIR = PROJECT_ROOT / "audit/post_processing/scoring_conformity"

# --- Per-comment conformity classification -------------------------------------
# Keys are comment ids (strings) matching the triage YAML.
# Each value is a dict with:
#   status          : one of the six labels above.
#   themes          : list of master-plan T1..T9 themes.
#   fb_ll           : list of FB-LL ids that cover the comment.
#   sp              : list of SP-* sub-plan owners.
#   verdict_note    : 1-2 sentence rationale citing current evidence.
#   evidence_paths  : list of repo paths supporting the verdict.

CONFORMITY_ASSIGNMENTS: dict[str, dict[str, Any]] = {
    # --- Acknowledgements ------------------------------------------------------
    "8": {
        "status": "not_applicable_ack",
        "themes": [], "fb_ll": [], "sp": [],
        "verdict_note": "Acknowledgement ('OK') on §1.1 Purpose. No action required.",
        "evidence_paths": [
            "report/output/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml",
        ],
    },
    "12": {
        "status": "not_applicable_ack",
        "themes": [], "fb_ll": [], "sp": [],
        "verdict_note": "Acknowledgement ('OK') on §1.3 Coal-to-Nuclear Transition Context.",
        "evidence_paths": [
            "report/output/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml",
        ],
    },
    # --- Incomplete reviewer text ---------------------------------------------
    "15": {
        "status": "needs_clarification",
        "themes": [], "fb_ll": [], "sp": ["SP-A"],
        "verdict_note": "Reviewer text 'Take into account the' is incomplete; cannot act without full sentence.",
        "evidence_paths": [
            "report/output/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml",
        ],
    },
    # --- T4 / FB-LL-04: Stage 1 vs Stage 2 boundary ---------------------------
    "32": {
        "status": "implemented",
        "themes": ["T4"], "fb_ll": ["FB-LL-04"], "sp": ["SP-C"],
        "verdict_note": "Stage 4 of feedback-rework-execution rewrote §3.2 safety-as-controlling-constraint narrative and added SSR-1 clause-map reference.",
        "evidence_paths": [
            "report/output/chapters/03_stage_2_site_selection.md",
            "audit/conversations/2026-05-09_feedback-rework-execution.md",
        ],
    },
    "35": {
        "status": "implemented",
        "themes": ["T4"], "fb_ll": ["FB-LL-04"], "sp": ["SP-C"],
        "verdict_note": "Stage 1 vs Stage 2 boundary paragraph landed in chapter 3 §3.3 per the execution log.",
        "evidence_paths": [
            "report/output/chapters/03_stage_2_site_selection.md",
            "audit/conversations/2026-05-09_feedback-rework-execution.md",
        ],
    },
    # --- T4 / FB-LL-05: RI-04 dual-mode ---------------------------------------
    "33": {
        "status": "implemented",
        "themes": ["T4"], "fb_ll": ["FB-LL-05"], "sp": ["SP-C"],
        "verdict_note": "RI-04 dual-mode (avoidance/ranking OR exclusion when dose-feasibility fails) documented in rubric notes and chapter 3 §3.5.",
        "evidence_paths": [
            "config/scoring_rubrics/ri_radiological.yaml",
            "report/output/chapters/03_stage_2_site_selection.md",
        ],
    },
    "564": {
        "status": "implemented",
        "themes": ["T4"], "fb_ll": ["FB-LL-05"], "sp": ["SP-C"],
        "verdict_note": "EPZ-as-screening-vs-CNCAN-dose-feasibility documented in RI-04 rubric notes and methodology.",
        "evidence_paths": [
            "config/scoring_rubrics/ri_radiological.yaml",
            "report/output/chapters/03_stage_2_site_selection.md",
        ],
    },
    # --- T6 / SP-A wording fixes ----------------------------------------------
    "47": {
        "status": "implemented",
        "themes": ["T6"], "fb_ll": [], "sp": ["SP-A"],
        "verdict_note": "§4.1 'Sites in regional top 20' table caption added per Stage 1 closeout.",
        "evidence_paths": [
            "report/output/chapters/04_results_and_findings.md",
            "audit/conversations/2026-05-09_feedback-rework-execution.md",
        ],
    },
    "49": {
        "status": "implemented",
        "themes": ["T6"], "fb_ll": [], "sp": ["SP-A"],
        "verdict_note": "§4.2 'Per-Country Top Candidate Sites' caption added per Stage 1 closeout.",
        "evidence_paths": [
            "report/output/chapters/04_results_and_findings.md",
            "audit/conversations/2026-05-09_feedback-rework-execution.md",
        ],
    },
    "65": {
        "status": "implemented",
        "themes": ["T6"], "fb_ll": ["FB-LL-07"], "sp": ["SP-A"],
        "verdict_note": "Austrian Pareto caption labelled illustrative example (AT_country_prototype.md line 51).",
        "evidence_paths": [
            "report/output/chapters/05_country_and_site_profiles/AT_country_prototype.md",
            "audit/conversations/2026-05-09_feedback-rework-execution.md",
        ],
    },
    # --- T8 / FB-LL-10: deferred ----------------------------------------------
    "72": {
        "status": "deferred_by_reviewer_or_policy",
        "themes": ["T8"], "fb_ll": ["FB-LL-10"], "sp": ["SP-H"],
        "verdict_note": "Explicitly deferred by reviewer ('Nu acuma ci in versiunea ulterioara'); parked in SP-H backlog.",
        "evidence_paths": [
            "report/output/feedback/plans/SP-H_backlog.plan.md",
        ],
    },
    # --- T5 / FB-LL-03: connector sub-classification (HI-01 / HI-06) ----------
    "76": {
        "status": "partially_implemented",
        "themes": ["T5"], "fb_ll": ["FB-LL-03"], "sp": ["SP-F", "SP-D"],
        "verdict_note": (
            "SP-F enriched airport_class + runway_length_m (HI-01 preview is a no-op; data present). "
            "Rubric HI-01 still uses old AND-clause on nearest_airport_km / nearest_military_airfield_km; "
            "SP-D HI-01 v2 not yet authored to consume airport_class."
        ),
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
            "audit/post_processing/hi01_preview/hi01_preview_report.md",
            "report/output/feedback/plans/SP-F_connector_refinements.plan.md",
        ],
    },
    "79": {
        "status": "partially_implemented",
        "themes": ["T5"], "fb_ll": ["FB-LL-03"], "sp": ["SP-F", "SP-C"],
        "verdict_note": "Connector class fields enriched; the screening-radius wording in chapter 5 family interpretations may still need explicit reviewer-reconciled stance.",
        "evidence_paths": [
            "audit/post_processing/sp_f_log_replay/hi01_three_site_preview.md",
        ],
    },
    "106": {
        "status": "partially_implemented",
        "themes": ["T5", "T2"], "fb_ll": ["FB-LL-03"], "sp": ["SP-F", "SP-D"],
        "verdict_note": "airport_class field populated; HI-01 v2 bands not yet authored.",
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
            "audit/post_processing/sp_f_log_replay/hi01_three_site_preview.md",
        ],
    },
    "120": {
        "status": "partially_implemented",
        "themes": ["T5"], "fb_ll": ["FB-LL-03"], "sp": ["SP-F"],
        "verdict_note": (
            "OSM military classification enriched (nearest_military_class, nearest_high_consequence_military_km) "
            "and applied via fix04 replay. Rubric HI-06 still uses legacy `military_type` enum, so the new "
            "classification is stored but not read by the rubric."
        ),
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
            "audit/post_processing/hi06_fix04_preview/hi06_fix04_post_apply_verify.md",
        ],
    },
    "563": {
        "status": "partially_implemented",
        "themes": ["T5"], "fb_ll": ["FB-LL-03"], "sp": ["SP-F"],
        "verdict_note": "Same as #120; classification data landed for RO sites; rubric HI-06 not yet consuming it.",
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
            "audit/post_processing/hi06_fix04_preview/hi06_fix04_post_apply_verify.md",
        ],
    },
    "582": {
        "status": "partially_implemented",
        "themes": ["T5"], "fb_ll": ["FB-LL-03"], "sp": ["SP-F", "SP-D"],
        "verdict_note": "Brăila HI-06 classification data landed; rubric still scores from raw nearest_military_km.",
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
            "audit/post_processing/scoring_rerun_runbook/anchor_delta.md",
        ],
    },
    # --- T1 / FB-LL-09: EPRI weight basis -------------------------------------
    "77": {
        "status": "partially_implemented",
        "themes": ["T1"], "fb_ll": ["FB-LL-09"], "sp": ["SP-B", "SP-G"],
        "verdict_note": (
            "EPRI weights config landed (config/epri/weights.yaml) and rubric YAMLs carry baseline/epri "
            "per-criterion factors with weight_basis_source citations. The --weight-basis flag is wired in "
            "the scoring CLI. Site-profile renderer not confirmed to print the basis on each criterion bullet."
        ),
        "evidence_paths": [
            "config/epri/weights.yaml",
            "config/scoring_rubrics/hi_human_induced.yaml",
            "report/output/feedback/plans/SP-B_epri_weights.plan.md",
        ],
    },
    "1929454976": {
        "status": "partially_implemented",
        "themes": ["T1"], "fb_ll": ["FB-LL-09"], "sp": ["SP-B"],
        "verdict_note": (
            "EPRI named profile is implemented (config/epri/weights.yaml + rubric weight_factors.epri). "
            "Comment is from Bogdan Termegan, not Ovidiu Coman, but tracks the EPRI request that frames T1."
        ),
        "evidence_paths": [
            "config/epri/weights.yaml",
        ],
    },
    "117": {
        "status": "partially_implemented",
        "themes": ["T3", "T1"], "fb_ll": ["FB-LL-02", "FB-LL-09"], "sp": ["SP-D", "SP-E", "SP-B"],
        "verdict_note": (
            "Renderer no longer asserts a numeric score on the same line as 'values not in measurement tables' "
            "(SP-E acceptance landed). EPRI weight basis exists in config but per-criterion-bullet provenance "
            "in the rendered profile is not yet confirmed in the regenerated profiles."
        ),
        "evidence_paths": [
            "src/scripts/_site_profile_markdown.py",
            "tests/scripts/test_site_profile_unscored_rendering.py",
        ],
    },
    # --- T2 / FB-LL-01: rubric high-end favorable bands -----------------------
    "92": {
        "status": "implemented",
        "themes": ["T2"], "fb_ll": ["FB-LL-01"], "sp": ["SP-D"],
        "verdict_note": "NH-03 [7,8] now matches liquefaction_suscept == 'low' and [9,10] matches 'very_low'/'none'.",
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
        ],
    },
    "94": {
        "status": "implemented",
        "themes": ["T2"], "fb_ll": ["FB-LL-01"], "sp": ["SP-D"],
        "verdict_note": "NH-04 [9,10] now matches slope_angle_deg < 1; rubric uses on-site mean slope per LL-019.",
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
        ],
    },
    "95": {
        "status": "implemented",
        "themes": ["T2"], "fb_ll": ["FB-LL-01"], "sp": ["SP-D"],
        "verdict_note": "NH-05 [9,10] favorable branch includes mining_void_distance_km is null (absent evidence = favorable).",
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
        ],
    },
    "96": {
        "status": "implemented",
        "themes": ["T2"], "fb_ll": ["FB-LL-01"], "sp": ["SP-D"],
        "verdict_note": "Volcanism (NH-07 in rubric; reviewer called it NH-06) [9,10] now matches nearest_volcano_km > 1000 OR null.",
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
        ],
    },
    "97": {
        "status": "implemented",
        "themes": ["T2"], "fb_ll": ["FB-LL-01"], "sp": ["SP-D"],
        "verdict_note": "Coastal flooding (NH-08) [9,10] now includes country_is_landlocked == true favorable branch.",
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
        ],
    },
    "99": {
        "status": "implemented",
        "themes": ["T2"], "fb_ll": ["FB-LL-01"], "sp": ["SP-D"],
        "verdict_note": "River flooding (NH-09) [9,10] now matches flood_zone_class_500yr in ['none','negligible'] (rubric comment cites SP-F Ovidiu).",
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
        ],
    },
    "100": {
        "status": "not_implemented",
        "themes": ["T2"], "fb_ll": ["FB-LL-01"], "sp": ["SP-D"],
        "verdict_note": (
            "NH-11 still treats annual_precip 400-800 mm as the [9,10] band; low annual precipitation "
            "(e.g. Brăila 17 mm) scores low. extreme_precip_mm is declared as a db_field but not used in any sub-score band. "
            "Reviewer expected low extreme daily precipitation to be favorable. anchor_delta shows NH-11 unchanged at 4.0."
        ),
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
            "audit/post_processing/scoring_rerun_runbook/anchor_delta.md",
        ],
    },
    "101": {
        "status": "implemented",
        "themes": ["T2"], "fb_ll": ["FB-LL-01"], "sp": ["SP-D"],
        "verdict_note": "NH-13 [9,10] now matches combustible_veg_pct < 5 (no nearby forest = favorable).",
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
        ],
    },
    "573": {
        "status": "not_implemented",
        "themes": ["T2"], "fb_ll": ["FB-LL-01"], "sp": ["SP-D"],
        "verdict_note": "Same NH-11 limitation as #100; Brăila NH-11 score remained 4.0 in feedback_rerun_20260509.",
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
            "audit/post_processing/scoring_rerun_runbook/anchor_delta.md",
        ],
    },
    "574": {
        "status": "needs_clarification",
        "themes": ["T2"], "fb_ll": ["FB-LL-01", "FB-LL-11"], "sp": ["SP-D"],
        "verdict_note": "Reviewer references NuScale tornado cat IV on an NH-13 wildfire anchor; routed to SP-H clarification before re-banding (FB-LL-11).",
        "evidence_paths": [
            "report/output/feedback/plans/SP-H_backlog.plan.md",
        ],
    },
    "578": {
        "status": "not_implemented",
        "themes": ["T2"], "fb_ll": ["FB-LL-01", "FB-LL-08"], "sp": ["SP-D"],
        "verdict_note": (
            "Brăila HI-01 'no major airport within 30 km' must score favorable, but rubric HI-01 [9,10] still uses "
            "the AND-clause 'nearest_airport_km > 30 and nearest_military_airfield_km > 60'; missing military "
            "airfield data still drops the site to pass-mark. SP-D HI-01 v2 explicitly deferred pending SP-F."
        ),
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
            "report/output/feedback/plans/SP-D_rubric_bands.plan.md",
        ],
    },
    "579": {
        "status": "implemented",
        "themes": ["T2"], "fb_ll": ["FB-LL-01"], "sp": ["SP-D"],
        "verdict_note": "HI-02 [9,10] now matches nearest_seveso_km > 20 OR (null AND hi02_search_completed) - favorable when search completed and nothing found.",
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
        ],
    },
    # --- T3 / FB-LL-02: renderer / unscored semantics -------------------------
    "102": {
        "status": "implemented",
        "themes": ["T3"], "fb_ll": ["FB-LL-02"], "sp": ["SP-D", "SP-E"],
        "verdict_note": "NH-14 records 'unscored' when fewer than 5 underlying NH criteria resolved; renderer distinguishes unscored from pass-mark.",
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
            "src/scripts/_site_profile_markdown.py",
        ],
    },
    "105": {
        "status": "partially_implemented",
        "themes": ["T2", "T3"], "fb_ll": ["FB-LL-01", "FB-LL-02", "FB-LL-08"], "sp": ["SP-D", "SP-E"],
        "verdict_note": (
            "Renderer no longer asserts numeric score with 'values not in measurement tables' (SP-E landed). "
            "But the HI-01 high-band AND-clause (FB-LL-08) is NOT fixed; Timelkam HI-01 will still default to "
            "pass-mark when the favorable airport situation co-occurs with missing military airfield data."
        ),
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
            "src/scripts/_site_profile_markdown.py",
            "tests/scripts/test_site_profile_unscored_rendering.py",
        ],
    },
    "107": {
        "status": "implemented",
        "themes": ["T3"], "fb_ll": ["FB-LL-02"], "sp": ["SP-D", "SP-E"],
        "verdict_note": "HI-02 favorable-by-default branch landed; renderer distinguishes unscored / pass-mark / favorable.",
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
            "src/scripts/_site_profile_markdown.py",
        ],
    },
    "108": {
        "status": "implemented",
        "themes": ["T3"], "fb_ll": ["FB-LL-02"], "sp": ["SP-D", "SP-E"],
        "verdict_note": "HI-08 [9,10] now matches nearest_nuclear_km > 100 OR (null AND hi08_search_completed); renderer fix landed.",
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
            "src/scripts/_site_profile_markdown.py",
        ],
    },
    "109": {
        "status": "implemented",
        "themes": ["T3"], "fb_ll": ["FB-LL-02"], "sp": ["SP-D", "SP-E"],
        "verdict_note": "Same as #108; HI-08 favorable-by-default + renderer.",
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
        ],
    },
    "575": {
        "status": "implemented",
        "themes": ["T3"], "fb_ll": ["FB-LL-02"], "sp": ["SP-D", "SP-E"],
        "verdict_note": "Same as #102; NH-14 records unscored rather than numeric default when underlying data is sparse.",
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
        ],
    },
    "580": {
        "status": "implemented",
        "themes": ["T3"], "fb_ll": ["FB-LL-02"], "sp": ["SP-D", "SP-E"],
        "verdict_note": "HI-04 [9,10] now matches nearest_flammable_storage_km > 15 OR (null AND hi04_search_completed).",
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
        ],
    },
    "581": {
        "status": "implemented",
        "themes": ["T3"], "fb_ll": ["FB-LL-02"], "sp": ["SP-D", "SP-E"],
        "verdict_note": "HI-05 [9,10] now matches nearest_hazmat_corridor_km > 10 OR (null AND hi05_search_completed); SP-F sentinel rework.",
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
        ],
    },
    "583": {
        "status": "implemented",
        "themes": ["T3"], "fb_ll": ["FB-LL-02"], "sp": ["SP-D", "SP-E"],
        "verdict_note": "HI-08 favorable-by-default branch and renderer fix landed; same as #108/#109.",
        "evidence_paths": [
            "config/scoring_rubrics/hi_human_induced.yaml",
        ],
    },
    # --- EP-01 -----------------------------------------------------------------
    "112": {
        "status": "partially_implemented",
        "themes": ["T2"], "fb_ll": [], "sp": ["SP-D", "SP-C"],
        "verdict_note": (
            "EP-01 rubric was re-banded with new score thresholds (>=85, >=70, >=55, >=40, >=30) and signed off "
            "in Phase 0.6. Timelkam composite of 44 now maps to [3,4] rather than the old 5.5 pass-mark - i.e. "
            "the score actually moves further from the reviewer's expectation of 'higher than 5.5'. The rubric "
            "change addresses the structural concern (no default 5.5) but does not lift Timelkam's specific value."
        ),
        "evidence_paths": [
            "config/scoring_rubrics/ep_emergency_planning.yaml",
            "report/output/feedback/plans/SP-D_band_proposals/EP-01.md",
        ],
    },
    # --- T7 / FB-LL-06: VOYGR-6 capacity --------------------------------------
    "119": {
        "status": "implemented",
        "themes": ["T7"], "fb_ll": ["FB-LL-06"], "sp": ["SP-A"],
        "verdict_note": "All '924 MWe' / 'VOYGR-12' narrative removed from 7 site profiles; cross_chapter_numeric_lint.py guards regression.",
        "evidence_paths": [
            "src/scripts/cross_chapter_numeric_lint.py",
            "audit/conversations/2026-05-09_feedback-rework-execution.md",
        ],
    },
    "568": {
        "status": "implemented",
        "themes": ["T6"], "fb_ll": ["FB-LL-06"], "sp": ["SP-A"],
        "verdict_note": "Romania row in §4.1.1 reconciled with country-level full-pass count; cross_chapter_numeric_lint covers ROMANIA_FULL_PASS_RECONCILIATION.",
        "evidence_paths": [
            "report/output/chapters/04_results_and_findings.md",
            "src/scripts/cross_chapter_numeric_lint.py",
        ],
    },
    # --- BF-01 clarification (#565) -------------------------------------------
    "565": {
        "status": "partially_implemented",
        "themes": [], "fb_ll": [], "sp": ["Phase 0.5", "SP-C"],
        "verdict_note": (
            "BF-01 was removed from the composite per SP-F decision (rubric comment: 'BF-01 is no longer scored; "
            "NS-02 is the single grid-connection score'). The narrative implication of 'depends on how many "
            "modules' is partly addressed by the rubric note pointing to NuScale 77 MWe / VOYGR-6 462 MWe references, "
            "but no SMR-module-count modulation is explicit."
        ),
        "evidence_paths": [
            "config/scoring_rubrics/nh_natural_hazards.yaml",
        ],
    },
}


def _load_triage(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _ovidiu_items(triage: dict[str, Any]) -> list[dict[str, Any]]:
    items = triage.get("items", []) or []
    out: list[dict[str, Any]] = []
    for item in items:
        auto = item.get("auto") or {}
        author = (auto.get("author") or "").strip()
        if author.startswith("Ovidiu"):
            out.append(item)
    return out


def _bogdan_apex(triage: dict[str, Any]) -> dict[str, Any] | None:
    for item in triage.get("items", []) or []:
        if str(item.get("id")) == "1929454976":
            return item
    return None


def _row_for_item(item: dict[str, Any]) -> dict[str, Any]:
    cid = str(item.get("id"))
    auto = item.get("auto") or {}
    cls = CONFORMITY_ASSIGNMENTS.get(cid, {
        "status": "needs_clarification",
        "themes": [], "fb_ll": [], "sp": [],
        "verdict_note": "No conformity classification assigned.",
        "evidence_paths": [],
    })
    heading = " / ".join(auto.get("heading_path") or [])
    return {
        "comment_id": cid,
        "author": (auto.get("author") or "").strip(),
        "date": auto.get("date") or "",
        "chapter": auto.get("chapter") or "",
        "heading_path": heading,
        "anchor_excerpt": (auto.get("anchor_excerpt") or "").strip(),
        "reviewer_text": (auto.get("text_excerpt") or "").strip(),
        "triage_category": item.get("category") or "",
        "triage_subsystem": item.get("subsystem") or "",
        "triage_action": item.get("action") or "",
        "themes": ",".join(cls["themes"]),
        "fb_ll": ",".join(cls["fb_ll"]),
        "sp": ",".join(cls["sp"]),
        "conformity_status": cls["status"],
        "verdict_note": cls["verdict_note"],
        "evidence_paths": "; ".join(cls["evidence_paths"]),
    }


def _write_csv(rows: list[dict[str, Any]], out_path: Path) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_markdown(rows: list[dict[str, Any]], status_counts: dict[str, int], out_path: Path) -> None:
    lines: list[str] = []
    lines.append("<!-- man_hours: 0.0 -->")
    lines.append("# Ovidiu Coman comment conformity matrix")
    lines.append("")
    lines.append(
        "Per-comment conformity status against current repository state. "
        "Generated by `src/scripts/build_scoring_conformity_matrix.py`. "
        "Source: `report/output/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml`."
    )
    lines.append("")
    lines.append("## Status summary")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("| --- | ---: |")
    for status in (
        "implemented",
        "partially_implemented",
        "deferred_by_reviewer_or_policy",
        "not_implemented",
        "needs_clarification",
        "not_applicable_ack",
    ):
        lines.append(f"| {status} | {status_counts.get(status, 0)} |")
    lines.append("")
    lines.append(f"Total Ovidiu comments classified: {sum(status_counts.values())}.")
    lines.append("")
    lines.append("## Per-comment classification")
    lines.append("")
    lines.append(
        "| # | Theme | FB-LL | SP | Status | Reviewer (excerpted) | Verdict / evidence |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        excerpt = row["reviewer_text"].replace("\n", " ").replace("|", "/")
        if len(excerpt) > 100:
            excerpt = excerpt[:97] + "..."
        verdict = row["verdict_note"].replace("\n", " ").replace("|", "/")
        if row["evidence_paths"]:
            verdict = (
                f"{verdict} <br/> Evidence: "
                + ", ".join(f"`{p}`" for p in row["evidence_paths"].split("; "))
            )
        lines.append(
            f"| {row['comment_id']} | {row['themes'] or '-'} | {row['fb_ll'] or '-'} | "
            f"{row['sp'] or '-'} | {row['conformity_status']} | {excerpt} | {verdict} |"
        )
    lines.append("")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    triage = _load_triage(TRIAGE_PATH)
    ovidiu = _ovidiu_items(triage)
    bogdan_apex = _bogdan_apex(triage)

    items = list(ovidiu)
    if bogdan_apex is not None:
        items.append(bogdan_apex)

    rows = [_row_for_item(item) for item in items]
    rows.sort(key=lambda r: (int(r["comment_id"]) if r["comment_id"].isdigit() else 10**12, r["comment_id"]))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "ovidiu_comment_conformity.csv"
    md_path = OUT_DIR / "ovidiu_comment_conformity.md"

    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["conformity_status"]] = status_counts.get(row["conformity_status"], 0) + 1

    _write_csv(rows, csv_path)
    _write_markdown(rows, status_counts, md_path)

    print(f"Ovidiu comments classified: {len(ovidiu)}")
    if bogdan_apex is not None:
        print("Also included Bogdan apex comment #1929454976 (T1 EPRI seed).")
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print("Status counts:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
