-- Silver: Mississauga permits.
-- Grain: one row per BP_NO — the proven double publication (HOUSDEMO 18-3651,
-- evidence §10) is removed keeping min OBJECTID. ArcGIS epoch-millis dates
-- become UTC timestamps cast to DATE for milestones (bare-date handling per
-- schema design §7 does not apply: these are true timestamps).
-- PII: no ruled-drop columns on this feed.

CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE TABLE silver.mississauga_permits AS
WITH ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY BP_NO ORDER BY OBJECTID) AS rn
    FROM read_parquet(
        '{BRONZE_ROOT}/mississauga-building-permits/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
)
SELECT
    BP_NO AS permit_number,
    STATUS AS status_raw,
    ADDRESS AS address,
    UNIT_NO AS unit_no,
    DESCRIPTION AS description,
    SCOPE AS scope,
    FILE_TYPE AS file_type,
    BLDG_TYPE AS building_type,
    APP_DETAIL AS app_detail,
    APPL_AREA AS appl_area,
    STOREYS AS storeys,
    EST_CON_VALUE AS construction_value_cad,
    RES_UNITS AS res_units,
    DEMO AS demo,
    POSTAL_CODE AS postal_code,
    BLDG_NO AS building_no,
    WARD AS ward,
    ZAREA AS zarea,
    LATITUDE AS latitude,
    LONGITUDE AS longitude,
    CAST(to_timestamp(APPLICATION_DATE / 1000) AS DATE) AS date_applied,
    CAST(to_timestamp(ISSUE_DATE / 1000) AS DATE) AS date_issued,
    CAST(to_timestamp(COMPLETE_DATE / 1000) AS DATE) AS date_closed,
    OBJECTID AS source_row_id,
    '{INGEST_DATE}' AS ingest_date
FROM ranked
WHERE rn = 1;

CREATE OR REPLACE TABLE silver.mississauga_permits_audit AS
SELECT
    COUNT(*) AS bronze_rows,
    COUNT(*) - (SELECT COUNT(*) FROM silver.mississauga_permits) AS rows_dropped_as_dupes
FROM read_parquet(
    '{BRONZE_ROOT}/mississauga-building-permits/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE);
