<!-- man_hours: 0.3 -->
# Site Area Template Wiring Plan

**Status:** Completed — verified `site_area_ha` as canonical footprint and `favourable_area_ha` as expansion envelope; updated site/country/specialist writing controls.

## Task

Verify the correct field(s) for site area and favourable/developable area, then update the site-profile writing controls so every selected site discusses available development area using the correct data fields.

## Requirements

- Check whether `site_area_ha` and `favourable_area_ha` are real and appropriate fields.
- Interpret the fields correctly rather than assuming `favourable_area_ha` means total developable area.
- If the site template lacks a clear instruction, add it to the closest active site-profile template/prompt.
- Preserve the report's Stage 1-2 framing and avoid implying construction readiness.

## Steps

1. Search schema, bundle exporter, and site-profile renderer for `site_area_ha`, `favourable_area_ha`, `buildable_area_ha`, and related land-area fields.
2. Inspect the active site-profile prompt and relevant renderer/bundle logic.
3. Update the site-profile writing controls with the correct field names and interpretation.
4. Update audit/man-hours metadata, lint touched files, and record the change.
