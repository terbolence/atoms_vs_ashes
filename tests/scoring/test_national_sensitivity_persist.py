# man_hours: 1.0
"""Unit tests for national sensitivity analytics writers."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

from atoms_vs_ashes.db.analytics_writers_national import (
    persist_national_mc_rank_distribution,
    persist_national_oat_importance,
    persist_national_rank_sensitivity,
    persist_national_sensitivity_summary,
)


class _Session:
    def __init__(self) -> None:
        self.executed = []
        self.saved = []

    def execute(self, stmt):  # noqa: ANN001 - SQLAlchemy statement double
        self.executed.append(stmt)

    def bulk_save_objects(self, objs):
        self.saved.extend(objs)


def test_rank_sensitivity_writer_noops_without_rows() -> None:
    session = _Session()
    assert persist_national_rank_sensitivity(
        session, run_id="sens-1", weight_profile="w_NH_plus_20", rows=[],
    ) == 0
    assert session.saved == []
    assert session.executed == []


def test_rank_sensitivity_writer_persists_rows() -> None:
    session = _Session()
    site_id = uuid.uuid4()
    rows = [
        SimpleNamespace(
            country_code="RO",
            smr_key="nuscale_voygr6",
            site_id=site_id,
            baseline_rank=1,
            scenario_rank=2,
            rank_delta=1,
            baseline_score=8.0,
            scenario_score=7.5,
            score_delta=-0.5,
            eligible_pair_count=4,
            small_n=False,
        )
    ]
    assert persist_national_rank_sensitivity(
        session,
        run_id="sens-1",
        weight_profile="w_NH_plus_20",
        scenario_family="weight",
        rows=rows,
    ) == 1
    assert len(session.executed) == 1
    saved = session.saved[0]
    assert saved.run_id == "sens-1"
    assert saved.country_code == "RO"
    assert saved.weight_profile == "w_NH_plus_20"
    assert saved.rank_delta == 1
    assert saved.scenario_family == "weight"


def test_summary_writer_uses_sentinels_for_optional_axes() -> None:
    session = _Session()
    rows = [
        {
            "country_code": "BG",
            "smr_key": "nuscale_voygr6",
            "metric": "profile_rank_delta",
            "weight_profile": "w_NH_plus_20",
            "criterion_id": None,
            "family": None,
            "n_pairs": 3,
            "mean_abs_rank_delta": 0.5,
            "small_n": False,
        }
    ]
    assert persist_national_sensitivity_summary(
        session, run_id="sens-1", rows=rows,
    ) == 1
    saved = session.saved[0]
    assert saved.criterion_id == "_all_"
    assert saved.family == "_all_"


def test_national_oat_writer_maps_to_summary_rows() -> None:
    session = _Session()
    rows = [
        SimpleNamespace(
            country_code="RO",
            smr_key="nuscale_voygr6",
            criterion_id="NH-01",
            family="NH",
            eligible_pair_count=3,
            mean_abs_rank_change=0.667,
            importance_score=0.2223,
            pairs_compared=3,
            small_n=False,
        )
    ]
    assert persist_national_oat_importance(session, "sens-1", rows) == 1
    saved = session.saved[0]
    assert saved.metric == "oat_importance"
    assert saved.criterion_id == "NH-01"
    assert saved.extra["pairs_compared"] == 3
    assert saved.extra["importance_score"] == 0.2223


def test_mc_rank_distribution_writer_persists_rows() -> None:
    session = _Session()
    site_id = uuid.uuid4()
    rows = [
        {
            "country_code": "RO",
            "smr_key": "nuscale_voygr6",
            "site_id": site_id,
            "iterations": 100,
            "p_rank_1": 0.25,
            "p_rank_le_3": 0.75,
            "p_rank_le_5": 1.0,
            "median_rank": 2,
            "p05_rank": 1,
            "p95_rank": 4,
            "rank_iqr": 1,
            "eligible_pair_count": 5,
            "small_n": False,
        }
    ]
    assert persist_national_mc_rank_distribution(
        session, run_id="sens-1", rows=rows,
    ) == 1
    saved = session.saved[0]
    assert saved.site_id == site_id
    assert saved.p_rank_le_3 == 0.75
