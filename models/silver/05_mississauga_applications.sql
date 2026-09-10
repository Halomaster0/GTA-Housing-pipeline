-- Silver: Mississauga applications (site plan + rezoning union).
-- Grain: one row per APP_FILE_NO (ADR-0005: a file in both feeds is one
-- application with two facets). Survivor prefers a decided row (non-null
-- APPROVAL_DATE), then min OBJECTID; feeds_seen records the union.
-- Unit detail: TOTAL_RES_UNITS plus the RES_* / ICI_* breakdowns.
-- PII: APPLICANT/PLANNER are REVIEW-tier (kept in silver, out of gold).

CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE TABLE silver.mississauga_applications AS
WITH unified AS (
    SELECT 'site-plan' AS source_feed, * FROM read_parquet(
        '{BRONZE_ROOT}/mississauga-site-plan-applications/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
    UNION ALL
    SELECT 'rezoning' AS source_feed, * FROM read_parquet(
        '{BRONZE_ROOT}/mississauga-rezoning-applications/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY APP_FILE_NO
            ORDER BY (APPROVAL_DATE IS NOT NULL) DESC, OBJECTID
        ) AS rn,
        STRING_AGG(DISTINCT source_feed, '+') OVER (PARTITION BY APP_FILE_NO) AS feeds_seen
    FROM unified
)
SELECT
    APP_FILE_NO AS application_number,
    TYPE_DESC AS type_desc,
    SUBTYPE_CODE AS subtype_code,
    YEAR AS year,
    APPLICATION_NO AS application_no,
    CATEGORY_DESC AS category_desc,
    GENERAL_LOCATION AS general_location,
    DESCRIPTION AS description,
    SITE_ADDRESS AS site_address,
    CAST(to_timestamp(APPLICATION_DATE / 1000) AS DATE) AS date_applied,
    CASE WHEN APPROVAL_DATE IS NULL THEN NULL
         ELSE CAST(to_timestamp(APPROVAL_DATE / 1000) AS DATE) END AS date_decision,
    APPLICANT AS applicant,
    PLANNER AS planner,
    RES_DET AS res_detached,
    RES_SEMIS AS res_semi,
    RES_ROWS AS res_rows,
    RES_APTS AS res_apartments,
    RES_OTH_APTS AS res_other_apartments,
    TOTAL_RES_UNITS AS total_res_units,
    TOTAL_NON_RES_GFA AS total_non_res_gfa,
    WARD AS ward,
    CHAR_AREA AS character_area,
    SIMPLE_STATUS AS status_raw,
    feeds_seen,
    source_feed AS surviving_feed,
    OBJECTID AS source_row_id,
    '{INGEST_DATE}' AS ingest_date
FROM ranked
WHERE rn = 1;

CREATE OR REPLACE TABLE silver.mississauga_applications_audit AS
SELECT
    COUNT(*) AS bronze_rows,
    COUNT(*) - (SELECT COUNT(*) FROM silver.mississauga_applications) AS rows_collapsed,
    SUM(CASE WHEN feeds_seen LIKE '%+%' THEN 1 ELSE 0 END) AS files_in_both_feeds
FROM (
    SELECT APP_FILE_NO,
        STRING_AGG(DISTINCT source_feed, '+') AS feeds_seen
    FROM (
        SELECT 'site-plan' AS source_feed, APP_FILE_NO FROM read_parquet(
            '{BRONZE_ROOT}/mississauga-site-plan-applications/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
        UNION ALL
        SELECT 'rezoning' AS source_feed, APP_FILE_NO FROM read_parquet(
            '{BRONZE_ROOT}/mississauga-rezoning-applications/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
    )
    GROUP BY APP_FILE_NO
);
