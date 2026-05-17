<!-- man_hours: 0.5 -->
# NH-12 Extreme Temperatures Scored Site Examples

Generated read-only from the local DB using `src/scripts/generate_scoring_examples.py`. The table shows real site rows and the scoring-engine output for the current working-tree bands.

## Scored examples — NH-12 (merged DB)

Two sites per band, picked by lowest + median extreme_temp_max_c within the band.

| band | site | site_id | country | lat | lon | extreme_temp_max_c | extreme_temp_min_c | nh12_quality | nh12_comment | run_id | fetched_at | score | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7-8 | Berane power station | e77a7e7f | ME | 42.8400 | 19.8600 | 19.56 | -7.92 | medium | ERA5 temperature (ref 1991-2020) \| max=19.6C \| min=-7.9C \| range=27.5C \| hot_days=0/yr \| cold_days=0/yr \| summer_mean=16.2C \| source=copernicus_era5 \| CMIP6_2050_ssp245=+1.7C \| CMIP6_2080_ssp585=+4.3C | 20260512T184804_724e6d22 | 2026-05-12 22:18:01.044352+03:00 | 7.5 | pass |
| 7-8 | Kütahya Domaniç power station | 2a3aad60 | TR | 39.8000 | 29.6100 | 24.81 | -3.96 | medium | ERA5 temperature (ref 1991-2020) \| max=24.8C \| min=-4.0C \| range=28.8C \| hot_days=0/yr \| cold_days=0/yr \| summer_mean=20.4C \| source=copernicus_era5 \| CMIP6_2050_ssp245=+1.2C \| CMIP6_2080_ssp585=+3.7C | 20260512T184804_724e6d22 | 2026-05-12 22:26:58.203550+03:00 | 7.5 | pass |
| 5-6 | Kangal power station | 0248611c | TR | 39.0775 | 37.2950 | 22.99 | -12.29 | medium | ERA5 temperature (ref 1991-2020) \| max=23.0C \| min=-12.3C \| range=35.3C \| hot_days=0/yr \| cold_days=0/yr \| summer_mean=18.5C \| source=copernicus_era5 \| CMIP6_2050_ssp245=+1.3C \| CMIP6_2080_ssp585=+4.1C | 20260512T184804_724e6d22 | 2026-05-12 22:26:30.853458+03:00 | 5.0 | pass |
| 5-6 | Orta Anadolu power station | f2e65fcf | TR | 40.6239 | 33.1128 | 23.90 | -6.44 | medium | ERA5 temperature (ref 1991-2020) \| max=23.9C \| min=-6.4C \| range=30.3C \| hot_days=0/yr \| cold_days=0/yr \| summer_mean=19.1C \| source=copernicus_era5 \| CMIP6_2050_ssp245=+1.2C \| CMIP6_2080_ssp585=+3.7C | 20260512T184804_724e6d22 | 2026-05-12 22:27:03.286392+03:00 | 6.5 | pass |
| 3-4 | Yıldırım Elazığ power station | 225656d9 | TR | 38.6620 | 39.7720 | 29.99 | -8.29 | medium | ERA5 temperature (ref 1991-2020) \| max=30.0C \| min=-8.3C \| range=38.3C \| hot_days=0/yr \| cold_days=0/yr \| summer_mean=25.8C \| source=copernicus_era5 \| CMIP6_2050_ssp245=+1.3C \| CMIP6_2080_ssp585=+4.1C | 20260512T184804_724e6d22 | 2026-05-12 22:27:57.767755+03:00 | 3.5 | pass |
| 3-4 | Prydniprovska power station | 02253fcc | UA | 48.4053 | 35.1117 | 26.18 | -9.63 | medium | ERA5 temperature (ref 1991-2020) \| max=26.2C \| min=-9.6C \| range=35.8C \| hot_days=0/yr \| cold_days=0/yr \| summer_mean=21.7C \| source=copernicus_era5 \| CMIP6_2050_ssp245=+1.4C \| CMIP6_2080_ssp585=+4.3C | 20260512T184804_724e6d22 | 2026-05-12 22:30:29.403703+03:00 | 4.5 | pass |
