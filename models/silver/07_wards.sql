-- Silver: wards (all vintages, all municipalities).
-- Grain: one row per ward-boundary version (municipality × ward code ×
-- effective range), per ADR-0007. Toronto carries real DATE_EFFECTIVE/EXPIRY
-- (is_current = expiry year 3000); Mississauga/Peel vintages are labelled
-- from their publication (prior Peel vintage is_current = FALSE).
-- PII: Peel Mayor/councillor/name columns are never selected (DROP-tier).
-- Ward codes are TEXT everywhere (Mississauga WARD is int in bronze).

CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE TABLE silver.wards AS
SELECT 'Toronto' AS municipality, CAST(AREA_SHORT_CODE AS VARCHAR) AS ward_code,
    AREA_NAME AS ward_name, 'city-wards-current' AS vintage,
    CAST(DATE_EFFECTIVE AS DATE) AS effective_start,
    CASE WHEN CAST(DATE_EXPIRY AS DATE) < DATE '2999-01-01' THEN CAST(DATE_EXPIRY AS DATE) END
        AS effective_end,
    CAST(DATE_EXPIRY AS DATE) >= DATE '2999-01-01' AS is_current,
    geometry AS geometry_geojson,
    '{INGEST_DATE}' AS ingest_date
FROM read_parquet(
    '{BRONZE_ROOT}/toronto-wards/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
UNION ALL
SELECT 'Mississauga', CAST(WARD AS VARCHAR), 'Ward ' || CAST(WARD AS VARCHAR),
    'mississauga-wards-current', NULL, NULL, TRUE, NULL, '{INGEST_DATE}'
FROM read_parquet(
    '{BRONZE_ROOT}/mississauga-wards/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
UNION ALL
SELECT Municipali, CAST(WardNumber AS VARCHAR), WardName, 'peel-2022-2026',
    DATE '2022-01-01', NULL, TRUE, NULL, '{INGEST_DATE}'
FROM read_parquet(
    '{BRONZE_ROOT}/peel-wards-current/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
UNION ALL
SELECT MUNIC, CAST(WARDNUM AS VARCHAR), 'Ward ' || CAST(WARDNUM AS VARCHAR),
    'peel-2018-2022', DATE '2018-01-01', DATE '2022-01-01', FALSE, NULL, '{INGEST_DATE}'
FROM read_parquet(
    '{BRONZE_ROOT}/peel-wards-prior/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE);
