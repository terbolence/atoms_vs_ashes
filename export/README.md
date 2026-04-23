# Database Export Guide

## Unified Export Script

We now have **one comprehensive export script** that combines all previous functionality:

**`export_databases.py`** - The complete solution for all database exports

## Usage Examples

### Basic Export (Both Databases, Original Column Names)
```bash
python export/export_databases.py
```
- Exports both API and LLM databases
- Uses original column names  
- Auto-generates timestamp version
- Output: `export/exports_YYYYMMDD_HHMM/`

### Export for External Stakeholders (Clear Column Names)
```bash
python export/export_databases.py --clear-names
```
- Uses descriptive column names: `EXCL_NH_01_PeakGroundAccel475yr_VALUE_g`
- Includes "Column Mappings" reference sheet
- Output: `export/exports_clear_YYYYMMDD_HHMM/`

### Export Single Database
```bash
# API database only
python export/export_databases.py --database api

# LLM database only  
python export/export_databases.py --database llm
```

### Custom Version and Location
```bash
python export/export_databases.py \
    --version stakeholder_review_v1 \
    --output-dir /path/to/custom/location \
    --clear-names
```

## Features Included

### ✅ From Previous Scripts
- **Versioned exports** with organized folder structure (from `export_both_databases.py`)
- **Robust error handling** for missing columns/tables (from `export_with_fallback.py`)  
- **Clear naming convention** for external use (from `export_with_clear_naming.py`)

### ✅ New Unified Features
- **Single command** for all export scenarios
- **Flexible database selection** (api, llm, or both)
- **Optional clear naming** (off by default for backwards compatibility)
- **Comprehensive error reporting** and recovery
- **Excel formatting** (auto-fit columns, frozen headers)
- **Detailed summary files** with file sizes and configuration

### ✅ Robust Operation
- **Graceful fallback** when standard export methods fail
- **Schema difference handling** between API and LLM databases  
- **Missing table detection** and error reporting
- **Excel cell truncation warnings** for very long content
- **Automatic directory creation** and cleanup

## Output Structure

```
export/
├── exports_YYYYMMDD_HHMM/              # Standard export
│   ├── api/atoms_vs_ashes_api.xlsx
│   ├── llm/atoms_vs_ashes_llm.xlsx
│   └── export_summary.txt
├── exports_clear_YYYYMMDD_HHMM/        # Clear naming export  
│   ├── api/atoms_vs_ashes_api_clear.xlsx
│   ├── llm/atoms_vs_ashes_llm_clear.xlsx
│   └── export_summary.txt
└── export_databases.py                 # The unified script
```

## Excel Sheets Generated

Each Excel file contains:
1. **Sites** - Complete site data (363 sites, ~295 columns)
2. **Ownership** - Ownership relationships (~3,228 records)  
3. **Screening Verdicts** - Assessment results (11K-86K records depending on database)
4. **SMR Designs** - Reactor design specifications (8 designs)
5. **Column Mappings** - Reference for clear naming (only when `--clear-names` used)

## Error Handling

The script includes multiple fallback mechanisms:
- **Standard → Safe export methods** if primary export fails
- **Individual sheet error isolation** (one failure doesn't stop others)
- **Missing table detection** with graceful degradation  
- **Schema difference accommodation** between databases
- **Detailed error reporting** in summary files

## Migration from Old Scripts

**Old scripts removed:**
- ❌ `export_both_databases.py` 
- ❌ `export_with_fallback.py`
- ❌ `export_with_clear_naming.py`

**New equivalent commands:**
```bash
# Old: python export/export_both_databases.py
# New: python export/export_databases.py

# Old: python export/export_with_clear_naming.py  
# New: python export/export_databases.py --clear-names

# Old: python export/export_with_fallback.py
# New: python export/export_databases.py (fallback built-in)
```

## Documentation

- **Column naming convention**: See `NAMING_CONVENTION_GUIDE.md` and `.docx`
- **Technical details**: This README and script docstrings
- **Export summaries**: Generated automatically in each export folder

The unified script maintains full backwards compatibility while adding new capabilities and improved reliability.