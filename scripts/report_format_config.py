"""Load report layout settings from report_format.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docx.enum.text import WD_ALIGN_PARAGRAPH


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FORMAT_PATH = (
    REPO_ROOT
    / "report/version 1.02/output/report/writing plan/report_format.json"
)

ALIGNMENT_MAP = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
    "outer": WD_ALIGN_PARAGRAPH.CENTER,
}


@dataclass(frozen=True)
class ReportFormatConfig:
    """Parsed report_format.json with path helpers."""

    path: Path
    data: dict[str, Any]

    @classmethod
    def load(cls, path: Path | str | None = None) -> ReportFormatConfig:
        fmt_path = Path(path) if path is not None else DEFAULT_FORMAT_PATH
        with fmt_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        return cls(path=fmt_path.resolve(), data=data)

    @property
    def report_root(self) -> Path:
        return self.path.parent.parent

    def build_path(self, key: str) -> Path:
        return self.report_root / self.data["build"][key]

    @property
    def chapters_dir(self) -> Path:
        return self.report_root / "chapters"

    @property
    def annexes_dir(self) -> Path:
        return self.report_root / "annexes"

    def alignment(self, name: str) -> WD_ALIGN_PARAGRAPH:
        return ALIGNMENT_MAP[name]

    def font_family(self, key: str | None = None) -> str:
        if key is None:
            return str(self.data["default_font_family"])
        return str(self.data["typography"][key]["font_family"])

    def size_pt(self, *keys: str) -> float:
        node: Any = self.data["typography"]
        for key in keys:
            node = node[key]
        return float(node["size_pt"])

    def line_spacing(self, key: str) -> float:
        return float(self.data["typography"][key]["line_spacing"])

    def table_line_spacing(self) -> float:
        return float(self.data["tables"]["line_spacing"])

    def header_shade_hex(self) -> str:
        return str(self.data["tables"]["header_row"]["background_hex"])

    def table_vertical_rules(self) -> bool:
        return bool(self.data["tables"]["borders"]["vertical_rules"])

    def table_layout_autofit(self) -> bool:
        return self.data["tables"].get("layout") == "autofit_contents"

    def margins_mm(self) -> dict[str, float]:
        return {k: float(v) for k, v in self.data["page"]["margins_mm"].items()}
