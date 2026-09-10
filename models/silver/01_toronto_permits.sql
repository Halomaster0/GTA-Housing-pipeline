-- Silver: Toronto permits (unified active + cleared).
-- Grain: one row per (permit_num, revision_num, permit_type) — the proven
-- bronze row identity minus CKAN _id (evidence §§10, 12). Survivor rule:
-- cleared resource wins on cross-resource collision (ADR-0005), then min _id
-- (double-entered rows differ only in builder name — the dropped names are
-- counted in the audit table for the data-quality report).
-- PII: no ruled-drop columns on this feed (BUILDER_NAME is REVIEW-tier:
-- kept in silver, dropped from gold — see conformance matrix).
-- Units: DWELLING_UNITS_CREATED/LOST are TEXT in bronze; try_cast keeps
-- unparseable values NULL instead of failing the build (failures counted).

CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE TABLE silver.toronto_permits AS
WITH unified AS (
    SELECT 'active' AS source_resource, * FROM read_parquet(
        '{BRONZE_ROOT}/toronto-building-permits-active/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
    UNION ALL
    SELECT 'cleared' AS source_resource, * FROM read_parquet(
        '{BRONZE_ROOT}/toronto-building-permits-cleared/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY PERMIT_NUM, REVISION_NUM, PERMIT_TYPE
            ORDER BY (source_resource = 'cleared') DESC, _id
        ) AS rn,
        COUNT(*) OVER (PARTITION BY PERMIT_NUM, REVISION_NUM, PERMIT_TYPE) AS n_dup
    FROM unified
)
SELECT
    PERMIT_NUM AS permit_number,
    REVISION_NUM AS revision_num,
    PERMIT_TYPE AS permit_type,
    STRUCTURE_TYPE AS structure_type,
    WORK AS work,
    STREET_NUM AS street_num,
    STREET_NAME AS street_name,
    STREET_TYPE AS street_type,
    STREET_DIRECTION AS street_direction,
    POSTAL AS postal,
    GEO_ID AS geo_id,
    WARD_GRID AS ward_grid,
    CAST(APPLICATION_DATE AS DATE) AS date_applied,
    CAST(ISSUED_DATE AS DATE) AS date_issued,
    CAST(COMPLETED_DATE AS DATE) AS date_closed,
    STATUS AS status_raw,
    DESCRIPTION AS description,
    CURRENT_USE AS current_use,
    PROPOSED_USE AS proposed_use,
    TRY_CAST(DWELLING_UNITS_CREATED AS INTEGER) AS dwelling_units_created,
    TRY_CAST(DWELLING_UNITS_LOST AS INTEGER) AS dwelling_units_lost,
    TRY_CAST(EST_CONST_COST AS DECIMAL(14, 2)) AS construction_value_cad,
    ASSEMBLY AS area_assembly,
    INSTITUTIONAL AS area_institutional,
    RESIDENTIAL AS area_residential,
    BUSINESS_AND_PERSONAL_SERVICES AS area_business_personal,
    MERCANTILE AS area_mercantile,
    INDUSTRIAL AS area_industrial,
    INTERIOR_ALTERATIONS AS area_interior_alterations,
    DEMOLITION AS area_demolition,
    BUILDER_NAME AS builder_name,
    source_resource,
    _id AS source_row_id,
    '{INGEST_DATE}' AS ingest_date
FROM ranked
WHERE rn = 1;

-- Audit: what dedup removed, for the data-quality report.
CREATE OR REPLACE TABLE silver.toronto_permits_audit AS
SELECT
    COUNT(*) AS bronze_rows,
    COUNT(*) - (SELECT COUNT(*) FROM silver.toronto_permits) AS rows_dropped_as_dupes,
    SUM(CASE WHEN n_dup > 1 THEN 1 ELSE 0 END) AS rows_involved_in_dupes
FROM (
    SELECT PERMIT_NUM, REVISION_NUM, PERMIT_TYPE,
        COUNT(*) OVER (PARTITION BY PERMIT_NUM, REVISION_NUM, PERMIT_TYPE) AS n_dup
    FROM (
        SELECT PERMIT_NUM, REVISION_NUM, PERMIT_TYPE FROM read_parquet(
            '{BRONZE_ROOT}/toronto-building-permits-active/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
        UNION ALL
        SELECT PERMIT_NUM, REVISION_NUM, PERMIT_TYPE FROM read_parquet(
            '{BRONZE_ROOT}/toronto-building-permits-cleared/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
    )
);
