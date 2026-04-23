# man_hours: 2.0
"""CI gate: every connector in ``MANDATORY_LOGGING_CONNECTORS`` must invoke
``log_raw_response`` (live HTTP) or ``log_raster_extraction`` (per-site
raster) from its ``batch.py``.

We use a static AST scan (cheap, deterministic, no I/O) backed by an import
check that confirms the logger symbol is actually bound in the module's
namespace.  This catches:

  * a connector being added to the registry but never wired up
  * the logger import being removed accidentally
  * a future "rewrite" that drops the call site

For an end-to-end smoke verification (logger invoked per site against a
mocked HTTP layer), see ``tests/integration/`` per-connector tests.

If this test fails for a new connector you authored, follow the integration
pattern documented in ``.cursor/rules/raw-response-logging.mdc``.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

from atoms_vs_ashes.connectors import MANDATORY_LOGGING_CONNECTORS

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _module_source_path(dotted_path: str) -> Path:
    """Resolve ``a.b.c`` to ``src/a/b/c.py``."""
    parts = dotted_path.split(".")
    return _PROJECT_ROOT.joinpath("src", *parts).with_suffix(".py")


def _calls_in_module(source: str, callee: str) -> list[ast.Call]:
    """Return every ``Call`` node whose target name matches ``callee``."""
    tree = ast.parse(source)
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name: str | None = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name == callee:
                calls.append(node)
    return calls


@pytest.mark.parametrize(
    "slug,spec",
    sorted(MANDATORY_LOGGING_CONNECTORS.items()),
    ids=sorted(MANDATORY_LOGGING_CONNECTORS.keys()),
)
def test_connector_calls_mandatory_logger(slug: str, spec: dict[str, str]) -> None:
    """Each registered connector must call its declared logger fn from batch.py."""
    logger_fn = spec["logger_fn"]
    batch_module = spec["batch_module"]

    assert logger_fn in {"log_raw_response", "log_raster_extraction"}, (
        f"Registry entry for {slug!r} declares unknown logger_fn={logger_fn!r}; "
        "only log_raw_response and log_raster_extraction are accepted."
    )

    src_path = _module_source_path(batch_module)
    assert src_path.is_file(), (
        f"Registered batch module for {slug!r} does not exist on disk: {src_path}. "
        "Update MANDATORY_LOGGING_CONNECTORS in src/atoms_vs_ashes/connectors/__init__.py."
    )

    source = src_path.read_text(encoding="utf-8")
    calls = _calls_in_module(source, logger_fn)
    assert calls, (
        f"Connector {slug!r} ({batch_module}) is registered as MANDATORY but its "
        f"batch module never calls {logger_fn}().  See "
        ".cursor/rules/raw-response-logging.mdc for the required integration pattern."
    )

    try:
        module = importlib.import_module(batch_module)
    except ModuleNotFoundError as exc:
        pytest.skip(
            f"Optional runtime dep missing for {slug}: {exc.name}; "
            f"AST check still passed."
        )
    assert hasattr(module, logger_fn), (
        f"Connector {slug!r} ({batch_module}) imports {logger_fn} but the symbol "
        "is not bound in the module namespace.  Did you import it from the right "
        "place?  Use 'from atoms_vs_ashes.connectors.response_logger import "
        f"{logger_fn}'."
    )


def test_registry_covers_every_per_site_connector_with_a_batch() -> None:
    """Sanity-check: every connector with a ``batch.py`` calling a logger
    must be registered.

    Walks ``src/atoms_vs_ashes/connectors/*/batch.py`` and asserts that any
    file invoking ``log_raw_response`` or ``log_raster_extraction`` is also
    listed in :data:`MANDATORY_LOGGING_CONNECTORS`.  Prevents silent drift
    where someone adds the helper to a new connector but forgets to register
    it for CI enforcement.
    """
    connectors_dir = _PROJECT_ROOT / "src" / "atoms_vs_ashes" / "connectors"
    registered_modules = {
        spec["batch_module"] for spec in MANDATORY_LOGGING_CONNECTORS.values()
    }

    missing: list[str] = []
    for batch_path in connectors_dir.glob("*/batch.py"):
        slug_dir = batch_path.parent.name
        rel = batch_path.relative_to(_PROJECT_ROOT / "src").with_suffix("")
        dotted = ".".join(rel.parts)
        try:
            text = batch_path.read_text(encoding="utf-8")
        except OSError:
            continue
        uses_logger = (
            "log_raw_response(" in text
            or "log_raster_extraction(" in text
        )
        if uses_logger and dotted not in registered_modules:
            missing.append(f"{slug_dir} ({dotted})")

    assert not missing, (
        "These connectors call the raw-response logger but are missing from "
        "MANDATORY_LOGGING_CONNECTORS:\n  - "
        + "\n  - ".join(sorted(missing))
        + "\nAdd each to src/atoms_vs_ashes/connectors/__init__.py so CI tracks them."
    )
