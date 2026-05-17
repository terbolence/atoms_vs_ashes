<!-- man_hours: 0.2 -->
# Cartographic Assets

Vendored Natural Earth Vector data used by the report's static map
basemap. Source: https://github.com/nvkelso/natural-earth-vector
(public domain).

| File | Source | Use |
| --- | --- | --- |
| `ne_50m_admin_0_countries.geojson` | Natural Earth 1:50m Admin 0 | Country boundary polygons drawn under site markers when OSM tiles are unavailable. |
| `ne_50m_coastline.geojson` | Natural Earth 1:50m Physical Coastline | S-38 coast-distance source for NH-08 coastal flooding and tsunami screening. |
| `ne_50m_populated_places_simple.geojson` | Natural Earth 1:50m Populated Places (simple) | City dots and labels used as offline geographic context. |

These files are vendored so the static maps can be regenerated
offline (per `live-api-safety` workspace rule). The OSM tile path in
`src/atoms_vs_ashes/cartography/basemap.py` is preferred when network
is available; these files are the deterministic fallback.
