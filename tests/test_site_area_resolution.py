from atoms_vs_ashes.analysis.site_area_resolution import resolve_site_area_ha


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
