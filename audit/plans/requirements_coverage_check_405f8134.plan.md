<!-- man_hours: 1.0 -->
<!-- Status: Completed — 2026-04-18 -->

# Requirements Coverage Check (Post-Processing Step 1)

## What we already know (from exploration)

**46 criteria** total: NH (14), HI (8), RI (6), EP (5), NS (13).

The LLM pipeline covers **all 46** (E1-E9 exclusionary, A1-A15 avoidance, 22+ ranking prompt keys). But its quality depends on API enrichment data — criteria with no API connector rely solely on the LLM's training knowledge.

**API connectors implemented and active: 27.** Coverage is strong for NH-01 through NH-13, HI-01 through HI-04, RI-01/03/04/05/06, NS-01 through NS-06, NS-08. Weak or absent for the rest.

## Methodology

Build a single **cross-reference matrix** by reading three input groups, then writing one output file.

### Inputs to read (read-only)

| #   | File                                                                                           | Purpose                                                     |
| --- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 1   | `requirements/agregated_requirements.md`                                                       | Master criterion list with phases and data sources          |
| 2   | `requirements/05_siting_criteria.md` + 05_1 through 05_5                                       | Detailed criterion definitions, thresholds, exclusion rules |
| 3   | `requirements/07_data_requirements.md`                                                         | Required databases per data category                        |
| 4   | `requirements/06_scoring_matrix.md`                                                            | Which criteria have scoring bands defined                   |
| 5   | `src/atoms_vs_ashes/connectors/__init__.py`                                                    | Active connector list                                       |
| 6   | `src/atoms_vs_ashes/db/models.py`                                                              | DB columns per criterion                                    |
| 7   | LLM orchestrator + prompt keys (already explored)                                              | LLM tier coverage                                           |

### Output

**One file:** `audit/post_processing/01_requirements_coverage/20260418_gaps.md`

## Execution notes

- All 6 todos completed on 2026-04-18.
- Gap analysis produced: 23 full, 13 partial, 10 none API coverage. 6/46 scoring bands defined, 40 missing.
- 8 action items (R-01 through R-06, F-01, F-02) added to `requirements/13_data_post_processing.md` §1.1.
- Scoring-band blocker flagged for §4 prerequisites.
