# Feedback artifacts

This folder is the working surface for reviewer feedback on the Atoms vs Ashes report. The original `.docx` is the carrier coming in from reviewers; everything else is generated and meant to drive iteration without re-reading the 750-page document.

## Contents

| File | Source | Purpose |
| --- | --- | --- |
| `atoms_vs_ashes_report_feedback.docx` | Reviewer | Original Word file with comment balloons. Not for direct reading by agents. |
| `atoms_vs_ashes_report_feedback_comments.json` | Generated | Machine-readable list of every comment with anchor + heading path. |
| `atoms_vs_ashes_report_feedback_comments.md` | Generated | Numbered, human-readable digest with `Where:` lines for triage. |
| `atoms_vs_ashes_report_feedback_triage.yaml` | Generated, **user-edited** | Per-comment triage scaffold. Idempotently merged on every regeneration. |

## Regenerate

```bash
python src/scripts/extract_docx_comments.py
```

Useful flags:

- `--no-anchors` — skip `word/document.xml` parsing (v1 behaviour: comments only).
- `--no-triage` — skip writing the triage scaffold.
- `--max-anchor-chars 400` — control truncation length.

The generator is split for clarity:

- [`src/scripts/extract_docx_comments.py`](../../../src/scripts/extract_docx_comments.py) — CLI orchestrator.
- [`src/scripts/_docx_comment_anchors.py`](../../../src/scripts/_docx_comment_anchors.py) — streaming `document.xml` parser.
- [`src/scripts/_docx_comment_triage.py`](../../../src/scripts/_docx_comment_triage.py) — heuristics + idempotent triage merge.
- [`src/scripts/_docx_comment_writers.py`](../../../src/scripts/_docx_comment_writers.py) — JSON + Markdown writers.

## Triage taxonomy

The triage scaffold uses a fixed vocabulary so the next plan can group comments deterministically.

### Categories (`category` field)

- `ack` — reviewer acknowledgement, no action required.
- `wording` — text/heading/table caption clarification.
- `scoring` — change to scoring formula or score interpretation.
- `weights` — change to swing weights or weighting methodology.
- `exclusionary` — exclusionary criterion semantics or thresholds.
- `sensitivity` — change to sensitivity analysis configuration or interpretation.
- `data` — missing or wrong data point, regardless of source.
- `connector` — change to a specific data connector or enrichment.
- `methodology` — methodological clarification in the report or in the engine.
- `clarification` — request for explanation only, may need wording tweak.

### Subsystems (`subsystem` field)

- `report-text` — chapter / annex / table caption changes only.
- `scoring-engine` — `src/atoms_vs_ashes/` analysis modules and config.
- `swing-weights` — weight definitions and audit pipeline.
- `sensitivity` — Phase 1.6 sensitivity scripts and figures.
- `data-connector` — connectors, enrichment runs, raw responses, verifiers.
- `methodology-doc` — IAEA mappings, screening logic narrative.
- `qa-cross-check` — cross-chapter consistency / numbers alignment.

The script also writes `auto.heuristic_category` and `auto.heuristic_subsystem` based on cheap keyword rules. Treat those as **suggestions**, not the ground truth — set the user-editable `category` and `subsystem` fields explicitly.

## Idempotent merge contract

When you re-run the extractor:

- `auto.*` blocks are refreshed from the latest `.docx`.
- `category`, `subsystem`, `action`, `depends_on`, `notes` are preserved per comment id.
- New ids are appended with empty user-editable fields.
- Comments removed from the source `.docx` are kept and tagged `auto.removed: true`, so review history is not lost.

Limitation: PyYAML does not preserve free-form comments. Inline notes belong in the `notes` field, not as YAML `# comments`, otherwise they will be dropped on regeneration.

## Downstream

Once the triage scaffold is filled in, the **next plan** consumes it to produce a master change plan and per-subsystem sub-plans, each owning a subset of comment ids end-to-end (logic change -> rerun -> rebuild report). Until then, treat `category` / `subsystem` / `action` as the authoritative routing layer.
