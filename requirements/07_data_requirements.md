## 9. Data Requirements and Databases

### 9.1 Data Categories

Per IAEA SSG-35 §5.8 and the Appendix to SSG-35, the following data categories shall be compiled for each potential/candidate site:

| # | Data Category | SSG-35 Ref | Key Data Elements |
|---|---|---|---|
| 1 | Geological | §A.3–A.6 | Regional geological maps, stratigraphy, cross-sections, tectonic maps, satellite imagery, borehole logs |
| 2 | Hydrogeological | §A.3–A.6 | Groundwater maps, aquifer characteristics, flow direction, water table depth |
| 3 | Seismological | §A.7–A.9 | Earthquake catalogues (historical and instrumental), seismic source zones, PGA maps, hazard curves |
| 4 | Fault Displacement | §A.10–A.12 | Capable fault maps, geomorphological surveys, slip rates, paleoseismic data |
| 5 | Volcanological | §A.13–A.15 | Holocene volcano locations, eruption histories, volcanic product hazard zones |
| 6 | Geotechnical | §A.16–A.18 | Soil classification, bearing capacity, liquefaction susceptibility, slope maps |
| 7 | Coastal Flooding | §A.19–A.27 | Tidal data, storm surge records, tsunami catalogues, shoreline stability |
| 8 | River Flooding | §A.28–A.30 | Discharge/level records, flood extent maps, dam inventories, ice hazard data |
| 9 | Meteorological | §A.31–A.33 | Temperature, precipitation, wind speed/direction, extreme event records, climate projections |
| 10 | Human Induced Events | §A.34–A.37 | Industrial facility locations, transport routes, air traffic data, military installations |
| 11 | Population & Land Use | §A.38–A.41 | Census data, population projections, land use maps, water use, protected areas, emergency infrastructure |

### 9.2 Database Sources

| Data Need | Primary Database(s) | Access Method | Coverage | Notes |
|---|---|---|---|---|
| **Coal plant inventory** | Global Energy Monitor — Global Coal Plant Tracker | CSV/XLSX download | Global, 108 countries | Updated bi-annually |
| | Beyond Fossil Fuels — Europe Coal Database | Web download | EU + Western Balkans | Retirement timelines |
| **Seismicity** | USGS Earthquake Hazards Program | REST API | Global | Real-time and historical catalogues |
| | European-Mediterranean Seismological Centre (EMSC) | REST API / CSV | Euro-Med region | Regional seismicity |
| | GEM Global Earthquake Model | GIS datasets | Global | Hazard maps, PGA data |
| | SHARE European Seismic Hazard Model | WMS/WFS | Europe | Probabilistic hazard maps |
| **Geology/Tectonics** | OneGeology (IUGS/CGI) | WMS/WFS | Global | Geological maps |
| | European Geological Data Infrastructure (EGDI) | WMS/API | Europe | Geological surveys, boreholes |
| | National geological surveys (per country) | Variable | Per country | High-resolution local data |
| **Flooding** | EU Flood Risk Maps (Floods Directive 2007/60/EC) | INSPIRE WMS/WFS | EU member states | Flood extent, depth, return period |
| | Copernicus Emergency Management Service | GIS download | Europe | Historical flood footprints |
| | Global Flood Monitoring System (GFMS) | Web/API | Global | Near-real-time flood data |
| **Meteorology** | Copernicus Climate Data Store (CDS) / ERA5 | CDS API (Python) | Global | Reanalysis data: temperature, wind, precipitation |
| | NOAA NCEI | API/FTP | Global | Extreme weather records |
| | National meteorological services | Variable | Per country | Station-based observations |
| **Population** | Eurostat (GISCO) | REST API / Bulk download | EU | Census data, population grids |
| | WorldPop | GeoTIFF download | Global | High-resolution population density |
| | LandScan (ORNL) | GeoTIFF download | Global | Ambient population distribution |
| **Land Use/Environment** | CORINE Land Cover (Copernicus) | WMS/WFS | Europe | Land use/land cover at 100m |
| | Natura 2000 Network (EEA) | GIS download | EU | Protected areas |
| | World Database on Protected Areas (WDPA) | API/Download | Global | UNESCO, RAMSAR, national parks |
| **Grid Infrastructure** | ENTSO-E Transparency Platform | REST API | Europe | Generation, cross-border flows |
| | OpenStreetMap (power=*) | Overpass API | Global | Transmission lines, substations |
| | National TSO data | Variable | Per country | Detailed grid maps |
| **Transport** | OpenStreetMap | Overpass API | Global | Road/rail networks |
| | Inland waterways databases (national) | Variable | Per country | Navigability, draft limits |
| **Volcanism** | Smithsonian Global Volcanism Program | Web/API | Global | Holocene volcano database |
| **Industrial Hazards** | EU-SEVESO III Directive facility registers | National registers | EU | Major accident hazard facilities |
| | OpenStreetMap (industrial=*) | Overpass API | Global | Industrial facility locations |
| **Satellite Imagery** | Copernicus Sentinel Hub | API | Global | Optical and radar imagery |
| | Google Earth Engine | Python API | Global | Multi-temporal analysis |

### 9.3 Data Quality Assessment

Per IAEA SSG-35 §5.5–5.7, each dataset shall be assessed for:

| Quality Dimension | Assessment Method |
|---|---|
| **Completeness** | Fraction of required data fields populated |
| **Spatial Resolution** | Comparison of dataset resolution vs. required resolution for the siting phase |
| **Temporal Coverage** | Length of historical record; suitability for return period estimation |
| **Currency** | Date of last update; relevance to current conditions |
| **Provenance** | Authoritative source verification; peer review or regulatory acceptance |
| **Uncertainty** | Known measurement errors, interpolation artefacts, model assumptions |

A data quality flag (High / Medium / Low / Insufficient) shall be assigned to each dataset per site. Where data quality is Insufficient, the impact on the screening/ranking decision shall be explicitly documented, and the site shall carry a conditional assessment flag pending additional data collection.

### 9.4 Limitations and Data Gaps

The study shall document all known limitations, including:

1. Non-EU countries (Serbia, Armenia) may have less comprehensive publicly accessible datasets for flood risk, seismic hazard, and land use.
2. Encrypted or restricted EPRI documents may limit direct citation of EPRI methodology details.
3. National-language databases may require translation and interpretation.
4. Some coal plant sites may lack publicly available detailed site plans and environmental monitoring baselines.
5. Military installation locations may be classified or incomplete in open sources.

Mitigation measures for each limitation shall be documented, including fallback data sources and conservative assumptions where data is absent.
