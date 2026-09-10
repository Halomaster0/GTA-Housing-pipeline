-- Gold: fct_applications. Grain: ONE ROW PER DEVELOPMENT APPLICATION
-- (administrative file number — ADR-0005, explicitly not the project).
--   Toronto: silver already one row per file (address collapse).
--   Mississauga: silver already one row per file (cross-feed union).
--   Brampton: collapse multi-polygon rows to one row per file (min poly_id
--     survivor, polygon_count kept) — polygon splits are geography, not cases.
-- Status comes from silver.application_status_history (current row); the fact
-- carries no history. Decision dates exist only for Mississauga
-- (APPROVAL_DATE); Toronto/Brampton carry NULL with the reason in the matrix.
-- Units: Mississauga TOTAL_RES_UNITS only; basis 'unknown' (ADR-0003).

CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE TABLE gold.fct_applications AS
WITH brampton_collapsed AS (
    SELECT file_number, poly_id, planning_layer
    FROM (
        SELECT file_number, poly_id, planning_layer,
            ROW_NUMBER() OVER (
                PARTITION BY file_number ORDER BY poly_id, planning_layer
            ) AS rn
        FROM silver.brampton_applications
    )
    WHERE rn = 1
),
unified AS (
    SELECT 'TOR' AS municipality_code,
        application_number, application_type AS raw_type,
        CAST(NULL AS VARCHAR) AS raw_subtype, status_raw,
        date_submitted, CAST(NULL AS DATE) AS date_decision,
        CAST(NULL AS INTEGER) AS units_proposed,
        ward_number AS ward_ref, description
    FROM silver.toronto_applications
    UNION ALL
    SELECT 'MISS', application_number, type_desc, category_desc, status_raw,
        date_applied, date_decision, total_res_units,
        CAST(ward AS VARCHAR), description
    FROM silver.mississauga_applications
    UNION ALL
    SELECT 'BRAM', b.file_number, b.application_type, b.application_type,
        b.status_raw, b.date_received, NULL, NULL,
        REGEXP_EXTRACT(b.ward, '[0-9]+'), b.proposal_description
    FROM silver.brampton_applications b
    JOIN brampton_collapsed c
        ON c.file_number = b.file_number
        AND c.poly_id = b.poly_id
        AND c.planning_layer = b.planning_layer
),
typed AS (
    SELECT u.*,
        CASE
            WHEN municipality_code = 'TOR' THEN 'UNKNOWN'
            WHEN municipality_code = 'MISS' AND (
                raw_subtype ILIKE '%apartment%' OR raw_subtype ILIKE '%infill%'
                OR raw_subtype ILIKE '%multi-unit%' OR raw_subtype ILIKE '%townhouse%'
                OR raw_subtype ILIKE '%condominium%')
                THEN 'RESIDENTIAL'
            WHEN municipality_code = 'MISS' AND raw_subtype ILIKE '%mixed-use%'
                THEN 'MIXED_USE'
            WHEN municipality_code = 'MISS' AND (
                raw_subtype ILIKE '%community%' OR raw_subtype ILIKE '%cultural%'
                OR raw_subtype ILIKE '%institutional%')
                THEN 'INSTITUTIONAL'
            WHEN municipality_code = 'MISS' AND raw_subtype IS NOT NULL
                THEN 'OTHER'
            WHEN municipality_code = 'MISS' THEN 'UNKNOWN'
            WHEN municipality_code = 'BRAM' AND raw_type = 'Draft Plan of Condo'
                THEN 'RESIDENTIAL'
            WHEN municipality_code = 'BRAM' THEN 'UNKNOWN'
        END AS use_type_code,
        CASE
            WHEN municipality_code = 'TOR' AND status_raw = 'Application Received'
                THEN 'SUBMITTED'
            WHEN municipality_code = 'TOR' AND status_raw IN (
                'Circulated', 'Under Review ', 'Under Review', 'Amend Drft Plan App')
                THEN 'UNDER_REVIEW'
            WHEN municipality_code = 'TOR' AND status_raw IN (
                'Approved', 'Council Approved', 'Draft Plan Approved',
                'Final Approval Completed', 'NOAC Issued', 'OMB Approved',
                'OMB Partially Approved')
                THEN 'APPROVED'
            WHEN municipality_code = 'TOR' AND status_raw IN ('Refused', 'OMB Refused')
                THEN 'REFUSED'
            WHEN municipality_code = 'TOR' AND status_raw IN ('Appeal Received', 'OMB Appeal')
                THEN 'APPEALED'
            WHEN municipality_code = 'TOR' THEN 'CLOSED'
            WHEN municipality_code = 'MISS' AND status_raw = 'Active'
                THEN 'UNDER_REVIEW'
            WHEN municipality_code = 'MISS' THEN 'APPROVED'
            WHEN municipality_code = 'BRAM' AND status_raw IN (
                'Submitted', 'Received', 'Incomplete', 'Invalid',
                'Initial Submission Rejected', 'Verification of Documents')
                THEN 'SUBMITTED'
            WHEN municipality_code = 'BRAM' AND status_raw IN (
                'In Review', 'In Review-Pre Public Meeting',
                'In Review-Public Mtg Complete', 'Staff Review Complete',
                'Meeting Scheduled', 'Hearing Scheduled', 'Staff Report Sent',
                'Comments Released', 'Stage 2 Review', 'Finalize', 'Review',
                'Deemed Complete', 'Application Complete')
                THEN 'UNDER_REVIEW'
            WHEN municipality_code = 'BRAM' AND status_raw IN (
                'Approved', 'COA - Approved (in part) with conditions',
                'COA - Approved with conditions', 'Final and Binding',
                'Draft Approved', 'Closed Approved', 'Registered', 'Registration',
                'Plan of Condo Registered', 'MZO Approved',
                'M-Plan/Condition Clearance', 'OMB - Approved',
                'OMB - Approved with conditions', 'OMB � Approved')
                THEN 'APPROVED'
            WHEN municipality_code = 'BRAM' AND status_raw IN (
                'Denied', 'Denied Closed', 'Refused', 'OMB - Refused',
                'COA - Null & Void')
                THEN 'REFUSED'
            WHEN municipality_code = 'BRAM' AND status_raw IN (
                'In Appeal', 'Under Appeal')
                THEN 'APPEALED'
            WHEN municipality_code = 'BRAM' THEN 'CLOSED'
        END AS status_code
    FROM unified u
)
SELECT
    ROW_NUMBER() OVER (ORDER BY t.municipality_code, t.application_number) AS application_sk,
    m.municipality_sk,
    t.application_number,
    g.geography_sk,
    u.use_type_sk,
    'unknown' AS use_type_classification_method,
    s.status_sk,
    t.status_raw,
    d1.date_sk AS date_submitted_sk,
    d2.date_sk AS date_decision_sk,
    t.units_proposed AS unit_count_proposed,
    'unknown' AS unit_count_basis,
    '{INGEST_DATE}' AS ingest_batch_id,
    CURRENT_TIMESTAMP AS row_loaded_at
FROM typed t
JOIN gold.dim_municipality m ON m.municipality_code = t.municipality_code
JOIN gold.dim_use_type u ON u.use_type_code = t.use_type_code
JOIN gold.dim_status s
    ON s.status_code = t.status_code AND s.applies_to = 'application'
LEFT JOIN gold.dim_date d1 ON d1.calendar_date = t.date_submitted
LEFT JOIN gold.dim_date d2 ON d2.calendar_date = t.date_decision
LEFT JOIN gold.dim_geography g
    ON ((g.municipality = 'Toronto' AND g.vintage = 'city-wards-current'
            AND t.municipality_code = 'TOR')
        OR (g.municipality = 'Mississauga' AND g.vintage = 'mississauga-wards-current'
            AND t.municipality_code = 'MISS')
        OR (g.municipality = 'Brampton' AND g.vintage = 'peel-2022-2026'
            AND t.municipality_code = 'BRAM'))
    AND g.ward_code = t.ward_ref;
