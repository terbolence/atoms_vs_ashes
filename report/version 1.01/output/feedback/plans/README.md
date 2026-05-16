<!-- man_hours: 0.3 -->
# Feedback rework — plans folder

This folder is the **co-located mirror** of the canonical feedback rework plans. The canonical copy lives at `~/.cursor/plans/feedback_rework_master_plan_73c0a8a8.plan.md`; the files here are working artefacts that sit next to the reviewer feedback they answer.

## Layout

| File / folder | Purpose | Gate |
| --- | --- | --- |
| `00_master.plan.md` | Master plan mirror (themes T1-T9, sub-plan dependency graph). | n/a |
| `feedback_lessons_learnt.md` | **Phase 0.4** synthesis of the 45 reviewer comments into 11 `FB-LL-*` lessons. | `sign_off: yes` required before SP-D YAML edits and SP-G rerun. |
| `SP-A_quick_wins.plan.md` | VOYGR-6 924->462, table captions, Romania count reconciliation, drop acks. | none |
| `SP-B_epri_weights.plan.md` | Add `epri` named weight profile alongside the current basis. | EPRI source document name from user. |
| `SP-C_methodology.plan.md` | Chapter 3 Stage 1/2 boundary + RI-04 dual mode. | depends on FB-LL sign-off. |
| `SP-D_rubric_bands.plan.md` | YAML edits per Phase 0.6 approved proposals. | **Phase 0.6 sign-off per criterion** required. |
| `SP-D_data_sanity/<criterion_id>.md` | **Phase 0.5** per-criterion data-cleanliness audit. | gate for routing into SP-D vs SP-F. |
| `SP-D_band_proposals/<criterion_id>.md` | **Phase 0.6** per-criterion proposed bands + regression matrix. | `sign_off: yes` per file. |
| `SP-E_engine_semantics.plan.md` | `bands.py` + `_site_profile_markdown.py` distinguish unscored vs favorable-by-default vs pass-mark. | depends on FB-LL sign-off. |
| `SP-F_connector_refinements.plan.md` | Airport class, military classification fields. | depends on FB-LL sign-off + live-API consent for re-enrichment. |
| `SP-G_rerun_regenerate.plan.md` | Full enrichment + scoring rerun + per-country/per-site bundle export. | live-API consent + all upstream sign-offs. |
| `SP-H_backlog.plan.md` | Reviewer comments deferred to a future iteration (#72) + engineering follow-ups. | n/a |

## How to read

1. Read [`feedback_lessons_learnt.md`](feedback_lessons_learnt.md) first.
2. Read [`00_master.plan.md`](00_master.plan.md) for the dependency graph.
3. Read the relevant `SP-*.plan.md` for the work you are about to execute.
4. Each sub-plan declares its `specialist_prompts:` and `mandatory_reads_first:` in YAML frontmatter — load those before substantive work per the always-on `specialized-system-prompt-routing.mdc` rule.

## Triage source of truth

The per-comment `category` / `subsystem` / `action` is in [`../synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml`](../synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml). Each sub-plan owns a subset of comment ids end-to-end.
