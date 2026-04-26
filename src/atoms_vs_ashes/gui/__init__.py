# man_hours: 0.25
"""Streamlit GUI MVP for the user-controlled scoring & sensitivity loop.

Run via ``streamlit run src/atoms_vs_ashes/gui/app.py`` (after
``pip install -e .[gui]``). The package only exposes thin renderers
on top of stable backend services — every interaction round-trips
through :mod:`atoms_vs_ashes.criterion_spec.preview`,
:mod:`atoms_vs_ashes.runprofile`, and :mod:`atoms_vs_ashes.metrics`,
so the GUI never duplicates business logic.
"""

__all__: list[str] = []
