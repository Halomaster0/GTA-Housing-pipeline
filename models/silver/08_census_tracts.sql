-- Silver: census tracts (Peel 2021 layer).
-- Grain: one row per CTUID. Per-capita / per-dwelling denominators for the
-- municipal comparison pages, independent of StatCan WDS (evidence §7).

CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE TABLE silver.census_tracts AS
SELECT CTUID AS tract_id, CTNAME AS tract_name, CSDNAME AS csd_name,
    LANDAREA AS land_area, Pop16 AS pop_2016, Pop21 AS pop_2021,
    PopChg16_21 AS pop_change_16_21, Dwell21 AS dwellings_2021,
    Dwell_UR21 AS dwellings_urban_2021, AreaKM2_21 AS area_km2,
    PopDen21 AS pop_density_2021, DwellUR_Den21 AS dwelling_density_2021,
    '{INGEST_DATE}' AS ingest_date
FROM read_parquet(
    '{BRONZE_ROOT}/peel-census2021-ct/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE);
