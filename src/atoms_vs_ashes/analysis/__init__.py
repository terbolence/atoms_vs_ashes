# man_hours: 0.5
"""Analysis modules — complex spatial assessments for screening and ranking.

All analysis modules follow the ``assess_and_persist()`` pattern:
fetch data from a connector, compute derived metrics, persist results
to domain-specific tables (SiteNaturalHazards, SiteHumanHazards, etc.)
with DataSource provenance and SiteObservation records.
"""
