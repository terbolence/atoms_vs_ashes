# man_hours: 1.2
"""Insert Iernut CCGT supplementary site.

Revision ID: 049
Revises: 048
Create Date: 2026-05-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "049"
down_revision: Union[str, None] = "048"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SITE_ID = "af7f107f-71b5-5a33-8125-9ccb7060f895"
_SITE_NAME = "Iernut power station"


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            WITH inserted AS (
                INSERT INTO sites (
                    site_id,
                    name,
                    alternative_names,
                    country_code,
                    country_name,
                    latitude,
                    longitude,
                    geom,
                    location_accuracy,
                    local_area,
                    subnational_unit,
                    region,
                    plant_type,
                    installed_capacity_mw,
                    status,
                    start_year,
                    owner_operator,
                    parent_company,
                    combustion_technology,
                    location,
                    wiki_url,
                    extended_data,
                    unit_count,
                    last_verified,
                    source_db
                )
                SELECT
                    CAST(:site_id AS uuid),
                    :name,
                    ARRAY[
                        'Centralei Termoelectrice Iernut',
                        'CTE Iernut',
                        'Ludus-Iernut'
                    ],
                    'RO',
                    'Romania',
                    46.467700,
                    24.183300,
                    ST_SetSRID(ST_MakePoint(24.183300, 46.467700), 4326),
                    'exact',
                    'Iernut',
                    'Mureș',
                    'Europe',
                    'gas',
                    430.00,
                    'construction',
                    2026,
                    'Romgaz SA [100%]',
                    'Romgaz SA [100.0%]',
                    'combined cycle',
                    'Iernut, Mureș County',
                    'https://www.gem.wiki/Iernut_power_station',
                    jsonb_build_object(
                        'source', 'alembic_049',
                        'fuel', 'fossil gas: natural gas',
                        'address', '545100, Mures, Iernut, Str. Energeticii nr 1',
                        'romgaz_ccgt_url', 'https://www.romgaz.ro/en/ccgt-project-overview-0',
                        'romgaz_branch_url', 'https://www.romgaz.ro/en/iernut-power-plant-branch',
                        'gem_wiki_url', 'https://www.gem.wiki/Iernut_power_station',
                        'ccgt_configuration', '4 gas turbines, 4 heat recovery steam generators, 2 steam turbines',
                        'gross_electrical_efficiency_pct', 56
                    ),
                    1,
                    now(),
                    'api'
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM sites
                    WHERE site_id = CAST(:site_id AS uuid)
                       OR (country_code = 'RO' AND lower(name) = lower(:name))
                )
                RETURNING site_id, name, country_code, plant_type, installed_capacity_mw
            )
            INSERT INTO audit_log (
                operation,
                table_name,
                site_id,
                after_value,
                source_file,
                run_id,
                message
            )
            SELECT
                'insert',
                'sites',
                site_id,
                jsonb_build_object(
                    'name', name,
                    'country_code', country_code,
                    'plant_type', plant_type,
                    'installed_capacity_mw', installed_capacity_mw,
                    'source', 'alembic_049'
                ),
                'src/alembic/versions/049_insert_iernut_ccgt_site.py',
                'alembic-049',
                'Inserted Iernut CCGT supplementary site'
            FROM inserted
            """
        ),
        {"site_id": _SITE_ID, "name": _SITE_NAME},
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            DELETE FROM audit_log
            WHERE site_id = CAST(:site_id AS uuid)
              AND run_id = 'alembic-049'
            """
        ),
        {"site_id": _SITE_ID},
    )
    bind.execute(
        sa.text(
            """
            DELETE FROM sites
            WHERE site_id = CAST(:site_id AS uuid)
              AND country_code = 'RO'
              AND lower(name) = lower(:name)
            """
        ),
        {"site_id": _SITE_ID, "name": _SITE_NAME},
    )
