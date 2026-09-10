-- Silver: Toronto applications.
-- Grain: one row per APPLICATION# (accumulating snapshot grain per ADR-0005).
-- Bronze grain is per-address (100 rows / 47 files, evidence §2): survivor is
-- min _id, plus address_count and the distinct address list so the collapse
-- is auditable. No unit field, one lifecycle date (DATE_SUBMITTED).
-- PII: CONTACT_NAME/PHONE/EMAIL are never selected (DROP-tier, ADR-0007).

CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE TABLE silver.toronto_applications AS
WITH ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY "APPLICATION#" ORDER BY _id) AS rn,
        COUNT(*) OVER (PARTITION BY "APPLICATION#") AS n_addr,
        STRING_AGG(
            DISTINCT TRIM(STREET_NUM || ' ' || STREET_NAME || ' ' || STREET_TYPE),
            ' | '
        ) OVER (PARTITION BY "APPLICATION#") AS address_list
    FROM read_parquet(
        '{BRONZE_ROOT}/toronto-development-applications/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
)
SELECT
    "APPLICATION#" AS application_number,
    APPLICATION_TYPE AS application_type,
    CAST(DATE_SUBMITTED AS DATE) AS date_submitted,
    STATUS AS status_raw,
    X AS x,
    Y AS y,
    DESCRIPTION AS description,
    "REFERENCE_FILE#" AS reference_file_number,
    FOLDERRSN AS foldersn,
    WARD_NUMBER AS ward_number,
    WARD_NAME AS ward_name,
    COMMUNITY_MEETING_DATE AS community_meeting_date,
    APPLICATION_URL AS application_url,
    "PARENT_FOLDER_NUMBER" AS parent_folder_number,
    POSTAL AS postal,
    n_addr AS address_count,
    address_list,
    _id AS source_row_id,
    '{INGEST_DATE}' AS ingest_date
FROM ranked
WHERE rn = 1;

CREATE OR REPLACE TABLE silver.toronto_applications_audit AS
SELECT
    COUNT(*) AS bronze_rows,
    COUNT(*) - (SELECT COUNT(*) FROM silver.toronto_applications) AS address_rows_collapsed,
    (SELECT COUNT(*) FROM silver.toronto_applications) AS application_files
FROM read_parquet(
    '{BRONZE_ROOT}/toronto-development-applications/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE);
