# man_hours: 2.5
import csv
import importlib.util
from pathlib import Path


def _load_script(name: str):
    path = Path(__file__).resolve().parents[2] / "src" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_audit_cli_writes_csv_from_recommendations(monkeypatch, tmp_path):
    module = _load_script("audit_site_area_confidence")
    out = tmp_path / "site_area.csv"

    monkeypatch.setattr(module, "fetch_site_rows", lambda **_: [{
        "site_id": "site-1",
        "name": "Doicesti power station",
        "country_code": "RO",
        "status": "cancelled",
        "installed_capacity_mw": 1400.0,
        "site_area_ha": 0.16,
        "buildable_area_ha": 0.16,
        "largest_contiguous_ha": 0.16,
        "favourable_area_ha": 49.32,
        "favourable_area_method": "comment_buildable_x_fav_pct",
        "ns05_quality": "high",
        "ns05_comment": "source=osm_overpass; tags=[man_made=works]; dist=0.40km",
        "llm_structured_ha": 40.0,
        "merge_audit_final_ha": 40.0,
        "llm_observation": (
            "Site area: 40 ha (buildable: 40 ha, expansion: 115 ha). "
            "Confidence: high. Sources: https://example.org/official-report"
        ),
        "llm_db_site_area_ha": None,
    }])
    monkeypatch.setattr(module, "load_manual_overrides", lambda _: {})

    assert module.main(["--out", str(out)]) == 0

    with out.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 1
    assert rows[0]["recommended_site_area_ha"] == "40.0"
    assert rows[0]["recommended_source"] in {"llm_web_observation", "llm_web_structured"}
    assert "S1" in rows[0]["review_flags"]
