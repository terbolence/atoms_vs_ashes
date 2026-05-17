# man_hours: 1.8
"""Tests for the read-only Phase 2 partial-data audit artifact writer."""

from __future__ import annotations

from scripts.audit_phase2_partial_data import (
    COVERAGE_VERDICT,
    CRITERIA,
    AuditRecord,
    numeric_summary,
    write_coverage_report,
    write_outputs,
)


def test_numeric_summary_reports_quantiles() -> None:
    out = numeric_summary([1, 2, 3, None])
    assert out["count"] == 3
    assert out["median"] == 2.0


def test_write_coverage_report_lists_all_criteria(tmp_path) -> None:
    records = [
        AuditRecord(
            site_id="s1",
            name="Alpha",
            country_code="RO",
            latitude=44.0,
            longitude=25.0,
            criterion_id="EP-03",
            smr_key="nuscale_voygr6",
            baseline_score=None,
            baseline_quality_flag=None,
            baseline_confidence=None,
            baseline_justification=None,
            candidate_score=7.5,
            candidate_quality_flag="scored",
            candidate_band="interim",
            fields={
                "ep03_gee_relief_16km_m": 120.0,
                "major_river_barrier": False,
                "waterway_count_epz": 1,
                "ep03_quality": "medium",
            },
        ),
    ]
    path = tmp_path / "20260517_phase2_data_coverage_report.md"
    write_coverage_report(records, path, run_id="run-1", smr_key="nuscale_voygr6")
    text = path.read_text()
    assert "EP-03" in text
    assert COVERAGE_VERDICT["EP-03"] in text
    for cid in CRITERIA:
        assert cid in text


def test_write_outputs_creates_csv_and_track_memos(tmp_path) -> None:
    records = [
        AuditRecord(
            site_id="s1",
            name="Alpha",
            country_code="RO",
            latitude=44.0,
            longitude=25.0,
            criterion_id=cid,
            smr_key="nuscale_voygr6",
            baseline_score=5.0,
            baseline_quality_flag="unscored",
            baseline_confidence="insufficient",
            baseline_justification="{}",
            candidate_score=7.5,
            candidate_quality_flag="scored",
            candidate_band="sample",
            fields={"hi02_quality": "ok", "nearest_seveso_km": None},
        )
        for cid in ("HI-02", "RI-03")
    ]
    paths = write_outputs(
        records,
        tmp_path,
        "20260517",
        run_id="run-1",
        smr_key="nuscale_voygr6",
    )
    assert any(p.name.endswith("_phase2_partial_data_detail.csv") for p in paths)
    assert any(p.name.endswith("_phase2_scored_site_examples.md") for p in paths)
    assert any(p.name == "phase2_track_HI-02_curation_memo.md" for p in paths)
