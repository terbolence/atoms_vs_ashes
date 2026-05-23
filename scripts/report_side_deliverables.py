# man_hours: 0.8
"""Build the report's side deliverables.

The results table is always produced by ``build_results_table_deliverable``,
which regenerates ``atoms_vs_ashes_results_table.{md,csv,docx}`` from ledgers.
"""

from __future__ import annotations

from report_format_config import ReportFormatConfig
from build_results_table_deliverable import build_results_table_deliverable
from build_work_audit_synthesis import build_work_audit_synthesis


def build_side_deliverables(fmt: ReportFormatConfig) -> None:
    print("Building side deliverable: results table (ledger -> md/csv/docx) ...")
    results_stats = build_results_table_deliverable(
        format_path=fmt.path,
        output_dir=fmt.report_root / "build",
    )
    print(
        "Wrote results table: "
        f"{results_stats['docx']} "
        f"({results_stats['selected_site_rows']} site rows, "
        f"{results_stats['copied_maps']} maps)"
    )

    print("Building side deliverable: work-audit synthesis ...")
    audit_stats = build_work_audit_synthesis(
        format_path=fmt.path,
        output_dir=fmt.report_root / "build",
    )
    print(
        "Wrote work-audit synthesis: "
        f"{audit_stats['docx']} "
        f"({audit_stats['expert_viewpoints']} expert viewpoints)"
    )
