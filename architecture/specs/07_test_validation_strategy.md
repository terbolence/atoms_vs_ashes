# 7. Test and Validation Strategy

## 7.1 Purpose

This document specifies the testing approach across unit, integration, and end-to-end levels, as well as manual cross-validation against reference sites.

**Traceability:** Requirements S10.8 (items 4–7).

---

## 7.2 Test Levels

### 7.2.1 Unit Tests

**Scope:** Individual functions and classes within each module.

**Coverage target:** ≥ 80% code coverage per module.

**What to test:**

| Module               | Unit Test Focus                                                          |
| -------------------- | ------------------------------------------------------------------------ |
| Data model           | Schema creation, field validation, ENUM constraints                      |
| Ingestion            | Parsing, deduplication, normalisation, country filtering                 |
| Each connector       | Response parsing, validation logic, cache key generation, error handling |
| Screening engine     | Each exclusionary criterion (E1–E9), each avoidance criterion (A1–A15)   |
| Scoring engine       | Score band assignment, composite score calculation, tie-breaking         |
| Sensitivity analysis | Weight perturbation, Monte Carlo iteration, statistical summary          |
| Output generation    | Report template rendering, CSV/JSON serialisation                        |

**Approach:**

- Use `pytest` with fixtures for database state and mock API responses.
- Connector unit tests shall use recorded (VCR-style) or mocked API responses, never live APIs.
- Screening and scoring tests shall use known-answer test cases: sites with predetermined attributes and expected pass/fail/score outcomes.

### 7.2.2 Integration Tests

**Scope:** End-to-end pipeline using a sample of known sites.

**What to test:**

- Full pipeline execution: ingest → enrich → screen → score → rank → report.
- Database state after each stage is consistent and complete.
- Output artifacts are generated and well-formed.
- Connector caching works correctly (second run uses cache).
- Configuration changes (weights, thresholds) produce expected ranking changes.

**Approach:**

- Use a dedicated test database (separate from production).
- Seed with a small fixture dataset (5–10 sites with known attributes).
- Connectors may use live APIs in integration tests (with caching to avoid repeated calls) or pre-recorded responses.

### 7.2.3 End-to-End Validation

**Scope:** Cross-check automated screening results against manual evaluation.

**Process:**

1. Select 3–5 reference sites with well-documented characteristics.
2. Manually evaluate each reference site against all criteria using the same data sources.
3. Run the automated pipeline on the same sites.
4. Compare:
   - Exclusionary screening results (pass/fail per criterion).
   - Avoidance screening results.
   - Assigned scores per criterion.
   - Final composite scores and ranks.
5. Document discrepancies and resolve (configuration error, data issue, or legitimate interpretation difference).

**Acceptance:** Automated results for reference sites shall match manual evaluation within documented tolerance bounds (e.g. score difference ≤ 0.5 on any criterion).

---

## 7.3 Connector Contract Tests

Each connector shall have a contract test that verifies:

1. **Schema compliance** — Response contains all required fields with correct types.
2. **Boundary behaviour** — Handles edge cases: sites on country borders, sites near poles/antimeridian (if applicable), sites with no nearby features.
3. **Error handling** — Gracefully handles API downtime, malformed responses, and empty results.
4. **Idempotency** — Running the same connector twice for the same site produces identical stored results (or correctly updates provenance timestamps).

---

## 7.4 Smoke Tests

Before any full batch run, execute a smoke test:

1. Run `health_check()` on all connectors.
2. Process 3–5 geographically diverse sites through the full pipeline.
3. Verify all stages complete without errors.
4. Verify output artifacts are generated.

If smoke tests fail, the batch run shall not proceed.

---

## 7.5 Regression Testing

When criteria, thresholds, or weights change:

1. Re-run the pipeline on the reference site set.
2. Compare results to the previous baseline.
3. Document expected vs. actual changes.
4. Update the baseline if changes are intentional.

---

## 7.6 Test Infrastructure

| Component         | Tool                                                    |
| ----------------- | ------------------------------------------------------- |
| Test runner       | pytest                                                  |
| Coverage          | pytest-cov                                              |
| API mocking       | responses, vcrpy, or pytest-httpserver                  |
| Database fixtures | pytest fixtures with SQLAlchemy test sessions           |
| CI integration    | Tests shall be runnable via a single command (`pytest`) |

---

## 7.7 Acceptance Criteria

- All modules have unit tests with ≥ 80% code coverage.
- Integration tests pass on the fixture dataset.
- End-to-end validation against 3–5 reference sites is documented with results.
- Smoke tests gate every batch run.
- Tests can be executed without network access (mocked API responses for unit tests).
