# man_hours: 0.25
"""Console-script ``atoms-gui`` — boots the Streamlit GUI without ceremony.

Run via ``atoms-gui`` (after ``pip install -e .[gui]``) or
``python -m atoms_vs_ashes.gui.launcher``. The launcher is a thin
wrapper around ``streamlit run src/atoms_vs_ashes/gui/app.py`` so the
user does not have to remember the entry-point path.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    """Boot the Streamlit GUI."""
    try:
        from streamlit.web import cli as stcli  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001 — best-effort UX
        sys.stderr.write(
            "Streamlit is not installed. Install GUI extras: "
            "`pip install -e .[gui]`.\n"
            f"({exc})\n"
        )
        return 1
    here = Path(__file__).parent
    app_path = here / "app.py"
    if not app_path.is_file():
        sys.stderr.write(f"GUI entry point missing: {app_path}\n")
        return 2
    sys.argv = [
        "streamlit", "run", str(app_path),
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    raise SystemExit(main())
