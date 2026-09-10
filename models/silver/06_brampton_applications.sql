-- Silver: Brampton applications (five planning layers union).
-- Grain: one row per (file_number, poly_id) — polygon splits are geographic
-- truth, not duplicates (evidence §10); gold collapses to one row per file.
-- No unit fields on any planning layer; decision dates exist only as status
-- text (no decision-date column). No FOLDERRSN here (ADR-0006).

CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE TABLE silver.brampton_applications AS
SELECT 'minor-variance' AS planning_layer, FILE_NUMBER AS file_number,
    REGIONAL_NUMBER AS regional_number, LOCATION AS location,
    CAST(to_timestamp(DATE_RECEIVED / 1000) AS DATE) AS date_received,
    APPLICATION_TYPE AS application_type, APPLICATION_TITLE AS application_title,
    DESCRIPTION AS description, STATUS AS status_raw,
    CITY_PLANNER AS city_planner, PROPOSAL_DESCRIPTION AS proposal_description,
    AGENT_COMPANY AS agent_company, APPLICANT_COMPANY AS applicant_company,
    WARD AS ward, POLY_ID AS poly_id, Shape__Area AS shape_area,
    '{INGEST_DATE}' AS ingest_date
FROM read_parquet(
    '{BRONZE_ROOT}/brampton-minor-variance/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
UNION ALL
SELECT 'opa-zba-subdivision', FILE_NUMBER, REGIONAL_NUMBER, LOCATION,
    CAST(to_timestamp(DATE_RECEIVED / 1000) AS DATE),
    APPLICATION_TYPE, APPLICATION_TITLE, DESCRIPTION, STATUS,
    CITY_PLANNER, PROPOSAL_DESCRIPTION, AGENT_COMPANY, APPLICANT_COMPANY,
    WARD, POLY_ID, Shape__Area, '{INGEST_DATE}'
FROM read_parquet(
    '{BRONZE_ROOT}/brampton-opa-zba-subdivision/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
UNION ALL
SELECT 'pre-consultation', FILE_NUMBER, REGIONAL_NUMBER, LOCATION,
    CAST(to_timestamp(DATE_RECEIVED / 1000) AS DATE),
    APPLICATION_TYPE, APPLICATION_TITLE, DESCRIPTION, STATUS,
    CITY_PLANNER, PROPOSAL_DESCRIPTION, AGENT_COMPANY, APPLICANT_COMPANY,
    WARD, POLY_ID, Shape__Area, '{INGEST_DATE}'
FROM read_parquet(
    '{BRONZE_ROOT}/brampton-pre-consultation/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
UNION ALL
SELECT 'consent-sever', FILE_NUMBER, REGIONAL_NUMBER, LOCATION,
    CAST(to_timestamp(DATE_RECEIVED / 1000) AS DATE),
    APPLICATION_TYPE, APPLICATION_TITLE, DESCRIPTION, STATUS,
    CITY_PLANNER, PROPOSAL_DESCRIPTION, AGENT_COMPANY, APPLICANT_COMPANY,
    WARD, POLY_ID, Shape__Area, '{INGEST_DATE}'
FROM read_parquet(
    '{BRONZE_ROOT}/brampton-consent-sever/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE)
UNION ALL
SELECT 'draft-plan-condo', FILE_NUMBER, REGIONAL_NUMBER, LOCATION,
    CAST(to_timestamp(DATE_RECEIVED / 1000) AS DATE),
    APPLICATION_TYPE, APPLICATION_TITLE, DESCRIPTION, STATUS,
    CITY_PLANNER, PROPOSAL_DESCRIPTION, AGENT_COMPANY, APPLICANT_COMPANY,
    WARD, POLY_ID, Shape__Area, '{INGEST_DATE}'
FROM read_parquet(
    '{BRONZE_ROOT}/brampton-draft-plan-condo/ingest_date={INGEST_DATE}/part-*.parquet', union_by_name = TRUE);

CREATE OR REPLACE TABLE silver.brampton_applications_audit AS
SELECT planning_layer, COUNT(*) AS rows_per_layer
FROM silver.brampton_applications
GROUP BY planning_layer;
