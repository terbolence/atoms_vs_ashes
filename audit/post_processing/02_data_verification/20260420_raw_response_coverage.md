Raw-response coverage from manifest=audit/post_processing/raw_response_run_manifest.yml
Expected sites:  363
Threshold:       100%

connector                logger_fn              run_id                              logged  disk  missing   ratio  status
-------------------------------------------------------------------------------------------------------------------------
bdticm_bedrock           log_raster_extraction  audit_20260419T221957                  363   363        0 100.00%  OK
copernicus_dem           log_raster_extraction  audit_20260419T221957                  363   363        0 100.00%  OK
copernicus_ems           log_raw_response       audit_postlogging_20260421             363   365        0 100.00%  OK
copernicus_era5          log_raster_extraction  audit_postlogging_20260421             363   363        0 100.00%  OK
corine                   log_raw_response       audit_20260419T221957                  363   363        0 100.00%  OK
egdi_geology             log_raw_response       audit_rerun_20260419                   363   363        0 100.00%  OK
entso_e                  log_raw_response       audit_postlogging_20260421             363   363        0 100.00%  OK
eurostat_gisco           log_raw_response       audit_postlogging_20260421             363   363        0 100.00%  OK
eurostat_projections     log_raw_response       audit_postlogging_20260421             363   363        0 100.00%  OK
natura2000               log_raw_response       audit_20260419T221957                  363   363        0 100.00%  OK
noaa_ncei                log_raw_response       audit_20260419T221957                  363   363        0 100.00%  OK
onegeology               log_raw_response       audit_postlogging_20260421             363   363        0 100.00%  OK
osm                      log_raw_response       osm_audit_20260420                     363   363        0 100.00%  OK
population               log_raw_response       audit_postlogging_20260421             363   363        0 100.00%  OK
seismic_hazard           log_raw_response       audit_postlogging_20260421             363   363        0 100.00%  OK
soilgrids                log_raster_extraction  audit_20260419T221957                  363   363        0 100.00%  OK

Overall: PASS
