<!-- man_hours: 3.4 -->
# Annex F: Generated Methodology Artefacts

**What this annex adds.** Annex F identifies the controlled methodology artefacts that support Chapters 2, 3, 4, 6 and Annexes A-E. It gives a publication-safe reproducibility map without exposing internal repository paths, command names, or working identifiers. Exact file locations and regeneration commands are retained in the internal audit copy.

## Controlled Artefact Index

| Controlled artefact | Report use | Publication control |
| --- | --- | --- |
| IAEA SSR-1 to project criterion traceability | Supports Annex A and the Chapter 1 methodology summary. | Must be regenerated when the criterion set or SSR-1 mapping changes. |
| Exclusionary thresholds and safety-floor rules | Supports Annex B and the Chapter 2-3 dual-gate description. | Must share the same rubric basis as the main scoring run. |
| National sensitivity method | Supports Chapter 3 Section 3.8, Chapter 4 Section 4.6, country profiles and Annex C. | Must use the 50,000-iteration national sensitivity basis inherited from version 1.2. |
| Failure-mode analysis | Supports Chapter 4 driver interpretation, Chapter 5 failure sections and Annex D. | Must be aligned to the NuScale VOYGR-6 reference case. |
| Swing-weight audit | Supports explanation of criteria that move national ranks most strongly. | Must be reviewed when criterion weights or observed score ranges change. |
| Criterion-correlation flag list | Supports checks for possible double-counting of related evidence axes. | Must be refreshed when scoring inputs or criteria are revised. |
| Project-wide assumption register | Supports Annex E and the treatment of uncertainty in Chapters 2, 4, 5 and 6. | Must be updated whenever the rubric or evidence hierarchy changes. |
| National sensitivity export pack | Supports score intervals, stability bands, and top-tier probabilities. | Must remain aligned with the published country and site profiles. |
| Scoring specifications and rubrics | Define criterion names, weights, thresholds, bands and evidence treatment. | Must remain frozen for the report version unless a controlled revision is opened. |
| Report layout specification | Defines the DOCX publication template, table treatment, heading levels and page rules. | Must be changed only through the report-format control process. |
| Publication assembly package | Combines chapters, Chapter 5 profiles, recommendation tables, failure sections and annexes. | Must strip internal comments and local file links from the assembled publication copy. |

## Reproducibility Notes

Each controlled artefact is derived from the same reconciled evidence base, scoring rubric and national sensitivity basis used in the report. Rerunning a generator without changing the rubric or evidence base should reproduce the same methodology output. Any change to a controlled artefact should be made together with the affected chapter, annex or profile so that the report does not mix analytical bases.

The publication assembly package is a consumer of the report source files. It assembles the front matter, Chapters 1-8, the Chapter 5 country and site profile sequence, the recommendation and failure sections, and Annexes A-F into a single publication manuscript. The assembly step also removes internal comments and local source links so that the reader-facing copy contains report language rather than file-system references.

## Human Review

Before camera-ready publication, the report owner should confirm four points:

1. The controlled artefacts all reflect the current frozen scoring rubric.
2. National sensitivity outputs use the 50,000-iteration national basis and are interpreted within country pools.
3. Annexes A-E cite the same controlled artefacts described here.
4. The internal audit copy retains exact paths, commands, and identifiers for reproducibility, while the published copy remains free of internal implementation details.
