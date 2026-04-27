# man_hours: 2.0
"""Page 3 — Site Selection Criteria (threshold editor) with live rubric preview and (i) info icons.

Every input the user touches re-runs :func:`build_preview`, so the
0–10 band table, normalised weights, and modified-from-recommended
diff stay in sync. Tooltips use ``help=`` (hover) per Streamlit
convention. Exclusionary pass-marks (safety floor) are shown only for
criteria with at least one ``action: exclude`` fail condition;
ranking / avoidance rows only show score boundaries.

Criteria are colour-marked by importance (see :mod:`atoms_vs_ashes.gui._threshold_editor_palette`).
"""

from __future__ import annotations

from atoms_vs_ashes.gui._threshold_editor_impl import render

render()
