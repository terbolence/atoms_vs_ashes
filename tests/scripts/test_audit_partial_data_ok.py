# man_hours: 1.5
"""Tests for the read-only partial-data audit artifact writer."""

from __future__ import annotations

from scripts.audit_partial_data_ok import (
    CRITERIA,
    AuditRecord,
    FIELD_MAP,
    numeric_summary,
    write_outputs,
)


def test_criteria_tuple_covers_eight_bucket_c_tracks() -> None:
    assert CRITERIA == (
        "EP-03",
        "HI-02",
        "HI-03",
        "HI-04",
        "NH-09",
        "NH-11",
        "RI-03",
        "RI-05",
    )
    assert set(FIELD_MAP) == set(CRITERIA)


def test_numeric_summary_reports_quantiles_and_stdev() -> None:
    out = numeric_summary([1, 2, 3, None, ""])

    assert out["count"] == 3
    assert out["stdev"] == 1.0


def test_write_outputs_creates_csv_and_per_criterion_memos(tmp_path) -> None:
    records = [
        AuditRecord(
            site_id="site-1",
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
            fields={"sample": 1},
        )
        for cid in ("EP-03", "HI-02")
    ]

    paths = write_outputs(records, tmp_path, "20260517")

    assert (tmp_path / "20260517_partial_data_detail.csv").exists()
    assert (tmp_path / "20260517_partial_data_summary.csv").exists()
    assert (tmp_path / "20260517_partial_data_EP03_curation_memo.md").exists()
    assert len(paths) == 4  # detail + summary + EP-03 + HI-02 memos
