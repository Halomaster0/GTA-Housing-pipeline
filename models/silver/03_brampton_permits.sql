-- Silver: Brampton permits (production MapServer).
-- Grain: one row per (permitnumber, foldersn) — a folder number spans shell +
-- finish sub-permits (evidence §11), keeping min OBJECTID; 4 re-processed
-- doubles differ only in OBJECTID/PROCESSDATE (evidence §12).
-- DWELLINGS and GFA are TEXT in bronze (try_cast, NULL on failure, counted).
-- ISSUEDATE is nullable (unissued permits) — date_issued stays NULL, never
-- coerced. PII: BUILDER/CONTRACTOR are REVIEW-tier (kept in silver, out of gold).

CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE TABLE silver.brampton_permits AS
WITH ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY PERMITNUMBER, FOLDERRSN ORDER BY OBJECTID) AS rn
    FROM read_parquet(
        '{BRONZE_ROOT}/brampton-building-permits/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
)
SELECT
    PERMITNUMBER AS permit_number,
    CAST(FOLDERRSN AS BIGINT) AS foldersn,
    ADDRESS AS address,
    SUBDESC AS subdesc,
    WORKDESC AS workdesc,
    CAST(to_timestamp(INDATE / 1000) AS DATE) AS date_applied,
    CASE WHEN ISSUEDATE IS NULL THEN NULL
         ELSE CAST(to_timestamp(ISSUEDATE / 1000) AS DATE) END AS date_issued,
    STATUSDESC AS status_raw,
    CASE WHEN PROCESSDATE IS NULL THEN NULL
         ELSE CAST(to_timestamp(PROCESSDATE / 1000) AS DATE) END AS date_processed,
    BUILDER AS builder,
    CONTRACTOR AS contractor,
    CASE WHEN EXPIRYDATE IS NULL THEN NULL
         ELSE CAST(to_timestamp(EXPIRYDATE / 1000) AS DATE) END AS date_expiry,
    TRY_CAST(GFA AS DECIMAL(12, 2)) AS floor_area_raw,
    SECOND_UNIT AS second_unit,
    BEDROOMS AS bedrooms,
    STOREYS AS storeys,
    TRY_CAST(DWELLINGS AS INTEGER) AS dwellings,
    GIS_ID AS gis_id,
    OBJECTID AS source_row_id,
    '{INGEST_DATE}' AS ingest_date
FROM ranked
WHERE rn = 1;

CREATE OR REPLACE TABLE silver.brampton_permits_audit AS
SELECT
    COUNT(*) AS bronze_rows,
    COUNT(*) - (SELECT COUNT(*) FROM silver.brampton_permits) AS rows_dropped_as_dupes,
    SUM(CASE WHEN dwellings IS NULL THEN 1 ELSE 0 END) AS rows_with_null_dwellings,
    SUM(CASE WHEN TRY_CAST(DWELLINGS AS INTEGER) IS NULL AND DWELLINGS IS NOT NULL
        THEN 1 ELSE 0 END) AS dwellings_cast_failures
FROM read_parquet(
    '{BRONZE_ROOT}/brampton-building-permits/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE);
