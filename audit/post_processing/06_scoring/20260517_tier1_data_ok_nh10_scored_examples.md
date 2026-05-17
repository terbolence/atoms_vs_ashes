<!-- man_hours: 0.5 -->
# NH-10 Extreme Winds Scored Site Examples

Generated read-only from the local DB using `src/scripts/generate_scoring_examples.py`. The table shows real site rows and the scoring-engine output for the current working-tree bands.

## Scored examples — NH-10 (merged DB)

Two sites per band, picked by lowest + median max_wind_speed_ms within the band.

| band | site | site_id | country | lat | lon | max_wind_speed_ms | nh10_quality | nh10_comment | run_id | fetched_at | score | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9-10 | Rovinari power station | 958e4d82 | RO | 44.9106 | 23.1348 | 5.41 | medium | ERA5 wind assessment (ref 1991-2020) \| 50yr_gust=5.4m/s \| max_gust=5.6m/s \| 99p=5.0m/s \| prevailing=0deg \| tropical_idx=0.0 \| gev=ok \| grid_dist=13.5km \| source=copernicus_era5 | 20260512T184804_724e6d22 | 2026-05-12 22:22:36.902950+03:00 | 9.5 | pass |
| 9-10 | Bobov Dol power station | b01fe781 | BG | 42.2858 | 23.0328 | 6.95 | medium | ERA5 wind assessment (ref 1991-2020) \| 50yr_gust=7.0m/s \| max_gust=7.0m/s \| 99p=6.6m/s \| prevailing=0deg \| tropical_idx=0.0 \| gev=ok \| grid_dist=4.8km \| source=copernicus_era5 | 20260512T184804_724e6d22 | 2026-05-12 21:55:49.608571+03:00 | 9.5 | pass |
| 7-8 | Despotovac power station | 5d53da59 | RS | 44.0500 | 21.2600 | 7.54 | medium | ERA5 wind assessment (ref 1991-2020) \| 50yr_gust=7.5m/s \| max_gust=7.6m/s \| 99p=7.0m/s \| prevailing=315deg \| tropical_idx=0.0 \| gev=ok \| grid_dist=5.6km \| source=copernicus_era5 | 20260512T184804_724e6d22 | 2026-05-12 22:22:58.478669+03:00 | 7.5 | pass |
| 7-8 | Orhaneli power station | 80b922cb | TR | 39.9502 | 28.8702 | 8.12 | medium | ERA5 wind assessment (ref 1991-2020) \| 50yr_gust=8.1m/s \| max_gust=8.1m/s \| 99p=8.0m/s \| prevailing=0deg \| tropical_idx=0.0 \| gev=ok \| grid_dist=11.6km \| source=copernicus_era5 | 20260512T184804_724e6d22 | 2026-05-12 22:27:03.270245+03:00 | 7.5 | pass |
| 5-6 | Dinar power station | 59f96677 | TR | 38.0640 | 30.1670 | 9.10 | medium | ERA5 wind assessment (ref 1991-2020) \| 50yr_gust=9.1m/s \| max_gust=9.0m/s \| 99p=8.3m/s \| prevailing=22deg \| tropical_idx=0.0 \| gev=ok \| grid_dist=10.2km \| source=copernicus_era5 | 20260512T184804_724e6d22 | 2026-05-12 22:25:30.653568+03:00 | 5.5 | pass |
| 5-6 | Kladno power station | f1d2bca1 | CZ | 50.1535 | 14.1286 | 10.07 | medium | ERA5 wind assessment (ref 1991-2020) \| 50yr_gust=10.1m/s \| max_gust=10.4m/s \| 99p=8.9m/s \| prevailing=248deg \| tropical_idx=0.0 \| gev=ok \| grid_dist=13.8km \| source=copernicus_era5 | 20260512T184804_724e6d22 | 2026-05-12 22:08:44.445456+03:00 | 5.5 | pass |
| 3-4 | Skawina power station | f5be4e73 | PL | 49.9774 | 19.8051 | 10.55 | medium | ERA5 wind assessment (ref 1991-2020) \| 50yr_gust=10.5m/s \| max_gust=10.7m/s \| 99p=8.7m/s \| prevailing=248deg \| tropical_idx=0.0 \| gev=ok \| grid_dist=4.7km \| source=copernicus_era5 | 20260512T184804_724e6d22 | 2026-05-12 22:20:49.995954+03:00 | 3.5 | pass |
| 3-4 | Plomin power station | ab151830 | HR | 45.1368 | 14.1627 | 11.14 | medium | ERA5 wind assessment (ref 1991-2020) \| 50yr_gust=11.1m/s \| max_gust=11.6m/s \| 99p=9.5m/s \| prevailing=45deg \| tropical_idx=0.0 \| gev=ok \| grid_dist=14.3km \| source=copernicus_era5 | 20260512T184804_724e6d22 | 2026-05-12 22:17:22.097460+03:00 | 3.5 | pass |
| 1-2 | Bandırma III power station | fecb62d9 | TR | 39.3850 | 27.5330 | 12.55 | medium | ERA5 wind assessment (ref 1991-2020) \| 50yr_gust=12.5m/s \| max_gust=12.8m/s \| 99p=11.7m/s \| prevailing=22deg \| tropical_idx=0.0 \| gev=ok \| grid_dist=13.1km \| source=copernicus_era5 | 20260512T184804_724e6d22 | 2026-05-12 22:24:38.736759+03:00 | 1.5 | pass |
| 1-2 | Tusimice power station | 287cbb48 | CZ | 50.3819 | 13.3400 | 12.81 | medium | ERA5 wind assessment (ref 1991-2020) \| 50yr_gust=12.8m/s \| max_gust=13.1m/s \| 99p=11.0m/s \| prevailing=248deg \| tropical_idx=0.0 \| gev=ok \| grid_dist=14.6km \| source=copernicus_era5 | 20260512T184804_724e6d22 | 2026-05-12 22:17:12.495323+03:00 | 1.5 | pass |
| 0-0 | (no sites in this band) | — | — | — | — | — | — | — | — | — | — | — |
