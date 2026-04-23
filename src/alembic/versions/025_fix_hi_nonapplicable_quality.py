"""Patch HI-02/03/04 quality for non-EU/partial-coverage countries.

E-PRTR/SEVESO registers cover only EU member states. Sites in countries
outside that register previously got quality='insufficient', which is
semantically incorrect — 'insufficient' means data exists but is below
minimum quality. 'not_applicable' is the correct value when the data
source does not cover the country at all.

Also corrects the 466 malformed observations that printed '[] km' instead
of the actual search radius, by updating them to use the corrected text.

Countries without E-PRTR coverage (no_coverage + partial):
  BA, ME, XK, AL, MK, MD, UA, BY, AM  (no coverage)
  RS, TR  (partial coverage, still not assessable from E-PRTR alone)

EU member states in scope (retain existing quality values):
  PL, CZ, SK, HU, AT, SI, HR, BG, RO, EE, LV, LT

Revision ID: 025
Revises: 024
Create Date: 2026-04-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NON_EU_COUNTRIES = (
    "BA", "ME", "XK", "AL", "MK", "MD", "UA", "BY", "AM",
    "RS", "TR",
)


def upgrade() -> None:
    conn = op.get_bind()

    placeholders = ", ".join(f"'{c}'" for c in _NON_EU_COUNTRIES)

    conn.execute(sa.text(f"""
        UPDATE site_human_hazards h
        SET hi02_quality = 'not_applicable',
            hi03_quality = 'not_applicable',
            hi04_quality = 'not_applicable'
        FROM sites s
        WHERE h.site_id = s.site_id
          AND s.country_code IN ({placeholders})
          AND (h.hi02_quality = 'insufficient' OR h.hi02_quality IS NULL)
    """))

    conn.execute(sa.text("""
        UPDATE site_observations
        SET observation = regexp_replace(
                observation,
                'No E-PRTR/SEVESO facilities found within \\[\\] km\\.',
                'No E-PRTR/SEVESO facilities found within 30 km.',
                'g'
            )
        WHERE criterion_id = 'HI-02'
          AND observation LIKE '%within [] km%'
    """))


def downgrade() -> None:
    conn = op.get_bind()

    placeholders = ", ".join(f"'{c}'" for c in _NON_EU_COUNTRIES)

    conn.execute(sa.text(f"""
        UPDATE site_human_hazards h
        SET hi02_quality = 'insufficient',
            hi03_quality = 'insufficient',
            hi04_quality = 'insufficient'
        FROM sites s
        WHERE h.site_id = s.site_id
          AND s.country_code IN ({placeholders})
          AND h.hi02_quality = 'not_applicable'
    """))
