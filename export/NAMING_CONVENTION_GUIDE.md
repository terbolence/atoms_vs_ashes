# Clear Naming Convention for External Stakeholder Exports

## Implementation Choice: Excel Export Only ✅

**Decision**: Implement the clear naming convention **only in the Excel export layer**, not in the database.

**Rationale**:
- ✅ **Database Integrity**: Preserves existing column names for backward compatibility
- ✅ **Maintenance**: Easier to update naming in one place (export layer)  
- ✅ **Flexibility**: Different export formats can use different naming schemes
- ✅ **Performance**: No database migration required
- ✅ **Risk Management**: Zero risk to existing application functionality

## Naming Convention Format

```
[PHASE]_[CATEGORY]_[CRITERION]_[MEASURE_NAME]_[MEASURE_TYPE]_[UNIT]
```

### Phase Codes (Screening Strategy)

| Code | Phase | Description |
|------|-------|-------------|
| `EXCL` | **Exclusionary** | Must pass to continue (go/no-go criteria) |
| `AVOID` | **Avoidance** | Prefer to avoid but not mandatory (penalties) |
| `RANK` | **Ranking** | Used for site comparison (scoring/optimization) |
| `FILTER` | **Basic Filter** | Preliminary screening (capacity, land area) |

### Category Codes (Technical Domain)

| Code | Category | Description |
|------|----------|-------------|
| `NH` | **Natural Hazard** | Earthquakes, floods, slope stability, etc. |
| `HI` | **Human Induced Hazard** | Aircraft, industrial explosions, toxic releases |
| `RI` | **Radiological Impact** | Population exposure, atmospheric dispersion |
| `EP` | **Emergency Planning** | Evacuation routes, special populations |
| `NS` | **Non-Safety/Infrastructure** | Grid, cooling, transport, site characteristics |

### Measure Types

| Type | Description | Examples |
|------|-------------|----------|
| `VALUE` | Raw measurement or calculated value | Distance, acceleration, population count |
| `QUALITY` | Data quality assessment | "high", "medium", "low", "insufficient" |
| `COMMENT` | Detailed explanatory text | Methodology notes, source details |
| `SOURCE` | Data source information | Dataset name, version, provider |

### Units (Self-Documenting)

| Unit | Meaning | Examples |
|------|---------|----------|
| `km` | Kilometers | Distance measurements |
| `g` | Gravity units | Seismic acceleration (PGA) |
| `per_km2` | Per square kilometer | Population density |
| `people` | Number of people | Population counts |
| `MW` | Megawatts | Power capacity |
| `kV` | Kilovolts | Electrical voltage |
| `score` | Dimensionless score | Composite assessments |
| `pct` | Percentage | Coverage, probability |
| `bool` | Boolean (true/false) | Binary flags |
| `text` | Text/categorical | Names, classifications |
| `none` | No unit | Quality assessments, comments |

## Example Transformations

### Before (Database Column) → After (Excel Column)

| Original Column | Clear Column Name | Description |
|----------------|-------------------|-------------|
| `pga_475yr_g` | `EXCL_NH_01_PeakGroundAccel475yr_VALUE_g` | Peak Ground Acceleration (475-year return period) |
| `nh01_quality` | `EXCL_NH_01_SeismicGroundMotion_QUALITY_none` | Seismic Ground Motion quality assessment |
| `nh01_comment` | `EXCL_NH_01_SeismicGroundMotion_COMMENT_none` | Seismic Ground Motion detailed comments |
| `nearest_airport_km` | `EXCL_HI_01_AirportDistance_VALUE_km` | Distance to nearest airport |
| `pop_density_5km` | `AVOID_RI_04_PopDensity5km_VALUE_per_km2` | Population density within 5km radius |
| `cooling_distance_km` | `RANK_NS_01_CoolingDistance_VALUE_km` | Distance to cooling water source |
| `ns01_quality` | `RANK_NS_01_CoolingWaterAvail_QUALITY_none` | Cooling Water Availability quality |

## Benefits for External Stakeholders

### 1. **Immediate Clarity**
- **Phase** tells you the decision-making role (must pass vs. preference vs. comparison)
- **Category** tells you the technical domain (natural vs. human hazards)
- **Criterion** maps to specific regulatory requirements (IAEA, NRC guidelines)
- **Unit** eliminates ambiguity about measurement scale

### 2. **Self-Documenting**
- No need to cross-reference with external documentation
- Column name contains complete context
- Sorting/filtering by prefix groups related columns

### 3. **Regulatory Alignment**
- Phase structure matches IAEA site evaluation methodology
- Categories align with nuclear safety assessment frameworks
- Criterion numbers reference established standards

## Column Mapping Reference

Each Excel export includes a **"Column Mappings"** sheet with:
- **Original_Column**: Database column name
- **Clear_Column_Name**: New descriptive name  
- **Description**: Full explanation of what the column represents

## Export Scripts

### 1. `export/export_with_clear_naming.py`
- **Primary script** with full clear naming implementation
- Includes column mapping reference sheet
- Creates versioned output folders

### 2. `export/export_both_databases.py` 
- **Standard export** with original column names
- Good for technical/internal use

### 3. `export/export_with_fallback.py`
- **Robust export** handling schema differences
- For databases with missing columns

## Usage Example

```bash
# Export with clear naming for external stakeholders
python export/export_with_clear_naming.py --version stakeholder_review_v1

# Export with original naming for technical team  
python export/export_both_databases.py --version internal_analysis_v2
```

## Quality Assurance

The system includes:
- **Automatic validation** of column mappings
- **Warning detection** for unmapped columns
- **Reference sheets** in each Excel file
- **Version tracking** for all exports
- **Size reporting** and completion status

## Future Extensions

The naming convention is designed to be extensible:
- **New phases**: Could add `MONITOR` for operational monitoring criteria
- **New categories**: Could add `CYBER` for cybersecurity assessments
- **New measures**: Could add `TREND` for time-series data
- **New units**: Can accommodate any measurement scale

This approach ensures that external stakeholders can immediately understand the purpose, context, and scale of every data column without requiring deep domain knowledge of the internal system architecture.