# man_hours: 0.75
"""Page 5 — **Results**: Phase 1 tools (Coverage / Sites / Sensitivity).

Workshop-ready set from
``src/architecture/specs/09_results_tools_specification.md``:

* **Coverage** — country survivor / near-miss / hard-fail matrix.
* **Sites** — country site ledger on the left + drawer on the right.
* **Regional** — composite-with-MC-band bar + map across the scope.
* **Stability** — A–H stability bands joined with MC composite range.
* **Sensitivity** — live DB sensitivity snapshot.

For sensitivity runs, Coverage / Sites / Regional / Failure Diagnostics
route through the *parent scoring run's baseline view* (resolved via
:func:`resolve_baseline_view`) so the verdict join finds the matching
``screening_verdicts`` rows; Sensitivity & Stability use the sensitivity
``run_id`` for perturbation deltas.

Only one **Tool** section renders per interaction (lazy) so the page
stays responsive.
"""

from __future__ import annotations

from atoms_vs_ashes.gui._results_page_main import render_results_page


def render() -> None:
    render_results_page()


render()
