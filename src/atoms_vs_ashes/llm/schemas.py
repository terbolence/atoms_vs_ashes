"""Pydantic output schemas and Anthropic tool definitions for all 46 criteria.

Each criterion has:
- A Pydantic model validating the LLM's structured response.
- An ``anthropic_tool()`` class method returning the tool dict for the API call.
- A ``tier`` attribute (1=exclusionary, 2=avoidance, 3=ranking).
- A ``criterion_id`` linking to the DB criteria table.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from atoms_vs_ashes.llm.config import TIER_AVOIDANCE, TIER_EXCLUSIONARY, TIER_RANKING


# ---------------------------------------------------------------------------
# Base schemas
# ---------------------------------------------------------------------------

class _ExclusionaryBase(BaseModel):
    verdict: str = Field(..., pattern="^(pass|fail|inconclusive)$")
    confidence: str = Field(..., pattern="^(high|medium|low)$")
    justification: str
    data_quality: str = Field(..., pattern="^(high|medium|low)$")
    cited_sources: list[str] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)
    sources_needed: list[str] = Field(default_factory=list)

    tier: int = TIER_EXCLUSIONARY

    @classmethod
    def _base_props(cls) -> dict[str, Any]:
        return {
            "verdict": {"type": "string", "enum": ["pass", "fail", "inconclusive"]},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "justification": {
                "type": "string",
                "description": (
                    "3-6 sentences. Label each claim as FACT, INFERENCE, or UNKNOWN. "
                    "Include the specific distance measurement if applicable. "
                    "State the threshold and whether it is triggered."
                ),
            },
            "data_quality": {"type": "string", "enum": ["high", "medium", "low"]},
            "cited_sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "DEPRECATED — use sources_used instead. Kept for backward compatibility.",
            },
            "sources_used": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Data sources ACTUALLY USED in this assessment — enrichment data, "
                    "specific factual knowledge you applied. "
                    "If only LLM knowledge: 'LLM general knowledge — low confidence'."
                ),
            },
            "sources_needed": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Data sources that WOULD IMPROVE this assessment but were NOT available. "
                    "E.g., 'EDSF fault database — needed for precise fault distance'."
                ),
            },
        }

    @classmethod
    def _base_required(cls) -> list[str]:
        return ["verdict", "confidence", "justification", "data_quality", "sources_used", "sources_needed"]


class _AvoidanceBase(BaseModel):
    verdict: str = Field(..., pattern="^(pass|caution|inconclusive)$")
    confidence: str = Field(..., pattern="^(high|medium|low)$")
    justification: str
    data_quality: str = Field(..., pattern="^(high|medium|low)$")
    cited_sources: list[str] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)
    sources_needed: list[str] = Field(default_factory=list)

    tier: int = TIER_AVOIDANCE

    @classmethod
    def _base_props(cls) -> dict[str, Any]:
        return {
            "verdict": {"type": "string", "enum": ["pass", "caution", "inconclusive"]},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "justification": {
                "type": "string",
                "description": (
                    "2-4 sentences. State the measured/estimated distance, "
                    "the threshold, and whether it is triggered."
                ),
            },
            "data_quality": {"type": "string", "enum": ["high", "medium", "low"]},
            "cited_sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "DEPRECATED — use sources_used instead.",
            },
            "sources_used": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Data sources ACTUALLY USED in this assessment.",
            },
            "sources_needed": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Data sources that WOULD IMPROVE this assessment but were NOT available.",
            },
        }

    @classmethod
    def _base_required(cls) -> list[str]:
        return ["verdict", "confidence", "justification", "data_quality", "sources_used", "sources_needed"]


class _RankingBase(BaseModel):
    score: int = Field(..., ge=1, le=5)
    score_low: int | None = Field(None, ge=1, le=5)
    score_high: int | None = Field(None, ge=1, le=5)
    confidence: str = Field(..., pattern="^(high|medium|low)$")
    justification: str
    data_quality: str = Field(..., pattern="^(high|medium|low)$")
    cited_sources: list[str] = Field(default_factory=list)

    tier: int = TIER_RANKING

    @classmethod
    def _base_props(cls) -> dict[str, Any]:
        return {
            "score": {"type": "integer", "minimum": 1, "maximum": 5, "description": "1=Poor, 5=Excellent"},
            "score_low": {"type": ["integer", "null"], "minimum": 1, "maximum": 5, "description": "Lower bound estimate"},
            "score_high": {"type": ["integer", "null"], "minimum": 1, "maximum": 5, "description": "Upper bound estimate"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "justification": {
                "type": "string",
                "description": (
                    "2-3 sentences. State the key metric value, the rubric band "
                    "it falls into, and any uncertainty."
                ),
            },
            "data_quality": {"type": "string", "enum": ["high", "medium", "low"]},
            "cited_sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "References used. If none, write 'LLM general knowledge — low confidence'.",
            },
        }

    @classmethod
    def _base_required(cls) -> list[str]:
        return ["score", "confidence", "justification", "data_quality", "cited_sources"]


def _tool(name: str, desc: str, props: dict, required: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "description": desc,
        "input_schema": {"type": "object", "properties": props, "required": required},
    }


# ===================================================================
# TIER 1 — EXCLUSIONARY (E1-E9)
# ===================================================================

class E1CapableFault(_ExclusionaryBase):
    criterion_id: str = "NH-02"
    nearest_fault_name: str | None = None
    nearest_fault_km: float | None = None
    fault_slip_rate_mm_yr: float | None = None
    tectonic_context: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_fault_name": {"type": ["string", "null"]},
            "nearest_fault_km": {"type": ["number", "null"], "description": "Approx distance to nearest capable fault in km"},
            "fault_slip_rate_mm_yr": {"type": ["number", "null"]},
            "tectonic_context": {"type": "string", "description": "Regional seismotectonic summary (REQUIRED)"},
        })
        req = cls._base_required() + ["tectonic_context"]
        return _tool("record_e1_assessment", "Record capable fault proximity assessment (E1)", p, req)


class E2Liquefaction(_ExclusionaryBase):
    criterion_id: str = "NH-03"
    liquefaction_suscept: str | None = None
    soil_type: str | None = None
    groundwater_depth_m: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "liquefaction_suscept": {"type": ["string", "null"], "enum": ["none", "low", "moderate", "high", "very_high", None]},
            "soil_type": {"type": ["string", "null"]},
            "groundwater_depth_m": {"type": ["number", "null"]},
        })
        return _tool("record_e2_assessment", "Record liquefaction assessment (E2)", p, cls._base_required())


class E3SlopeInstability(_ExclusionaryBase):
    criterion_id: str = "NH-04"
    slope_angle_deg: float | None = None
    slope_stability_class: str | None = None
    landslide_inventory_notes: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "slope_angle_deg": {"type": ["number", "null"]},
            "slope_stability_class": {"type": ["string", "null"], "enum": ["stable", "moderate", "unstable", None]},
            "landslide_inventory_notes": {"type": ["string", "null"]},
        })
        return _tool("record_e3_assessment", "Record slope instability assessment (E3)", p, cls._base_required())


class E4Volcanism(_ExclusionaryBase):
    criterion_id: str = "NH-07"
    nearest_holocene_volcano_km: float | None = None
    volcano_name: str | None = None
    hazard_zone_type: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_holocene_volcano_km": {"type": "number", "description": "Distance to nearest Holocene volcano in km (REQUIRED, use 9999 if none in region)"},
            "volcano_name": {"type": ["string", "null"]},
            "hazard_zone_type": {"type": ["string", "null"], "description": "lava_flow / pyroclastic / lahar / none"},
        })
        req = cls._base_required() + ["nearest_holocene_volcano_km"]
        return _tool("record_e4_assessment", "Record volcanism assessment (E4)", p, req)


class E5Karst(_ExclusionaryBase):
    criterion_id: str = "NH-05"
    karst_present: bool | None = None
    karst_severity: str | None = None
    karst_formation_type: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "karst_present": {"type": ["boolean", "null"]},
            "karst_severity": {"type": ["string", "null"], "enum": ["none", "minor", "moderate", "massive", None]},
            "karst_formation_type": {
                "type": ["string", "null"],
                "description": "Bedrock type: 'none' (no karst-prone rock), 'limestone', 'dolomite', 'gypsum', 'evaporite', 'mixed_carbonate', or null if unknown. Use 'none' when site is on clastic/ignite rock.",
            },
        })
        return _tool("record_e5_assessment", "Record karst assessment (E5)", p, cls._base_required())


class E6Subsidence(_ExclusionaryBase):
    criterion_id: str = "NH-05b"
    mining_void_present: bool | None = None
    subsidence_risk_class: str | None = None
    collapse_mechanism: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "mining_void_present": {"type": ["boolean", "null"]},
            "subsidence_risk_class": {"type": ["string", "null"], "enum": ["none", "low", "moderate", "high", None]},
            "collapse_mechanism": {
                "type": ["string", "null"],
                "description": "Short phrase: 'open-pit surface mining', 'underground longwall', 'underground room-and-pillar', 'salt extraction', 'no mining', 'groundwater withdrawal', or null if unknown. Always fill when mining_void_present is not null.",
            },
        })
        return _tool("record_e6_assessment", "Record subsidence/collapse assessment (E6)", p, cls._base_required())


class E7ProtectedAreas(_ExclusionaryBase):
    criterion_id: str = "NS-08"
    in_protected_area: bool | None = None
    protected_area_name: str | None = None
    protected_area_type: str | None = None
    distance_to_boundary_km: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "in_protected_area": {"type": "boolean", "description": "Is the site inside a protected area? (REQUIRED)"},
            "protected_area_name": {"type": ["string", "null"]},
            "protected_area_type": {"type": ["string", "null"], "description": "natura_2000 / biosphere / unesco / national_park / none"},
            "distance_to_boundary_km": {"type": ["number", "null"]},
        })
        req = cls._base_required() + ["in_protected_area"]
        return _tool("record_e7_assessment", "Record protected areas assessment (E7)", p, req)


class E8EmergencyFeasibility(_ExclusionaryBase):
    criterion_id: str = "EP-01"
    road_access_adequate: bool | None = None
    population_density_concern: bool | None = None
    geographic_barriers: str | None = None
    institutional_capacity_notes: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "road_access_adequate": {"type": ["boolean", "null"]},
            "population_density_concern": {"type": ["boolean", "null"]},
            "geographic_barriers": {"type": ["string", "null"]},
            "institutional_capacity_notes": {"type": ["string", "null"]},
        })
        return _tool("record_e8_assessment", "Record emergency plan feasibility assessment (E8)", p, cls._base_required())


class E9CoolingWater(_ExclusionaryBase):
    criterion_id: str = "NS-01"
    cooling_source_type: str | None = None
    cooling_source_name: str | None = None
    cooling_distance_km: float | None = None
    estimated_flow_m3s: float | None = None
    dry_cooling_viable: bool | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "cooling_source_type": {"type": "string", "description": "river / lake / sea / reservoir / none (REQUIRED)"},
            "cooling_source_name": {"type": ["string", "null"]},
            "cooling_distance_km": {"type": ["number", "null"]},
            "estimated_flow_m3s": {"type": ["number", "null"]},
            "dry_cooling_viable": {"type": ["boolean", "null"]},
        })
        req = cls._base_required() + ["cooling_source_type"]
        return _tool("record_e9_assessment", "Record cooling water sufficiency assessment (E9)", p, req)


# ===================================================================
# TIER 2 — AVOIDANCE (A1-A15)
# ===================================================================

class A1FlightPath(_AvoidanceBase):
    criterion_id: str = "HI-01"
    nearest_flight_path_km: float | None = None
    airport_name: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_flight_path_km": {"type": ["number", "null"]},
            "airport_name": {"type": ["string", "null"]},
        })
        return _tool("record_a1_assessment", "Record flight path proximity assessment (A1)", p, cls._base_required())


class A2AirportType2(_AvoidanceBase):
    criterion_id: str = "HI-01"
    nearest_type2_airport_km: float | None = None
    airport_name: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_type2_airport_km": {"type": ["number", "null"]},
            "airport_name": {"type": ["string", "null"]},
        })
        return _tool("record_a2_assessment", "Record Type 2 airport proximity assessment (A2)", p, cls._base_required())


class A3SmallAirport(_AvoidanceBase):
    criterion_id: str = "HI-01"
    nearest_small_airport_km: float | None = None
    airport_name: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_small_airport_km": {"type": ["number", "null"]},
            "airport_name": {"type": ["string", "null"]},
        })
        return _tool("record_a3_assessment", "Record small airport proximity assessment (A3)", p, cls._base_required())


class A4LargeAirport(_AvoidanceBase):
    criterion_id: str = "HI-01"
    nearest_large_airport_km: float | None = None
    airport_name: str | None = None
    yearly_flight_ops: int | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_large_airport_km": {"type": ["number", "null"]},
            "airport_name": {"type": ["string", "null"]},
            "yearly_flight_ops": {"type": ["integer", "null"]},
        })
        return _tool("record_a4_assessment", "Record large airport proximity assessment (A4)", p, cls._base_required())


class A5MilitaryRanges(_AvoidanceBase):
    criterion_id: str = "HI-06"
    nearest_military_range_km: float | None = None
    facility_name: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_military_range_km": {"type": ["number", "null"]},
            "facility_name": {"type": ["string", "null"]},
        })
        return _tool("record_a5_assessment", "Record military range proximity assessment (A5)", p, cls._base_required())


class A6AmmunitionStorage(_AvoidanceBase):
    criterion_id: str = "HI-06"
    nearest_ammo_storage_km: float | None = None
    facility_name: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_ammo_storage_km": {"type": ["number", "null"]},
            "facility_name": {"type": ["string", "null"]},
        })
        return _tool("record_a6_assessment", "Record ammunition storage proximity assessment (A6)", p, cls._base_required())


class A7HazmatFacilities(_AvoidanceBase):
    criterion_id: str = "HI-02"
    nearest_hazmat_km: float | None = None
    facility_type: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_hazmat_km": {"type": ["number", "null"]},
            "facility_type": {"type": ["string", "null"]},
        })
        return _tool("record_a7_assessment", "Record hazardous material facility proximity assessment (A7)", p, cls._base_required())


class A8HazardousCloud(_AvoidanceBase):
    criterion_id: str = "HI-03"
    nearest_cloud_source_km: float | None = None
    source_type: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_cloud_source_km": {"type": ["number", "null"]},
            "source_type": {"type": ["string", "null"]},
        })
        return _tool("record_a8_assessment", "Record hazardous cloud source proximity assessment (A8)", p, cls._base_required())


class A9Tsunami(_AvoidanceBase):
    criterion_id: str = "NH-08"
    distance_to_coast_km: float | None = None
    elevation_amsl_m: float | None = None
    tsunami_risk: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "distance_to_coast_km": {"type": ["number", "null"]},
            "elevation_amsl_m": {"type": ["number", "null"]},
            "tsunami_risk": {"type": ["string", "null"], "enum": ["none", "low", "moderate", "high", None]},
        })
        return _tool("record_a9_assessment", "Record tsunami exposure assessment (A9)", p, cls._base_required())


class A10SeismicPGA(_AvoidanceBase):
    criterion_id: str = "NH-01"
    pga_475yr_g: float | None = None
    pga_2475yr_g: float | None = None
    within_smr_envelope: bool | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "pga_475yr_g": {"type": ["number", "null"], "description": "PGA at 475-year return period (g)"},
            "pga_2475yr_g": {"type": ["number", "null"], "description": "PGA at 2475-year return period (g)"},
            "within_smr_envelope": {"type": ["boolean", "null"]},
        })
        return _tool("record_a10_assessment", "Record seismic PGA avoidance assessment (A10)", p, cls._base_required())


class A11FloodRisk(_AvoidanceBase):
    criterion_id: str = "NH-09"
    flood_zone_class: str | None = None
    elevation_adequate: bool | None = None
    flood_defences_feasible: bool | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "flood_zone_class": {"type": ["string", "null"]},
            "elevation_adequate": {"type": ["boolean", "null"]},
            "flood_defences_feasible": {"type": ["boolean", "null"]},
        })
        return _tool("record_a11_assessment", "Record flood risk avoidance assessment (A11)", p, cls._base_required())


class A12PopulationDensity(_AvoidanceBase):
    criterion_id: str = "RI-04"
    estimated_pop_5km: int | None = None
    estimated_pop_density_5km: float | None = None
    exceeds_threshold: bool | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "estimated_pop_5km": {"type": ["integer", "null"]},
            "estimated_pop_density_5km": {"type": ["number", "null"]},
            "exceeds_threshold": {"type": ["boolean", "null"]},
        })
        return _tool("record_a12_assessment", "Record population density avoidance assessment (A12)", p, cls._base_required())


class A13GridAdequacy(_AvoidanceBase):
    criterion_id: str = "NS-02"
    grid_capacity_mw: float | None = None
    nearest_substation_km: float | None = None
    adequate_for_smr: bool | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "grid_capacity_mw": {"type": ["number", "null"]},
            "nearest_substation_km": {"type": ["number", "null"]},
            "adequate_for_smr": {"type": ["boolean", "null"]},
        })
        return _tool("record_a13_assessment", "Record grid adequacy avoidance assessment (A13)", p, cls._base_required())


class A14TransportAccess(_AvoidanceBase):
    criterion_id: str = "NS-03"
    heavy_haul_capable: bool | None = None
    nearest_rail_km: float | None = None
    nearest_highway_km: float | None = None
    nearest_waterway_km: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "heavy_haul_capable": {"type": ["boolean", "null"]},
            "nearest_rail_km": {"type": ["number", "null"]},
            "nearest_highway_km": {"type": ["number", "null"]},
            "nearest_waterway_km": {"type": ["number", "null"]},
        })
        return _tool("record_a14_assessment", "Record transport access avoidance assessment (A14)", p, cls._base_required())


class A15SiteArea(_AvoidanceBase):
    criterion_id: str = "NS-05"
    estimated_industrial_land_ha: float | None = None
    adequate_for_nuclear_island: bool | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "estimated_industrial_land_ha": {"type": ["number", "null"]},
            "adequate_for_nuclear_island": {"type": ["boolean", "null"]},
        })
        return _tool("record_a15_assessment", "Record site area adequacy assessment (A15)", p, cls._base_required())


# ===================================================================
# TIER 3 — RANKING (NH/HI/RI/EP/NS)
# ===================================================================

class NH01SeismicGM(_RankingBase):
    criterion_id: str = "NH-01"
    pga_475yr_g: float | None = None
    pga_2475yr_g: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "pga_475yr_g": {"type": ["number", "null"]},
            "pga_2475yr_g": {"type": ["number", "null"]},
        })
        return _tool("record_nh01_ranking", "Score seismic ground motion (NH-01)", p, cls._base_required())


class NH06Foundation(_RankingBase):
    criterion_id: str = "NH-06"
    bearing_capacity_kpa: float | None = None
    depth_to_bedrock_m: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "bearing_capacity_kpa": {"type": ["number", "null"]},
            "depth_to_bedrock_m": {"type": ["number", "null"]},
        })
        return _tool("record_nh06_ranking", "Score foundation conditions (NH-06)", p, cls._base_required())


class NH08CoastalFlood(_RankingBase):
    criterion_id: str = "NH-08"
    distance_to_coast_km: float | None = None
    storm_surge_risk: str | None = None
    tsunami_risk: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "distance_to_coast_km": {"type": ["number", "null"]},
            "storm_surge_risk": {"type": ["string", "null"]},
            "tsunami_risk": {"type": ["string", "null"]},
        })
        return _tool("record_nh08_ranking", "Score coastal flooding risk (NH-08)", p, cls._base_required())


class NH09RiverFlood(_RankingBase):
    criterion_id: str = "NH-09"
    flood_zone_class: str | None = None
    nearest_river_km: float | None = None
    dam_break_exposure: bool | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "flood_zone_class": {"type": ["string", "null"]},
            "nearest_river_km": {"type": ["number", "null"]},
            "dam_break_exposure": {"type": ["boolean", "null"]},
        })
        return _tool("record_nh09_ranking", "Score river flooding risk (NH-09)", p, cls._base_required())


class NH10ExtremeWinds(_RankingBase):
    criterion_id: str = "NH-10"
    max_wind_speed_ms: float | None = None
    tornado_risk: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "max_wind_speed_ms": {"type": ["number", "null"]},
            "tornado_risk": {"type": ["string", "null"]},
        })
        return _tool("record_nh10_ranking", "Score extreme wind conditions (NH-10)", p, cls._base_required())


class NH11ExtremePrecip(_RankingBase):
    criterion_id: str = "NH-11"
    extreme_precip_mm: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"extreme_precip_mm": {"type": ["number", "null"]}})
        return _tool("record_nh11_ranking", "Score extreme precipitation (NH-11)", p, cls._base_required())


class NH12ExtremeTemp(_RankingBase):
    criterion_id: str = "NH-12"
    extreme_temp_max_c: float | None = None
    extreme_temp_min_c: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "extreme_temp_max_c": {"type": ["number", "null"]},
            "extreme_temp_min_c": {"type": ["number", "null"]},
        })
        return _tool("record_nh12_ranking", "Score extreme temperatures (NH-12)", p, cls._base_required())


class NH13Wildfire(_RankingBase):
    criterion_id: str = "NH-13"
    wildfire_combustible_pct: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"wildfire_combustible_pct": {"type": ["number", "null"]}})
        return _tool("record_nh13_ranking", "Score wildfire risk (NH-13)", p, cls._base_required())


class NH14CombinedHazards(_RankingBase):
    criterion_id: str = "NH-14"
    combined_hazard_notes: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"combined_hazard_notes": {"type": ["string", "null"]}})
        return _tool("record_nh14_ranking", "Score combined natural hazards (NH-14)", p, cls._base_required())


class HI01Aviation(_RankingBase):
    criterion_id: str = "HI-01"
    nearest_airport_km: float | None = None
    nearest_airport_name: str | None = None
    airport_count: int | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_airport_km": {"type": ["number", "null"]},
            "nearest_airport_name": {"type": ["string", "null"]},
            "airport_count": {"type": ["integer", "null"]},
        })
        return _tool("record_hi01_ranking", "Score aviation hazard (HI-01)", p, cls._base_required())


class HI02IndustrialExplosions(_RankingBase):
    criterion_id: str = "HI-02"
    nearest_seveso_km: float | None = None
    nearest_industrial_km: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_seveso_km": {"type": ["number", "null"]},
            "nearest_industrial_km": {"type": ["number", "null"]},
        })
        return _tool("record_hi02_ranking", "Score industrial explosion hazard (HI-02)", p, cls._base_required())


class HI03ToxicReleases(_RankingBase):
    criterion_id: str = "HI-03"
    nearest_toxic_source_km: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"nearest_toxic_source_km": {"type": ["number", "null"]}})
        return _tool("record_hi03_ranking", "Score toxic release hazard (HI-03)", p, cls._base_required())


class HI04ExternalFires(_RankingBase):
    criterion_id: str = "HI-04"
    nearest_flammable_storage_km: float | None = None
    nearest_pipeline_km: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_flammable_storage_km": {"type": ["number", "null"]},
            "nearest_pipeline_km": {"type": ["number", "null"]},
        })
        return _tool("record_hi04_ranking", "Score external fire hazard (HI-04)", p, cls._base_required())


class HI05TransportHazards(_RankingBase):
    criterion_id: str = "HI-05"
    hazmat_route_distance_km: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"hazmat_route_distance_km": {"type": ["number", "null"]}})
        return _tool("record_hi05_ranking", "Score transport hazard (HI-05)", p, cls._base_required())


class HI06Military(_RankingBase):
    criterion_id: str = "HI-06"
    nearest_military_km: float | None = None
    nearest_military_name: str | None = None
    military_count: int | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_military_km": {"type": ["number", "null"]},
            "nearest_military_name": {"type": ["string", "null"]},
            "military_count": {"type": ["integer", "null"]},
        })
        return _tool("record_hi06_ranking", "Score military installation hazard (HI-06)", p, cls._base_required())


class HI07EMI(_RankingBase):
    criterion_id: str = "HI-07"
    nearest_transmitter_km: float | None = None
    transmitter_type: str | None = None
    transmitter_count: int | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_transmitter_km": {"type": ["number", "null"]},
            "transmitter_type": {"type": ["string", "null"]},
            "transmitter_count": {"type": ["integer", "null"]},
        })
        return _tool("record_hi07_ranking", "Score EMI hazard (HI-07)", p, cls._base_required())


class HI08NuclearInstallations(_RankingBase):
    criterion_id: str = "HI-08"
    nearest_nuclear_km: float | None = None
    nearest_nuclear_name: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_nuclear_km": {"type": ["number", "null"]},
            "nearest_nuclear_name": {"type": ["string", "null"]},
        })
        return _tool("record_hi08_ranking", "Score nearby nuclear installation impact (HI-08)", p, cls._base_required())


class RI01AtmosphericDispersion(_RankingBase):
    criterion_id: str = "RI-01"
    prevailing_wind_dir: str | None = None
    avg_wind_speed_ms: float | None = None
    mixing_height_m: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "prevailing_wind_dir": {"type": ["string", "null"]},
            "avg_wind_speed_ms": {"type": ["number", "null"]},
            "mixing_height_m": {"type": ["number", "null"]},
        })
        return _tool("record_ri01_ranking", "Score atmospheric dispersion conditions (RI-01)", p, cls._base_required())


class RI02SurfaceWater(_RankingBase):
    criterion_id: str = "RI-02"
    nearest_river_flow_m3s: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"nearest_river_flow_m3s": {"type": ["number", "null"]}})
        return _tool("record_ri02_ranking", "Score surface water dispersion (RI-02)", p, cls._base_required())


class RI03Groundwater(_RankingBase):
    criterion_id: str = "RI-03"
    aquifer_type: str | None = None
    groundwater_flow_dir: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "aquifer_type": {"type": ["string", "null"]},
            "groundwater_flow_dir": {"type": ["string", "null"]},
        })
        return _tool("record_ri03_ranking", "Score groundwater dispersion (RI-03)", p, cls._base_required())


class RI04PopulationDensity(_RankingBase):
    criterion_id: str = "RI-04"
    pop_density_5km: float | None = None
    pop_density_25km: float | None = None
    pop_total_80km: int | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "pop_density_5km": {"type": ["number", "null"]},
            "pop_density_25km": {"type": ["number", "null"]},
            "pop_total_80km": {"type": ["integer", "null"]},
        })
        return _tool("record_ri04_ranking", "Score population density at EPZ (RI-04)", p, cls._base_required())


class RI05PopulationCentres(_RankingBase):
    criterion_id: str = "RI-05"
    nearest_city_50k_km: float | None = None
    nearest_city_name: str | None = None
    nearest_city_pop: int | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_city_50k_km": {"type": ["number", "null"]},
            "nearest_city_name": {"type": ["string", "null"]},
            "nearest_city_pop": {"type": ["integer", "null"]},
        })
        return _tool("record_ri05_ranking", "Score distance to population centres (RI-05)", p, cls._base_required())


class RI06PopulationProjection(_RankingBase):
    criterion_id: str = "RI-06"
    pop_growth_rate_pct: float | None = None
    projected_pop_25km_60yr: int | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "pop_growth_rate_pct": {"type": ["number", "null"]},
            "projected_pop_25km_60yr": {"type": ["integer", "null"]},
        })
        return _tool("record_ri06_ranking", "Score population projections (RI-06)", p, cls._base_required())


class EP02EvacuationRoutes(_RankingBase):
    criterion_id: str = "EP-02"
    road_density_km_per_km2: float | None = None
    has_motorway_access: bool | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "road_density_km_per_km2": {"type": ["number", "null"]},
            "has_motorway_access": {"type": ["boolean", "null"]},
        })
        return _tool("record_ep02_ranking", "Score evacuation routes (EP-02)", p, cls._base_required())


class EP03GeographyConstraints(_RankingBase):
    criterion_id: str = "EP-03"
    major_river_barrier: bool | None = None
    waterway_count_epz: int | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "major_river_barrier": {"type": ["boolean", "null"]},
            "waterway_count_epz": {"type": ["integer", "null"]},
        })
        return _tool("record_ep03_ranking", "Score physical geography constraints (EP-03)", p, cls._base_required())


class EP04SpecialPopulations(_RankingBase):
    criterion_id: str = "EP-04"
    hospital_count_epz: int | None = None
    prison_count_epz: int | None = None
    care_home_count_epz: int | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "hospital_count_epz": {"type": ["integer", "null"]},
            "prison_count_epz": {"type": ["integer", "null"]},
            "care_home_count_epz": {"type": ["integer", "null"]},
        })
        return _tool("record_ep04_ranking", "Score special populations in EPZ (EP-04)", p, cls._base_required())


class EP05ConcurrentHazards(_RankingBase):
    criterion_id: str = "EP-05"
    concurrent_hazard_notes: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"concurrent_hazard_notes": {"type": ["string", "null"]}})
        return _tool("record_ep05_ranking", "Score concurrent hazard impact on emergency (EP-05)", p, cls._base_required())


class NS02GridConnection(_RankingBase):
    criterion_id: str = "NS-02"
    nearest_substation_km: float | None = None
    nearest_hv_line_km: float | None = None
    grid_export_capacity_mw: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_substation_km": {"type": ["number", "null"]},
            "nearest_hv_line_km": {"type": ["number", "null"]},
            "grid_export_capacity_mw": {"type": ["number", "null"]},
        })
        return _tool("record_ns02_ranking", "Score grid connection quality (NS-02)", p, cls._base_required())


class NS03TransportAccess(_RankingBase):
    criterion_id: str = "NS-03"
    nearest_highway_km: float | None = None
    nearest_rail_km: float | None = None
    nearest_waterway_km: float | None = None
    heavy_haul_capable: bool | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "nearest_highway_km": {"type": ["number", "null"]},
            "nearest_rail_km": {"type": ["number", "null"]},
            "nearest_waterway_km": {"type": ["number", "null"]},
            "heavy_haul_capable": {"type": ["boolean", "null"]},
        })
        return _tool("record_ns03_ranking", "Score transport access (NS-03)", p, cls._base_required())


class NS04SiteTopography(_RankingBase):
    criterion_id: str = "NS-04"
    dominant_land_class: str | None = None
    favourable_land_pct: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "dominant_land_class": {"type": ["string", "null"]},
            "favourable_land_pct": {"type": ["number", "null"]},
        })
        return _tool("record_ns04_ranking", "Score site topography (NS-04)", p, cls._base_required())


class NS05LandAvailability(_RankingBase):
    criterion_id: str = "NS-05"
    buildable_area_ha: float | None = None
    largest_contiguous_ha: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "buildable_area_ha": {"type": ["number", "null"]},
            "largest_contiguous_ha": {"type": ["number", "null"]},
        })
        return _tool("record_ns05_ranking", "Score land availability (NS-05)", p, cls._base_required())


class NS06ExistingInfra(_RankingBase):
    criterion_id: str = "NS-06"
    reusable_infra_score: int | None = None
    reusable_assets: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "reusable_infra_score": {"type": ["integer", "null"], "minimum": 1, "maximum": 5},
            "reusable_assets": {"type": ["string", "null"]},
        })
        return _tool("record_ns06_ranking", "Score existing reusable infrastructure (NS-06)", p, cls._base_required())


class NS07EnvImpact(_RankingBase):
    criterion_id: str = "NS-07"
    env_impact_notes: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"env_impact_notes": {"type": ["string", "null"]}})
        return _tool("record_ns07_ranking", "Score non-radiological environmental impact (NS-07)", p, cls._base_required())


class NS08EcologicalSensitivity(_RankingBase):
    criterion_id: str = "NS-08"
    ecological_natural_pct: float | None = None
    ecological_patch_count: int | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "ecological_natural_pct": {"type": ["number", "null"]},
            "ecological_patch_count": {"type": ["integer", "null"]},
        })
        return _tool("record_ns08_ranking", "Score ecological sensitivity (NS-08)", p, cls._base_required())


class NS09Socioeconomic(_RankingBase):
    criterion_id: str = "NS-09"
    socioeconomic_notes: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"socioeconomic_notes": {"type": ["string", "null"]}})
        return _tool("record_ns09_ranking", "Score socioeconomic impact (NS-09)", p, cls._base_required())


class NS10Workforce(_RankingBase):
    criterion_id: str = "NS-10"
    workforce_notes: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"workforce_notes": {"type": ["string", "null"]}})
        return _tool("record_ns10_ranking", "Score workforce availability (NS-10)", p, cls._base_required())


class NS11CoalNuclearSynergy(_RankingBase):
    criterion_id: str = "NS-11"
    synergy_notes: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"synergy_notes": {"type": ["string", "null"]}})
        return _tool("record_ns11_ranking", "Score coal-to-nuclear synergies (NS-11)", p, cls._base_required())


class NS12RegulatoryPolitical(_RankingBase):
    criterion_id: str = "NS-12"
    regulatory_notes: str | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({"regulatory_notes": {"type": ["string", "null"]}})
        return _tool("record_ns12_ranking", "Score regulatory/political environment (NS-12)", p, cls._base_required())


class NS13ConstructionLogistics(_RankingBase):
    criterion_id: str = "NS-13"
    laydown_suitable_ha: float | None = None
    laydown_largest_patch_ha: float | None = None

    @classmethod
    def anthropic_tool(cls) -> dict[str, Any]:
        p = cls._base_props()
        p.update({
            "laydown_suitable_ha": {"type": ["number", "null"]},
            "laydown_largest_patch_ha": {"type": ["number", "null"]},
        })
        return _tool("record_ns13_ranking", "Score construction logistics (NS-13)", p, cls._base_required())


# ===================================================================
# Registry — maps prompt key → schema class
# ===================================================================

PROMPT_REGISTRY: dict[str, type] = {
    "E1": E1CapableFault,
    "E2": E2Liquefaction,
    "E3": E3SlopeInstability,
    "E4": E4Volcanism,
    "E5": E5Karst,
    "E6": E6Subsidence,
    "E7": E7ProtectedAreas,
    "E8": E8EmergencyFeasibility,
    "E9": E9CoolingWater,
    "A1": A1FlightPath,
    "A2": A2AirportType2,
    "A3": A3SmallAirport,
    "A4": A4LargeAirport,
    "A5": A5MilitaryRanges,
    "A6": A6AmmunitionStorage,
    "A7": A7HazmatFacilities,
    "A8": A8HazardousCloud,
    "A9": A9Tsunami,
    "A10": A10SeismicPGA,
    "A11": A11FloodRisk,
    "A12": A12PopulationDensity,
    "A13": A13GridAdequacy,
    "A14": A14TransportAccess,
    "A15": A15SiteArea,
    "NH-01": NH01SeismicGM,
    "NH-06": NH06Foundation,
    "NH-08": NH08CoastalFlood,
    "NH-09": NH09RiverFlood,
    "NH-10": NH10ExtremeWinds,
    "NH-11": NH11ExtremePrecip,
    "NH-12": NH12ExtremeTemp,
    "NH-13": NH13Wildfire,
    "NH-14": NH14CombinedHazards,
    "HI-01": HI01Aviation,
    "HI-02": HI02IndustrialExplosions,
    "HI-03": HI03ToxicReleases,
    "HI-04": HI04ExternalFires,
    "HI-05": HI05TransportHazards,
    "HI-06": HI06Military,
    "HI-07": HI07EMI,
    "HI-08": HI08NuclearInstallations,
    "RI-01": RI01AtmosphericDispersion,
    "RI-02": RI02SurfaceWater,
    "RI-03": RI03Groundwater,
    "RI-04": RI04PopulationDensity,
    "RI-05": RI05PopulationCentres,
    "RI-06": RI06PopulationProjection,
    "EP-02": EP02EvacuationRoutes,
    "EP-03": EP03GeographyConstraints,
    "EP-04": EP04SpecialPopulations,
    "EP-05": EP05ConcurrentHazards,
    "NS-02": NS02GridConnection,
    "NS-03": NS03TransportAccess,
    "NS-04": NS04SiteTopography,
    "NS-05": NS05LandAvailability,
    "NS-06": NS06ExistingInfra,
    "NS-07": NS07EnvImpact,
    "NS-08": NS08EcologicalSensitivity,
    "NS-09": NS09Socioeconomic,
    "NS-10": NS10Workforce,
    "NS-11": NS11CoalNuclearSynergy,
    "NS-12": NS12RegulatoryPolitical,
    "NS-13": NS13ConstructionLogistics,
}

EXCLUSIONARY_KEYS = [f"E{i}" for i in range(1, 10)]
AVOIDANCE_KEYS = [f"A{i}" for i in range(1, 16)]
RANKING_KEYS = [k for k in PROMPT_REGISTRY if k not in EXCLUSIONARY_KEYS + AVOIDANCE_KEYS]
ALL_KEYS = EXCLUSIONARY_KEYS + AVOIDANCE_KEYS + RANKING_KEYS
