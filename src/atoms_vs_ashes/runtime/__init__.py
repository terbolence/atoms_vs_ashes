# man_hours: 0.25
"""Runtime glue between configs (RunProfile, CriterionSpec) and the engine.

This package owns the loaders and orchestration helpers the GUI / CLI
call into. It deliberately depends on
:mod:`atoms_vs_ashes.criterion_spec` and :mod:`atoms_vs_ashes.scoring`
but *not* the other way around — keeping the import graph acyclic.
"""

from atoms_vs_ashes.runtime.cancellation import (
    CancellationRequested,
    CancellationToken,
    FileWatchedCancellationToken,
    install_sigint_handler,
)
from atoms_vs_ashes.runtime.heartbeat import HeartbeatRecord, HeartbeatWriter
from atoms_vs_ashes.runtime.loaders import (
    DEFAULT_SPEC_DIR,
    compile_rubric_with_overrides,
    load_compiled_rubric,
    load_rubric_with_overrides,
)
from atoms_vs_ashes.runtime.catalogue_scope import (
    scope_including_supplementary_catalogue,
    supplementary_site_statuses,
)
from atoms_vs_ashes.runtime.scope import RunScope, scope_from_run_profile

__all__ = [
    "CancellationRequested",
    "CancellationToken",
    "DEFAULT_SPEC_DIR",
    "FileWatchedCancellationToken",
    "HeartbeatRecord",
    "HeartbeatWriter",
    "RunScope",
    "compile_rubric_with_overrides",
    "install_sigint_handler",
    "load_compiled_rubric",
    "load_rubric_with_overrides",
    "scope_from_run_profile",
    "scope_including_supplementary_catalogue",
    "supplementary_site_statuses",
]
