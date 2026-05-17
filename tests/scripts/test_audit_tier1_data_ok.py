# man_hours: 1.5
"""Tests for the read-only Tier 1 Data OK audit artifact writer."""

from __future__ import annotations

from scripts.audit_tier1_data_ok import (
    AuditRecord,
    numeric_summary,
    write_outputs,
)


def test_numeric_summary_reports_quantiles_and_stdev() -> None:
    out = numeric_summary([1, 2, 3, None, ""])

    assert out["count"] == 3
    assert out["min"] == 1.0
    assert out["median"] == 2.0
    assert out["max"] == 3.0
    assert out["stdev"] == 1.0


def test_write_outputs_creates_markdown_and_csv_artifacts(tmp_path) -> None:
    records = [
        AuditRecord(
            site_id="site-1",
            name="Alpha",
            country_code="RO",
            latitude=44.0,
            longitude=25.0,
            criterion_id="HI-07",
            smr_key="nuscale_voygr6",
            baseline_score=5.0,
            baseline_quality_flag="unscored",
            baseline_confidence="insufficient",
            baseline_justification="{}",
            candidate_score=7.5,
            candidate_quality_flag="scored",
            candidate_band="Sparse RF environment",
            fields={
                "transmitter_count": 2,
                "nearest_transmitter_km": 6.0,
                "transmitter_type": "tower",
                "hi07_quality": "ok",
                "hi07_comment": "sample",
                "human_run_id": "run-1",
                "human_fetched_at": None,
            },
        ),
        AuditRecord(
            site_id="site-2",
            name="Beta",
            country_code="CZ",
            latitude=50.0,
            longitude=14.0,
            criterion_id="NH-10",
            smr_key="nuscale_voygr6",
            baseline_score=9.5,
            baseline_quality_flag="medium",
            baseline_confidence="medium",
            baseline_justification="{}",
            candidate_score=5.5,
            candidate_quality_flag="scored",
            candidate_band="Middle relative wind exposure",
            fields={
                "max_wind_speed_ms": 10.0,
                "nh10_quality": "medium",
                "nh10_comment": "sample",
                "natural_run_id": "run-1",
                "natural_fetched_at": None,
            },
        ),
        AuditRecord(
            site_id="site-3",
            name="Gamma",
            country_code="TR",
            latitude=39.0,
            longitude=32.0,
            criterion_id="NH-12",
            smr_key="nuscale_voygr6",
            baseline_score=9.5,
            baseline_quality_flag="medium",
            baseline_confidence="medium",
            baseline_justification="{}",
            candidate_score=5.0,
            candidate_quality_flag="scored",
            candidate_band="aggregated(mean_of_sub_scores)",
            fields={
                "extreme_temp_max_c": 33.0,
                "extreme_temp_min_c": 3.0,
                "nh12_quality": "medium",
                "nh12_comment": "sample",
                "natural_run_id": "run-1",
                "natural_fetched_at": None,
            },
        ),
    ]

    paths = write_outputs(records, tmp_path, "20260517")

    assert len(paths) == 3
    assert all(path.exists() for path in paths)
    md = (tmp_path / "20260517_tier1_data_ok_curation_memo.md").read_text()
    assert "read-only audit" in md
    assert "HI-07" in md
    assert "Candidate scores" in md
