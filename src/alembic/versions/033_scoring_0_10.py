"""Phase 1.1 — migrate scoring schema to native 0–10.

Replaces the 1–5 ``score`` / ``score_low`` / ``score_high`` columns on
``ranking_scores`` with ``NUMERIC(3,1)`` companions on a 0–10 range
(``score_0_10``, ``score_low_0_10``, ``score_high_0_10``) and carries the
per-criterion weight provenance (``weight_factor``, ``weight_normalised``,
``quality_flag``) on every score row.

Adds Monte-Carlo bounds and a ``weight_profile`` discriminator to
``composite_rankings`` so sensitivity runs (``w_plus_20``, ``w_minus_20``,
``mc_1000`` …) coexist with the baseline composite.

Data copy: ``score_0_10 = score * 2`` (1 → 2, 5 → 10); weights back-filled
from ``report/sites_evaluation/02_master_weights.md`` (sum of the 48
per-criterion factors = 283, normalised to 1.0).

Downgrade is deterministic: ``score = GREATEST(1, LEAST(5, ROUND(score_0_10 / 2.0)::int))``.

Revision ID: 033
Revises: 032
Create Date: 2026-04-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "033"
down_revision: Union[str, None] = "032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Master weight table — single source of truth:
# report/sites_evaluation/02_master_weights.md.
# Σ of the 48 per-criterion factors = 283, used as the normaliser so
# persisted ``weight_normalised`` values sum to exactly 1.0.
# ---------------------------------------------------------------------------

_WEIGHT_FACTORS: dict[str, int] = {
    "BF-01": 8, "BF-02": 5,
    "NH-01": 9, "NH-02": 9, "NH-03": 7, "NH-04": 5, "NH-05": 7,
    "NH-06": 5, "NH-07": 10, "NH-08": 6, "NH-09": 8, "NH-10": 3,
    "NH-11": 3, "NH-12": 4, "NH-13": 3, "NH-14": 3,
    "HI-01": 7, "HI-02": 7, "HI-03": 7, "HI-04": 6, "HI-05": 6,
    "HI-06": 6, "HI-07": 2, "HI-08": 3,
    "RI-01": 6, "RI-02": 5, "RI-03": 5, "RI-04": 8, "RI-05": 10,
    "RI-06": 5,
    "EP-01": 8, "EP-02": 6, "EP-03": 5, "EP-04": 6, "EP-05": 4,
    "NS-01": 8, "NS-02": 8, "NS-03": 8, "NS-04": 6, "NS-05": 5,
    "NS-06": 5, "NS-07": 5, "NS-08": 6, "NS-09": 5, "NS-10": 4,
    "NS-11": 6, "NS-12": 6, "NS-13": 4,
}
_WEIGHT_SUM = sum(_WEIGHT_FACTORS.values())  # 283


def upgrade() -> None:
    bind = op.get_bind()

    # ------------------------------------------------------------------
    # ranking_scores — add 0–10 score columns + weight provenance
    # ------------------------------------------------------------------
    op.add_column(
        "ranking_scores",
        sa.Column("score_0_10", sa.Numeric(3, 1), nullable=True),
    )
    op.add_column(
        "ranking_scores",
        sa.Column("score_low_0_10", sa.Numeric(3, 1), nullable=True),
    )
    op.add_column(
        "ranking_scores",
        sa.Column("score_high_0_10", sa.Numeric(3, 1), nullable=True),
    )

    # Copy legacy 1–5 values into the new 0–10 columns (1 → 2, 5 → 10).
    bind.execute(sa.text("""
        UPDATE ranking_scores
           SET score_0_10      = score * 2,
               score_low_0_10  = score_low * 2,
               score_high_0_10 = score_high * 2
    """))

    op.alter_column("ranking_scores", "score_0_10", nullable=False)

    # Drop the legacy 1–5 check constraints before dropping the columns.
    op.drop_constraint("ck_ranking_score_range", "ranking_scores", type_="check")
    op.drop_constraint(
        "ck_ranking_score_low_range", "ranking_scores", type_="check"
    )
    op.drop_constraint(
        "ck_ranking_score_high_range", "ranking_scores", type_="check"
    )

    op.drop_column("ranking_scores", "score_high")
    op.drop_column("ranking_scores", "score_low")
    op.drop_column("ranking_scores", "score")

    op.create_check_constraint(
        "ck_ranking_score_0_10_range",
        "ranking_scores",
        "score_0_10 BETWEEN 0 AND 10",
    )
    op.create_check_constraint(
        "ck_ranking_score_low_0_10_range",
        "ranking_scores",
        "score_low_0_10 IS NULL OR score_low_0_10 BETWEEN 0 AND 10",
    )
    op.create_check_constraint(
        "ck_ranking_score_high_0_10_range",
        "ranking_scores",
        "score_high_0_10 IS NULL OR score_high_0_10 BETWEEN 0 AND 10",
    )

    # Weight provenance — recorded per score row so downstream exports
    # never have to look up the master table at query time.
    op.add_column(
        "ranking_scores",
        sa.Column("weight_factor", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "ranking_scores",
        sa.Column("weight_normalised", sa.Numeric(5, 4), nullable=True),
    )
    op.add_column(
        "ranking_scores",
        sa.Column("quality_flag", sa.String(20), nullable=True),
    )
    op.create_check_constraint(
        "ck_ranking_weight_factor_range",
        "ranking_scores",
        "weight_factor IS NULL OR weight_factor BETWEEN 1 AND 10",
    )
    op.create_check_constraint(
        "ck_ranking_weight_normalised_range",
        "ranking_scores",
        "weight_normalised IS NULL OR (weight_normalised >= 0 AND weight_normalised <= 1)",
    )

    # Back-fill weight_factor / weight_normalised from the master table.
    for criterion_id, factor in _WEIGHT_FACTORS.items():
        normalised = round(factor / _WEIGHT_SUM, 4)
        bind.execute(
            sa.text("""
                UPDATE ranking_scores
                   SET weight_factor = :wf,
                       weight_normalised = :wn
                 WHERE criterion_id = :cid
            """),
            {"wf": factor, "wn": normalised, "cid": criterion_id},
        )

    # ------------------------------------------------------------------
    # composite_rankings — add MC bounds + weight_profile discriminator
    # ------------------------------------------------------------------
    op.add_column(
        "composite_rankings",
        sa.Column("composite_score_low", sa.Numeric(6, 3), nullable=True),
    )
    op.add_column(
        "composite_rankings",
        sa.Column("composite_score_high", sa.Numeric(6, 3), nullable=True),
    )
    op.add_column(
        "composite_rankings",
        sa.Column(
            "weight_profile",
            sa.String(30),
            nullable=False,
            server_default="baseline",
        ),
    )
    op.create_index(
        "ix_composite_weight_profile",
        "composite_rankings",
        ["weight_profile"],
    )

    # Extend the uniqueness so that sensitivity runs reusing a run_id
    # across several profiles do not collide with the baseline row.
    op.drop_constraint(
        "uq_composite_site_smr_run",
        "composite_rankings",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_composite_site_smr_run_profile",
        "composite_rankings",
        ["site_id", "smr_key", "run_id", "weight_profile"],
    )


def downgrade() -> None:
    # ------------------------------------------------------------------
    # composite_rankings — restore original uniqueness and drop extras
    # ------------------------------------------------------------------
    op.drop_constraint(
        "uq_composite_site_smr_run_profile",
        "composite_rankings",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_composite_site_smr_run",
        "composite_rankings",
        ["site_id", "smr_key", "run_id"],
    )
    op.drop_index(
        "ix_composite_weight_profile", table_name="composite_rankings"
    )
    op.drop_column("composite_rankings", "weight_profile")
    op.drop_column("composite_rankings", "composite_score_high")
    op.drop_column("composite_rankings", "composite_score_low")

    # ------------------------------------------------------------------
    # ranking_scores — rebuild the legacy 1–5 columns
    # ------------------------------------------------------------------
    op.drop_constraint(
        "ck_ranking_weight_normalised_range", "ranking_scores", type_="check"
    )
    op.drop_constraint(
        "ck_ranking_weight_factor_range", "ranking_scores", type_="check"
    )
    op.drop_column("ranking_scores", "quality_flag")
    op.drop_column("ranking_scores", "weight_normalised")
    op.drop_column("ranking_scores", "weight_factor")

    op.add_column(
        "ranking_scores",
        sa.Column("score", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "ranking_scores",
        sa.Column("score_low", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "ranking_scores",
        sa.Column("score_high", sa.SmallInteger(), nullable=True),
    )

    bind = op.get_bind()
    bind.execute(sa.text("""
        UPDATE ranking_scores
           SET score      = GREATEST(1, LEAST(5, ROUND(score_0_10 / 2.0)::int)),
               score_low  = CASE
                    WHEN score_low_0_10 IS NULL THEN NULL
                    ELSE GREATEST(1, LEAST(5, ROUND(score_low_0_10 / 2.0)::int))
               END,
               score_high = CASE
                    WHEN score_high_0_10 IS NULL THEN NULL
                    ELSE GREATEST(1, LEAST(5, ROUND(score_high_0_10 / 2.0)::int))
               END
    """))

    op.alter_column("ranking_scores", "score", nullable=False)

    op.drop_constraint(
        "ck_ranking_score_high_0_10_range", "ranking_scores", type_="check"
    )
    op.drop_constraint(
        "ck_ranking_score_low_0_10_range", "ranking_scores", type_="check"
    )
    op.drop_constraint(
        "ck_ranking_score_0_10_range", "ranking_scores", type_="check"
    )

    op.drop_column("ranking_scores", "score_high_0_10")
    op.drop_column("ranking_scores", "score_low_0_10")
    op.drop_column("ranking_scores", "score_0_10")

    op.create_check_constraint(
        "ck_ranking_score_range",
        "ranking_scores",
        "score BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_ranking_score_low_range",
        "ranking_scores",
        "score_low IS NULL OR score_low BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_ranking_score_high_range",
        "ranking_scores",
        "score_high IS NULL OR score_high BETWEEN 1 AND 5",
    )
