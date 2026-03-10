## 12. Project Execution Plan

### 12.1 Phased Approach

| Phase | Activity | Duration | Dependencies |
|---|---|---|---|
| **Phase 0: Preparation** | | **2 weeks** | |
| 0.1 | Establish project management framework, tools, repositories | Week 1 | — |
| 0.2 | Create document maps for IAEA SSG-35 and supplementary standards | Week 1 | 0.1 |
| 0.3 | Create document maps for EPRI 3002023910 | Week 1–2 | 0.1 |
| 0.4 | Finalise criteria weights with project stakeholders | Week 2 | 0.2, 0.3 |
| **Phase 1: Data Infrastructure** | | **3 weeks** | |
| 1.1 | Design and deploy PostgreSQL database schema | Week 3 | 0.1 |
| 1.2 | Ingest coal plant inventory (Global Energy Monitor, Beyond Fossil Fuels) | Week 3 | 1.1 |
| 1.3 | Add Romania supplementary sites (Braila-Chiscani, FPCU Feldioara) | Week 3 | 1.1 |
| 1.4 | Develop and execute web search validation module | Weeks 3–5 | 1.2 |
| 1.5 | Develop API connectors for external databases | Weeks 3–5 | 1.1 |
| 1.6 | Validate API connectors against known reference data | Week 5 | 1.5 |
| **Phase 2: Screening** | | **2 weeks** | |
| 2.1 | Execute exclusionary screening (E1–E9) | Week 6 | 1.4, 1.5 |
| 2.2 | Execute avoidance screening (A1–A15) | Week 6–7 | 2.1 |
| 2.3 | Review screening results, adjust thresholds if needed | Week 7 | 2.2 |
| 2.4 | Produce candidate site list | Week 7 | 2.3 |
| **Phase 3: Detailed Evaluation** | | **3 weeks** | |
| 3.1 | Retrieve detailed data for all candidate sites via API connectors | Week 8 | 2.4, 1.5 |
| 3.2 | Conduct manual data enrichment for primary-region sites | Weeks 8–9 | 3.1 |
| 3.3 | Apply scoring rubrics and compute scores | Week 9 | 3.1, 3.2 |
| 3.4 | Compute composite scores and rankings | Week 9 | 3.3 |
| 3.5 | Perform sensitivity analysis | Week 10 | 3.4 |
| 3.6 | Select final shortlist (12–20 sites) | Week 10 | 3.5 |
| **Phase 4: Report Development** | | **3 weeks** | |
| 4.1 | Draft site evaluation profiles | Weeks 10–11 | 3.6 |
| 4.2 | Develop business case chapter | Weeks 10–11 | 3.6 |
| 4.3 | Develop benefits map | Week 11 | 4.2 |
| 4.4 | Compile full report (Deliverable 2) | Weeks 11–12 | 4.1, 4.2, 4.3 |
| 4.5 | Compile viable site shortlist (Deliverable 1) | Week 12 | 3.6 |
| 4.6 | Internal review and quality assurance | Week 12–13 | 4.4, 4.5 |
| 4.7 | Final revision and delivery | Week 13 | 4.6 |

**Total Estimated Duration: 13 weeks**

### 12.2 Document Map Generation (Phase 0)

For each key reference document, a structured mapping file shall be created in the `document_maps/` folder to enable efficient reference during report development:

| Document | Map File | Content |
|---|---|---|
| IAEA SSG-35 | `document_maps/SSG-35_map.md` | Section-by-section summary with paragraph references, table/figure index, criteria extraction |
| IAEA SSR-1 | `document_maps/SSR-1_map.md` | Requirements summary with paragraph references |
| IAEA SSG-9 | `document_maps/SSG-9_map.md` | Seismic criteria and data requirements |
| IAEA SSG-18 | `document_maps/SSG-18_map.md` | Meteorological/hydrological criteria |
| IAEA SSG-21 | `document_maps/SSG-21_map.md` | Volcanic hazard criteria |
| IAEA NS-G-3.1 | `document_maps/NS-G-3.1_map.md` | Human induced events criteria and screening distances |
| IAEA NS-G-3.2 | `document_maps/NS-G-3.2_map.md` | Dispersion and population criteria |
| IAEA NS-G-3.6 | `document_maps/NS-G-3.6_map.md` | Geotechnical criteria |
| IAEA GSG-10 | `document_maps/GSG-10_map.md` | Radiological environmental impact framework |
| EPRI 3002023910 | `document_maps/EPRI-SitingGuide_map.md` | Criteria categories, screening steps, evaluation methodology |

Each map file shall contain:
- Document metadata (title, year, number of pages, key sections)
- Section-level summaries (1–3 sentences per section)
- Extracted criteria, thresholds, and screening values with exact paragraph/table references
- Cross-references to other IAEA/EPRI documents
- Key figures and tables identified by page number
