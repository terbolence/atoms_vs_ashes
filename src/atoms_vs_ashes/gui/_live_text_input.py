# man_hours: 0.4
"""Live-updating text field for search/filter (Streamlit quirk workarounds)."""

from __future__ import annotations

import streamlit as st

_DEFAULT_DEBOUNCE_MS = 200


def live_text_input(
    label: str,
    *,
    key: str,
    placeholder: str = "",
    help: str | None = None,
    debounce_ms: int = _DEFAULT_DEBOUNCE_MS,
) -> str:
    """Return text, updating while typing (debounced), not only on Enter/blur.

    Native ``st.text_input`` only commits on Enter or when focus leaves
    the field, so table filters would not feel live. The optional
    ``streamlit-keyup`` dependency (see ``[project.optional-dependencies]``
    ``gui``) sends a value on each keyup. Without it, we fall back to
    ``st.text_input`` and document the need to press Enter or defocus.
    """
    try:
        from st_keyup import st_keyup
    except ImportError:
        if help:
            st.caption(help)
        v = st.text_input(
            label, key=key, placeholder=placeholder, help=help,
        )
        s = v if v is not None else st.session_state.get(key, "")
        return str(s) if s is not None else ""

    raw = st_keyup(
        label,
        key=key,
        placeholder=placeholder,
        debounce=debounce_ms,
    )
    if raw is not None:
        return str(raw)
    stored = st.session_state.get(key)
    if stored is None:
        return ""
    return str(stored)
