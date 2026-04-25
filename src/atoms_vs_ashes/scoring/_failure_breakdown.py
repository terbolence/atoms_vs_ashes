# man_hours: 1.0
"""Aggregate failure outcomes for the Phase 1.6 site-screening pipeline.

Pure-data helpers used by ``scripts.generate_failure_analysis``: takes
pre-loaded ``ScreeningVerdict`` rows (filtered by the relevant
``run_id``) plus a ``site_id → country_code`` lookup and returns a
:class:`FailureBreakdown` bundle with:

- top-level counts (universe, survivors, hard/floor/both buckets);
- per-criterion fail counts (unique pairs, not verdict rows);
- per-country and per-SMR outcome breakdowns;
- a one-row-per-pair list with the criterion ids that triggered;
- a histogram of compound failures (distinct criteria failed per pair).

This dual-bucket view (hard vs. floor) is what regulators want to read:
hard fails are unambiguous, floor fails sit on top of the 5.0 safety
floor (see ``report/methodology/exclusionary_floors.md``), and the join
shows which sites have *no* legitimate path forward.
"""

from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from atoms_vs_ashes.db.models import ScreeningVerdict

EXCLUSIONARY_PHASE = "exclusionary"
FLOOR_SUFFIX = ":floor"


@dataclass(frozen=True)
class CriterionStat:
    criterion_id: str
    criterion_name: str
    hard_pairs: int
    floor_pairs: int
    union_pairs: int
    intersection_pairs: int


@dataclass(frozen=True)
class CountryStat:
    country_code: str
    n_sites: int
    n_pairs: int
    survived: int
    hard_only: int
    floor_only: int
    both: int
    n_sites_with_survivor: int


@dataclass(frozen=True)
class SmrStat:
    smr_key: str
    n_pairs: int
    survived: int
    hard_only: int
    floor_only: int
    both: int


@dataclass(frozen=True)
class PairOutcome:
    site_id: uuid.UUID
    smr_key: str
    country_code: str
    bucket: str  # "survived" | "hard_only" | "floor_only" | "both"
    hard_criteria: tuple[str, ...]
    floor_criteria: tuple[str, ...]


@dataclass
class FailureBreakdown:
    total_pairs: int
    survived: int
    hard_only: int
    floor_only: int
    both: int
    n_distinct_sites: int
    n_distinct_smrs: int
    per_criterion: list[CriterionStat]
    per_country: list[CountryStat]
    per_smr: list[SmrStat]
    pair_outcomes: list[PairOutcome]
    multi_failure_histogram: dict[int, int]

    @property
    def failed_any(self) -> int:
        return self.hard_only + self.floor_only + self.both

    @property
    def failed_by_hard(self) -> int:
        return self.hard_only + self.both

    @property
    def failed_by_floor(self) -> int:
        return self.floor_only + self.both


def _is_floor_key(prompt_key: str | None) -> bool:
    return bool(prompt_key and prompt_key.endswith(FLOOR_SUFFIX))


def _bucket_of(hard: set[str], floor: set[str]) -> str:
    if not hard and not floor:
        return "survived"
    if hard and floor:
        return "both"
    if hard:
        return "hard_only"
    return "floor_only"


def _collect_pair_failures(
    verdicts_by_pair: Mapping[tuple, Sequence[ScreeningVerdict]],
) -> dict[tuple, tuple[set[str], set[str]]]:
    """Return ``{(site_id, smr_key): (hard_criteria, floor_criteria)}``."""
    out: dict[tuple, tuple[set[str], set[str]]] = {}
    for pair, verdicts in verdicts_by_pair.items():
        hard: set[str] = set()
        floor: set[str] = set()
        for v in verdicts:
            if v.phase != EXCLUSIONARY_PHASE or v.verdict != "fail":
                continue
            if _is_floor_key(v.prompt_key):
                floor.add(v.criterion_id)
            else:
                hard.add(v.criterion_id)
        out[pair] = (hard, floor)
    return out


def _per_criterion_stats(
    pair_failures: Mapping[tuple, tuple[set[str], set[str]]],
    *,
    criterion_names: Mapping[str, str],
) -> list[CriterionStat]:
    hard_pairs: dict[str, set[tuple]] = defaultdict(set)
    floor_pairs: dict[str, set[tuple]] = defaultdict(set)
    for pair, (hard, floor) in pair_failures.items():
        for cid in hard:
            hard_pairs[cid].add(pair)
        for cid in floor:
            floor_pairs[cid].add(pair)
    cids = sorted(set(hard_pairs) | set(floor_pairs))
    rows: list[CriterionStat] = []
    for cid in cids:
        h = hard_pairs.get(cid, set())
        f = floor_pairs.get(cid, set())
        rows.append(
            CriterionStat(
                criterion_id=cid,
                criterion_name=criterion_names.get(cid, cid),
                hard_pairs=len(h),
                floor_pairs=len(f),
                union_pairs=len(h | f),
                intersection_pairs=len(h & f),
            )
        )
    rows.sort(key=lambda s: -s.union_pairs)
    return rows


def _per_country_stats(outcomes: Sequence[PairOutcome]) -> list[CountryStat]:
    by_country: dict[str, list[PairOutcome]] = defaultdict(list)
    for o in outcomes:
        by_country[o.country_code].append(o)
    rows: list[CountryStat] = []
    for code, items in by_country.items():
        bucket_counts = Counter(o.bucket for o in items)
        sites = {o.site_id for o in items}
        sites_with_survivor = {
            o.site_id for o in items if o.bucket == "survived"
        }
        rows.append(
            CountryStat(
                country_code=code,
                n_sites=len(sites),
                n_pairs=len(items),
                survived=bucket_counts.get("survived", 0),
                hard_only=bucket_counts.get("hard_only", 0),
                floor_only=bucket_counts.get("floor_only", 0),
                both=bucket_counts.get("both", 0),
                n_sites_with_survivor=len(sites_with_survivor),
            )
        )
    rows.sort(key=lambda r: (-r.n_pairs, r.country_code))
    return rows


def _per_smr_stats(outcomes: Sequence[PairOutcome]) -> list[SmrStat]:
    by_smr: dict[str, list[PairOutcome]] = defaultdict(list)
    for o in outcomes:
        by_smr[o.smr_key].append(o)
    rows: list[SmrStat] = []
    for smr, items in by_smr.items():
        bucket_counts = Counter(o.bucket for o in items)
        rows.append(
            SmrStat(
                smr_key=smr,
                n_pairs=len(items),
                survived=bucket_counts.get("survived", 0),
                hard_only=bucket_counts.get("hard_only", 0),
                floor_only=bucket_counts.get("floor_only", 0),
                both=bucket_counts.get("both", 0),
            )
        )
    rows.sort(key=lambda r: (-r.survived, r.smr_key))
    return rows


def aggregate_failures(
    verdicts_by_pair: Mapping[tuple, Sequence[ScreeningVerdict]],
    *,
    country_by_site: Mapping[uuid.UUID, str],
    criterion_names: Mapping[str, str],
) -> FailureBreakdown:
    """Build a :class:`FailureBreakdown` from pre-loaded verdicts."""
    pair_failures = _collect_pair_failures(verdicts_by_pair)
    outcomes: list[PairOutcome] = []
    for pair, (hard, floor) in pair_failures.items():
        site_id, smr_key = pair
        outcomes.append(
            PairOutcome(
                site_id=site_id,
                smr_key=smr_key,
                country_code=country_by_site.get(site_id, "??"),
                bucket=_bucket_of(hard, floor),
                hard_criteria=tuple(sorted(hard)),
                floor_criteria=tuple(sorted(floor)),
            )
        )
    outcomes.sort(key=lambda o: (o.country_code, o.smr_key, str(o.site_id)))

    bucket_counts = Counter(o.bucket for o in outcomes)
    distinct_sites = {o.site_id for o in outcomes}
    distinct_smrs = {o.smr_key for o in outcomes}
    histogram: Counter[int] = Counter()
    for _pair, (hard, floor) in pair_failures.items():
        union = hard | floor
        if union:
            histogram[len(union)] += 1

    return FailureBreakdown(
        total_pairs=len(outcomes),
        survived=bucket_counts.get("survived", 0),
        hard_only=bucket_counts.get("hard_only", 0),
        floor_only=bucket_counts.get("floor_only", 0),
        both=bucket_counts.get("both", 0),
        n_distinct_sites=len(distinct_sites),
        n_distinct_smrs=len(distinct_smrs),
        per_criterion=_per_criterion_stats(
            pair_failures, criterion_names=criterion_names
        ),
        per_country=_per_country_stats(outcomes),
        per_smr=_per_smr_stats(outcomes),
        pair_outcomes=outcomes,
        multi_failure_histogram=dict(sorted(histogram.items())),
    )


__all__ = [
    "CriterionStat",
    "CountryStat",
    "SmrStat",
    "PairOutcome",
    "FailureBreakdown",
    "aggregate_failures",
]
