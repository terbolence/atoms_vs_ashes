# Redundancy Inventory — Phase 5c

Surface inventory of structural overlap in the chapter, methodology and annex
markdown files. Each entry is classified against the six source-of-truth (SST)
rules declared in the master plan:

1. Canonical view discipline — one canonical artefact per data axis.
2. Pivots and filters, not duplicates — a different angle is a filter / sort
   over the canonical view with the filter named in the caption.
3. Single data source per table — every table footer names the bundle / ledger
   CSV it was rendered from.
4. Programmatic rendering — data tables are rendered from
   `data/*_bundle.json` / `*_ledger.csv` by a script.
5. Prose-citation discipline — prose cites the table rather than restating
   rows inline.
6. Chapter 4 vs Chapter 5 separation — Chapter 4 holds the regional view,
   Chapter 5 holds the per-country deep-dive; data lives in one home, not
   both.

Reviewer comments addressed by this inventory: `#54`, `#57`, `#70` (the three
explicit "redundant text / repeated tables" complaints) plus the structural
overlap that surfaces during a programmatic walk of the published prose.

Scope walked: 122 markdown files under
`report/version 1.03/output/report/chapters/`,
`report/version 1.03/output/report/annexes/`, and
`report/version 1.03/methodology/`. Programmatic table-signature scan ran
through `src/scripts/build_chapter_4_tables.py` siblings; 345 markdown
tables detected, 105 unique column signatures, 8 signatures spanning
≥ 2 files. The eight signatures are the spine of this inventory; the prose
findings are recorded by hand from the reviewer comments and the chapter
audit.

---

## A. Table-signature duplicates

### A.1 Per-site identity block (`field | value`)

- **Occurrences:** 66 files (every published site profile under
  `chapters/05_country_and_site_profiles/sites/`).
- **SST rule:** rule 4 (programmatic rendering).
- **Classification:** Not a redundancy. Each instance is a per-site
  identity table rendered from the site bundle JSON by
  `src/scripts/build_country_profile_prototype.py`. The canonical home is
  the bundle JSON; the table is a programmatic projection.
- **Decision:** Acceptable. No action required.

### A.2 Per-country ranked-site table (`rank | site | status | composite | mc low | mc high | band | top-10 hit | coverage`)

- **Occurrences:** 17 country prototypes
  (`chapters/05_country_and_site_profiles/{CC}_country_prototype.md`).
- **SST rule:** rules 2 + 4 + 6.
- **Classification:** Pivot view. Each country's table is a `(country_code, smr_key)`
  filter over the same canonical national-ledger CSV
  (`chapters/05_country_and_site_profiles/data/{CC}_site_ledger.csv`). The
  caption already names the country and SMR key. Programmatically rendered
  by `build_country_profile_prototype.py`. Chapter 4's Table 4.3.1 is the
  regional top-tier filter; Chapter 5 country profiles are the national
  filters. The two surfaces do not duplicate rows: Chapter 4 holds the
  regional view, Chapter 5 holds the national deep-dive.
- **Decision:** Acceptable. No action required.

### A.3 Failure-analysis glossary (`term | definition`)

- **Occurrences:** 9 methodology files
  (`methodology/failure_analysis.md` plus eight `failure_analysis_{smr}.md`
  variants).
- **SST rule:** rule 1.
- **Classification:** Real sibling redundancy. The eight SMR-specific
  variants repeat the global glossary instead of cross-referencing the
  canonical home.
- **Decision:** Declare `methodology/failure_analysis.md` as the canonical
  glossary home. The eight SMR-specific files keep their SMR-specific
  numbers and replace the glossary block with a one-line pointer to
  `methodology/failure_analysis.md`. Treatment scope: 8 files × ~10
  rows = 80 rows removed; one cross-reference link added per file.

### A.4 Failure-analysis criterion summary (`criterion | name | hard fails | floor fails | hard ∧ floor | total pairs failed | share of all failures`)

- **Occurrences:** 9 methodology files (same set as A.3).
- **SST rule:** rule 2 (pivots, not duplicates).
- **Classification:** Real sibling redundancy in two-thirds of cases. The
  global `failure_analysis.md` holds the all-SMR view; each SMR-specific
  file should hold only the `smr_key = ...` filter of the same canonical
  view, not a separate authored table. Currently the SMR-specific files
  carry an SMR-filtered cut that is structurally identical to the global
  one with a different filter argument.
- **Decision:** Treat as pivot views. Render each SMR-specific file by
  the same generator (`src/scripts/generate_failure_analysis.py` already
  emits them) with the `smr_key` argument named in the caption. Add a
  footer line stating the source CSV and the filter
  (`smr_key={...}`). Treatment scope: caption + footer edit on 8 files;
  no row removal.

### A.5 Failure-analysis country survivorship (`iso | country | n sites | n pairs | survived | survival rate | hard only | hard ∧ floor | floor only | sites w/ survivor`)

- **Occurrences:** 9 methodology files (same set as A.3 / A.4).
- **SST rule:** rule 2.
- **Classification:** Same as A.4 — pivot view, one canonical generator
  per SMR filter.
- **Decision:** Same as A.4. Caption + footer edit; no row removal.

### A.6 Per-site criterion evidence block (`criterion | code | measured value | threshold | confidence | justification`)

- **Occurrences:** 3 site profiles
  (`HR_ploce_power_station.md`, `ME_maoce_power_station.md`,
  `ME_pljevlja_power_station.md`).
- **SST rule:** rule 4.
- **Classification:** Not a redundancy. Each instance is a per-site
  evidence table rendered from the corresponding site bundle.
- **Decision:** Acceptable. No action required.

### A.7 Confidence-band descriptor (`band | condition | descriptor`)

- **Occurrences:** 10 occurrences across 2 files
  (`methodology/exclusionary_floors.md` and
  `annexes/annex_b_scoring_methodology_and_exclusionary_floors.md`).
- **SST rule:** rule 2 (pivot view, not duplicate).
- **Classification:** Surface-level signature match but the table contents
  differ: `methodology/exclusionary_floors.md` is the engineering-audit
  surface (hard-fail descriptors, floor pass-mark notes, score-pivot
  distances, and rubric expression text), while Annex B is the
  reader-facing methodology surface (simplified descriptors and band
  semantics for the report audience). Row counts and condition strings
  are intentionally different.
- **Decision:** Two-audience treatment. Both surfaces are retained.
  Add explicit cross-reference lines so the engineering and reader-facing
  surfaces point at each other: Annex B cites
  `methodology/exclusionary_floors.md` as the engineering source; the
  methodology file cites Annex B as the reader-facing summary.

### A.8 Failure-analysis criterion-pair tally (`distinct criteria failed | pairs | share of failed`)

- **Occurrences:** 2 files (`methodology/failure_analysis.md` and
  `methodology/failure_analysis_nuscale_voygr6.md`).
- **SST rule:** rule 2.
- **Classification:** Same as A.4. Pivot view, NuScale filter of the
  canonical all-SMR view.
- **Decision:** Same as A.4. Caption + footer edit.

---

## B. Prose-level findings driven by reviewer comments

### B.1 Reviewer `#54` — repeated explanations across §4.x

- **Anchor:** `report/version 1.03/output/report/chapters/03_stage_2_site_selection.md`
  (§3.10) + `report/version 1.03/output/report/chapters/04_results_and_findings.md`.
- **SST rule:** rule 5 (prose-citation discipline).
- **Classification:** Real prose redundancy. The reviewer flags that
  Chapter 4 restates the same finding in §4.1, §4.3, §4.4 and §4.6 with
  different wording. The cause is narrative repetition rather than table
  duplication.
- **Decision:** Tighten §4.1 / §4.3 / §4.4 / §4.6 so each restatement
  cites the canonical table (Table 4.3.1 / 4.3.2 / 4.4.1 / 4.6.1) rather
  than re-prose the same row counts. Implementation already partly done
  in Phase 5a (counts cite the regenerated tables); the remaining work is
  a copy-edit pass to remove the narrative restatements that still
  duplicate the table content.

### B.2 Reviewer `#57` — do we need cross-country evaluation more than illustrated in Table 4.1?

- **Anchor:** `04_results_and_findings.md` §4.1 (above Table 4.1.1).
- **SST rule:** rules 1 + 6.
- **Classification:** Real scoping question. The reviewer asks whether
  any cross-country prose beyond Table 4.1.1 + 4.3.1 + 4.3.2 is
  justified. The answer is: the regional Tables 4.1.1 / 4.3.1 / 4.3.2
  are the canonical regional surface; any cross-country prose elsewhere
  in Chapter 4 should cite them rather than restate. Chapter 5 country
  profiles hold the per-country detail and do not need to mirror
  Chapter 4 row counts.
- **Decision:** Keep the regional tables as the canonical regional home.
  Replace any sibling cross-country table in Chapter 4 prose with a
  citation. Walk Chapter 4 once and confirm no narrative paragraph
  restates Chapter 5 country-level totals.

### B.3 Reviewer `#70` — several similar tables in §5.2 saying the same thing

- **Anchor:** `05_country_and_site_profiles.md` §5.2.
- **SST rule:** rules 1 + 6.
- **Classification:** Real surface redundancy. §5.2 has (i) the
  Country | Current profile | Leading candidate | Screening class index
  table at lines 20-37, (ii) a paragraph that lists the same countries in
  text, and (iii) the per-country prototype that repeats the same row in
  its opening identity block. Three different surfaces print the same
  fact "Austria's leading candidate is Riedersbach with avoidance flag".
- **Decision:** Pick the §5.2 index table as the canonical chapter-5 home
  (rule 6). Tighten the §5.2 prose to remove the narrative country list
  that restates rows from the index table. Per-country prototypes keep
  their identity blocks because they are programmatic projections from
  the country bundle, not hand-authored copies.

---

## C. Cross-chapter prose findings

### C.1 Iernut row data appearing in both Chapter 4 and the Romanian country profile

- **SST rule:** rule 6.
- **Classification:** Expected. Chapter 4 Table 4.3.1 holds the regional
  full-pass row; the Romanian country profile holds the per-country
  context (composite, MC interval, band, drivers) inside the country
  ledger filter. The two surfaces share the same atomic fact but project
  it for different audiences (regional ranking vs national deep-dive).
- **Decision:** Acceptable per rule 6. The regional row cites the
  Romanian country profile for context; the country profile cites the
  regional table for placement.

### C.2 Country roster restatement in §2.1 + §5.2 + Annex E + reading list

- **Files:**
  - `chapters/02_stage_1_site_survey.md`
  - `chapters/05_country_and_site_profiles.md`
  - `annexes/annex_e_assumption_register_and_data_limitations.md`
- **SST rule:** rule 1.
- **Classification:** Soft redundancy. Each surface restates "Austria,
  Bosnia and Herzegovina, Bulgaria, Czechia, Croatia, Hungary, Latvia,
  Moldova, Montenegro, North Macedonia, Poland, Romania, Serbia,
  Slovakia, Turkey and Ukraine". This is acceptable because the roster
  is a scoping anchor: it has to appear in the scoping chapter
  (Chapter 2), the country-profile chapter (Chapter 5), and the
  assumption register (Annex E A-SCOPE-03). The text is verbatim and
  any update has to propagate to all three.
- **Decision:** Keep all three restatements. Add a one-line maintenance
  note to `audit/conversations/` flagging the three locations as a
  single update unit so that the next roster change touches all three
  together.

---

## D. Categories of treatment summarised

| Category                                                                 | Treatment                                                                             | Rule(s)   | Affected files                          |
| :----------------------------------------------------------------------- | :------------------------------------------------------------------------------------ | :-------- | :-------------------------------------- |
| Methodology glossary mirrored across SMR files                           | Declare canonical home in `failure_analysis.md`; SMR files cross-reference.           | 1         | A.3 — 8 files                           |
| Methodology criterion / country / pair tables mirrored across SMR files  | Treat as pivot view; caption names filter; footer cites source CSV.                   | 2 + 3 + 4 | A.4, A.5, A.8 — 8 files each            |
| Confidence-band descriptor table — engineering vs reader-facing surfaces | Two-audience treatment retained; add reciprocal cross-references.                     | 2         | A.7 — 2 files                           |
| Chapter 4 narrative restatements of Chapter 4 tables                     | Tighten prose to cite the canonical table; remove inline row restatements.            | 5         | B.1 — `04_results_and_findings.md`      |
| Chapter 4 / 5 cross-surface country totals                               | Keep regional tables as canonical home; replace sibling restatements with citations.  | 1 + 6     | B.2 — `04_results_and_findings.md`      |
| §5.2 country index + narrative country list                              | Keep the index table; remove the narrative country list that restates it.             | 1 + 6     | B.3 — `05_country_and_site_profiles.md` |
| Country roster restatement across §2.1 + §5.2 + Annex E A-SCOPE-03       | Keep all three (scoping anchor); add maintenance note.                                | 1 (soft)  | C.2 — 3 files                           |
| Per-site / per-country programmatic projections                          | Acceptable; canonical home is the bundle JSON / ledger CSV; render is the projection. | 4         | A.1, A.2, A.6 — 86 files                |

---

## E. Execution order (matched to `p5c_redundancy_decide_execute`)

1. A.3 — canonical glossary in `failure_analysis.md`; cross-reference in the 8 SMR variants.
2. A.4, A.5, A.8 — caption + footer edits in the 8 SMR variants naming the
   `smr_key` filter and the source CSV.
3. A.7 — add reciprocal cross-references between
   `methodology/exclusionary_floors.md` and Annex B so the engineering
   and reader-facing surfaces explicitly point at each other.
4. B.1 — copy-edit pass on §4.1 / §4.3 / §4.4 / §4.6 of
   `04_results_and_findings.md` to remove narrative restatements of the
   canonical tables.
5. B.2 — sweep Chapter 4 for sibling cross-country prose; replace with
   citations to Tables 4.1.1 / 4.3.1 / 4.3.2.
6. B.3 — tighten §5.2 of `05_country_and_site_profiles.md` to remove the
   narrative country list that restates the §5.2 index table.
7. C.2 — record the country-roster maintenance note in the closure audit
   log.

After execution, rerun `src/scripts/cross_chapter_numeric_lint.py --strict`
and `src/scripts/lint_ledger_consistency.py` to confirm no numeric drift
was introduced by the prose edits.
