# man_hours: 5.0
from atoms_vs_ashes.analysis.site_area_resolution import (
    SiteAreaContext,
    build_site_area_recommendation,
    parse_site_area_observation,
    resolve_site_area_ha,
)


def test_llm_wins_when_larger_than_ten():
    result = resolve_site_area_ha(llm_ha=40.0, api_footprint_ha=25.0, favourable_area_ha=80.0)

    assert result.value_ha == 40.0
    assert result.source == "llm"


def test_api_wins_when_llm_is_small():
    result = resolve_site_area_ha(llm_ha=10.0, api_footprint_ha=25.0, favourable_area_ha=80.0)

    assert result.value_ha == 25.0
    assert result.source == "api_footprint"


def test_favourable_wins_when_llm_and_api_are_small():
    result = resolve_site_area_ha(llm_ha=0.5, api_footprint_ha=9.5, favourable_area_ha=80.0)

    assert result.value_ha == 80.0
    assert result.source == "favourable_area"


def test_doicesti_like_case_uses_llm():
    result = resolve_site_area_ha(llm_ha=40.0, api_footprint_ha=0.16, favourable_area_ha=49.32)

    assert result.value_ha == 40.0
    assert result.source == "llm"


def test_all_null_is_unidentified():
    result = resolve_site_area_ha(llm_ha=None, api_footprint_ha=None, favourable_area_ha=None)

    assert result.value_ha is None
    assert result.source == "unidentified"
    assert result.observation == "area could not be identified"


def test_all_zero_is_explicit_zero():
    result = resolve_site_area_ha(llm_ha=0.0, api_footprint_ha=0.0, favourable_area_ha=0.0)

    assert result.value_ha == 0.0
    assert result.source == "explicit_zero"


def test_all_present_values_below_one_are_unidentified():
    result = resolve_site_area_ha(llm_ha=0.4, api_footprint_ha=0.16, favourable_area_ha=0.9)

    assert result.value_ha is None
    assert result.source == "unidentified"
    assert result.observation == "area could not be identified"


def test_one_to_ten_band_writes_favourable_area_when_available():
    result = resolve_site_area_ha(llm_ha=None, api_footprint_ha=0.5, favourable_area_ha=7.0)

    assert result.value_ha == 7.0
    assert result.source == "favourable_band"


def test_one_to_ten_band_falls_back_to_max_present_without_favourable():
    result = resolve_site_area_ha(llm_ha=4.0, api_footprint_ha=8.0, favourable_area_ha=None)

    assert result.value_ha == 8.0
    assert result.source == "max_residual"


def test_v2_manual_verified_wins_and_records_favourable_as_context_only():
    context = SiteAreaContext(
        site_id="aff5ffe6-fe7a-4de7-afad-9d4645a64cd9",
        name="Doicesti power station",
        status="cancelled",
        current_site_area_ha=0.16,
        favourable_area_ha=49.32,
        merge_audit_final_ha=40.0,
        llm_observation=parse_site_area_observation(
            "[NS-05 web_search] Site area: 40 ha (buildable: 40 ha, expansion: 115 ha). "
            "Confidence: high. Sources: https://example.org/official-report"
        ),
    )

    result = build_site_area_recommendation(
        context,
        manual_verified_ha=40.0,
        manual_note="user confirmed Doicesti known site area",
        llm_structured_ha=40.0,
    )

    assert result.proposed_site_area_ha == 40.0
    assert result.source == "manual_verified"
    assert result.confidence_tier == "high"
    assert result.write_eligible is True
    assert result.regional_developable_ha == 49.32
    assert result.expansion_potential_ha == 115.0


def test_v2_favourable_area_can_inform_low_confidence_site_envelope():
    context = SiteAreaContext(
        site_id="site-1",
        name="No footprint site",
        status="operating",
        installed_capacity_mw=100.0,
        current_site_area_ha=0.4,
        favourable_area_ha=80.0,
        ns05_comment="source=osm_overpass; tags=[name=shed]; dist=1.8km",
    )

    result = build_site_area_recommendation(context)

    assert result.proposed_site_area_ha == 60.0
    assert result.source == "favourable_envelope_inference"
    assert result.confidence_tier == "low"
    assert result.write_eligible is True
    assert result.regional_developable_ha == 80.0
    assert any(candidate.source == "capacity_bounded_inference" for candidate in result.candidates)


def test_v2_cited_llm_observation_can_replace_tiny_osm_polygon():
    context = SiteAreaContext(
        site_id="site-2",
        name="Mintia-like power station",
        status="retired",
        current_site_area_ha=0.01,
        favourable_area_ha=131.99,
        merge_audit_final_ha=329.78,
        ns05_comment="source=osm_overpass; tags=[power=plant]; dist=0.67km",
        llm_observation=parse_site_area_observation(
            "Site area: 329.78 ha (buildable: 329.78 ha, expansion: 0 ha). "
            "Confidence: high. Sources: https://example.org/cadastral-auction"
        ),
    )

    result = build_site_area_recommendation(context, llm_structured_ha=329.78)

    assert result.proposed_site_area_ha == 329.78
    assert result.source in {"llm_web_observation", "llm_web_structured"}
    assert result.confidence_tier in {"high", "medium"}
    assert result.write_eligible is True
    assert "S1" in result.review_flags
    assert "S2" in result.review_flags


def test_v2_trusted_osm_polygon_can_be_selected():
    context = SiteAreaContext(
        site_id="site-3",
        name="Trusted OSM plant",
        status="operating",
        current_site_area_ha=65.0,
        buildable_area_ha=65.0,
        largest_contiguous_ha=64.0,
        ns05_quality="high",
        ns05_comment="source=osm_overpass; tags=[power=plant]; dist=0.10km",
    )

    result = build_site_area_recommendation(context)

    assert result.proposed_site_area_ha == 65.0
    assert result.source == "osm_polygon"
    assert result.write_eligible is True


def test_v2_never_built_observation_does_not_force_zero_when_land_evidence_exists():
    context = SiteAreaContext(
        site_id="site-4",
        name="Porto Romano Power Station",
        status="cancelled",
        installed_capacity_mw=800.0,
        current_site_area_ha=5.75,
        largest_contiguous_ha=616.36,
        favourable_area_ha=42.12,
        merge_audit_final_ha=42.12,
        llm_observation=parse_site_area_observation(
            "Site area: 0 ha (buildable: 0 ha, expansion: 0 ha). Confidence: high. "
            "The project was cancelled and never constructed; no physical power plant site exists."
        ),
    )

    result = build_site_area_recommendation(context, llm_structured_ha=5.75)

    assert result.proposed_site_area_ha == 64.0
    assert result.source == "contiguous_capped_inference"
    assert result.confidence_tier == "review"
    assert "S8" in result.review_flags
    assert result.write_eligible is True


def test_v2_never_built_can_select_zero_when_no_land_evidence_exists():
    context = SiteAreaContext(
        site_id="site-5",
        name="Paper-only cancelled project",
        status="cancelled",
        llm_observation=parse_site_area_observation(
            "Site area: 0 ha (buildable: 0 ha, expansion: 0 ha). Confidence: high. "
            "The project was cancelled before construction; no physical site exists."
        ),
    )

    result = build_site_area_recommendation(context)

    assert result.proposed_site_area_ha == 0.0
    assert result.source == "cancelled_zero"
    assert result.write_eligible is True


def test_v2_meda_uses_buildable_area_and_caps_inconsistent_contiguous():
    context = SiteAreaContext(
        site_id="meda",
        name="Meda power station",
        status="operating",
        installed_capacity_mw=770.0,
        buildable_area_ha=200.55,
        largest_contiguous_ha=622.18,
        favourable_area_ha=82.25,
    )

    result = build_site_area_recommendation(context)

    assert result.proposed_site_area_ha == 200.55
    assert result.source == "buildable_area_inference"
    assert result.confidence_tier == "review"
    assert "S3" in result.review_flags
    assert any(
        candidate.source == "contiguous_capped_inference" and candidate.value_ha == 200.55
        for candidate in result.candidates
    )


def test_v2_karapinar_uses_large_buildable_envelope_not_unidentified():
    context = SiteAreaContext(
        site_id="karapinar",
        name="Karapinar Konya Seker power station",
        status="operating",
        installed_capacity_mw=2000.0,
        current_site_area_ha=5.09,
        buildable_area_ha=312.24,
        largest_contiguous_ha=1247.24,
        favourable_area_ha=243.52,
    )

    result = build_site_area_recommendation(context)

    assert result.proposed_site_area_ha == 312.24
    assert result.source == "buildable_area_inference"
    assert result.write_eligible is True
    assert "S3" in result.review_flags


def test_v2_luminer_falls_back_to_capacity_bounded_estimate():
    context = SiteAreaContext(
        site_id="luminer",
        name="Luminer Enerji power station",
        status="operating",
        installed_capacity_mw=160.0,
        current_site_area_ha=0.02,
        buildable_area_ha=0.02,
        largest_contiguous_ha=0.02,
        favourable_area_ha=0.0,
    )

    result = build_site_area_recommendation(context)

    assert result.proposed_site_area_ha == 12.8
    assert result.source == "capacity_bounded_inference"
    assert result.confidence_tier == "low"
    assert "S9" in result.selected_candidate.flags


def test_v2_zabrze_uses_discounted_favourable_envelope_with_capacity_context():
    context = SiteAreaContext(
        site_id="zabrze",
        name="Zabrze power station",
        status="retired",
        installed_capacity_mw=108.0,
        current_site_area_ha=5.06,
        favourable_area_ha=94.48,
    )

    result = build_site_area_recommendation(context)

    assert result.proposed_site_area_ha == 70.86
    assert result.source == "favourable_envelope_inference"
    assert result.confidence_tier == "low"
    assert any(candidate.source == "capacity_bounded_inference" for candidate in result.candidates)
