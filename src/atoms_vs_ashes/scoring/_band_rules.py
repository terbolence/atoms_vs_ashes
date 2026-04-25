# man_hours: 0.5
"""Stability band thresholds and country shortlist sizing.

Bands **A–C** are unchanged from the original regulatory definition.
Sites that fail the top-10 % / 0.50 hit-rate rule (formerly lumped into
one big **D**) are split into **D–H** using the fraction of scenarios
in which the site's best pair sits in the **global top 30 %** slice —
the natural percentile extension for siting studies where the head of
the distribution matters but ~90 % of sites should not collapse into a
single opaque tier.

Re-used at every analysis *scope*: global all-SMR, global per-SMR, and
within-country (all-SMR or per-SMR). The percentile is applied inside
whichever pool the scope defines, so per-country bands rank local
competitiveness rather than global rank.
"""

from __future__ import annotations

import math

TOP_PCTS: tuple[float, float, float] = (0.05, 0.10, 0.30)

BAND_DISPLAY_ORDER: tuple[str, ...] = ("A", "B", "C", "D", "E", "F", "G", "H")


def assign_stability_band(
    rate5: float, rate10: float, rate30: float
) -> str:
    """Return band A–H from pre-rounded hit rates in [0, 1].

    ``rate5`` / ``rate10`` / ``rate30`` are the fractions of scenarios
    in which the site (best of its pairs) sits in the top-5 / 10 / 30 %
    slice of the scenario's pool.
    """
    if rate5 >= 0.80:
        return "A"
    if rate10 >= 0.80:
        return "B"
    if rate10 >= 0.50:
        return "C"
    if rate30 >= 9 / 14:
        return "D"
    if rate30 >= 7 / 14:
        return "E"
    if rate30 >= 5 / 14:
        return "F"
    if rate30 >= 3 / 14:
        return "G"
    return "H"


def shortlist_size(n_sites: int, *, pct: float = 0.30, floor: int = 10) -> int:
    """Country shortlist size K.

    - ``n < floor`` → K = n (every site).
    - ``n >= floor`` → K = min(n, max(floor, ceil(pct * n))).

    Examples with defaults (pct=0.30, floor=10): n=5→5, n=9→9, n=10→10,
    n=15→10, n=50→15, n=100→30.
    """
    if n_sites <= 0:
        return 0
    if n_sites < floor:
        return n_sites
    return min(n_sites, max(floor, int(math.ceil(pct * n_sites))))
