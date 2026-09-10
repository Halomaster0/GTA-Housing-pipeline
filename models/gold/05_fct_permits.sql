-- Gold: fct_permits. Grain: ONE ROW PER BUILDING PERMIT.
-- Collapse rules (proven shapes, evidence §§10–12):
--   Toronto: per PERMIT_NUM — prefer the definitive row over Conditional
--     Permit precursors, then max REVISION_NUM, then min source row.
--   Mississauga: per BP_NO, min OBJECTID (double publication).
--   Brampton: per PERMITNUMBER — prefer the row carrying DWELLINGS (shell
--     rows hold the count, finish rows are null) then min OBJECTID, so folder
--     unit sums do not double-count shell-vs-finish pairs.
-- Units: Toronto created−lost only when BOTH are reported (strict NULL
-- otherwise); every unit value carries basis 'unknown' (ADR-0003).
-- related_application_number is NULL everywhere: no proven key (ADR-0006).
-- Geography: Mississauga resolves by ward; Toronto (grid ref) and Brampton
-- (no ward) permits carry NULL geography_sk — measured, not hidden.

CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE TABLE gold.fct_permits AS
WITH toronto_ranked AS (
    SELECT p.*,
        ROW_NUMBER() OVER (
            PARTITION BY permit_number
            ORDER BY (permit_type = 'Conditional Permit'), revision_num DESC, source_row_id
        ) AS rn
    FROM silver.toronto_permits p
),
mississauga_ranked AS (
    SELECT p.*,
        ROW_NUMBER() OVER (PARTITION BY permit_number ORDER BY source_row_id) AS rn
    FROM silver.mississauga_permits p
),
brampton_ranked AS (
    SELECT p.*,
        ROW_NUMBER() OVER (
            PARTITION BY permit_number
            ORDER BY (dwellings IS NULL), source_row_id
        ) AS rn
    FROM silver.brampton_permits p
),
collapsed AS (
    SELECT 'TOR' AS municipality_code, permit_number,
        permit_type AS raw_type, NULL AS raw_subtype, work AS raw_work,
        status_raw, date_applied, date_issued, date_closed,
        dwelling_units_created, dwelling_units_lost, NULL::INTEGER AS units_single,
        construction_value_cad, NULL::DOUBLE AS appl_area,
        area_assembly, area_institutional, area_residential,
        area_business_personal, area_mercantile, area_industrial,
        area_interior_alterations, area_demolition, NULL::DECIMAL(12, 2) AS floor_area_single,
        CAST(NULL AS VARCHAR) AS ward_ref, description
    FROM toronto_ranked WHERE rn = 1
    UNION ALL
    SELECT 'MISS', permit_number, file_type, building_type, scope,
        status_raw, date_applied, date_issued, date_closed,
        NULL, NULL, res_units, construction_value_cad, appl_area,
        NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
        CAST(ward AS VARCHAR), description
    FROM mississauga_ranked WHERE rn = 1
    UNION ALL
    SELECT 'BRAM', permit_number, subdesc, workdesc, workdesc,
        status_raw, date_applied, date_issued, NULL,
        NULL, NULL, dwellings, NULL, NULL,
        NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, floor_area_raw,
        NULL, workdesc
    FROM brampton_ranked WHERE rn = 1
),
typed AS (
    SELECT c.*,
        CASE
            WHEN municipality_code = 'TOR' AND raw_type IN (
                'New Houses', 'Residential Building Permit',
                'Small Residential Projects', 'Rental Renovation Licence')
                THEN 'RESIDENTIAL'
            WHEN municipality_code = 'TOR' AND raw_type = 'Multiple Use Permit'
                THEN 'MIXED_USE'
            WHEN municipality_code = 'TOR' AND raw_type = 'Portable Classrooms'
                THEN 'INSTITUTIONAL'
            WHEN municipality_code = 'TOR' THEN 'OTHER'
            WHEN municipality_code = 'MISS' AND (
                raw_subtype IN (
                    'APARTMENT (> 6 UNITS)', 'CONDOMINIUM ROW DWELLING',
                    'DETACHED DWELLING', 'DUPLEX, 3, 4, 5 0R 6PLEX',
                    'RESIDENTIAL - OTHER', 'ROW DWELLING',
                    'SEMI-DETACHED DWELLING', 'STREET ROW DWELLING')
                OR raw_type = 'RESIDENTIAL')
                THEN 'RESIDENTIAL'
            WHEN municipality_code = 'MISS' THEN 'OTHER'
            WHEN municipality_code = 'BRAM' AND (
                raw_type LIKE 'C:%' OR raw_type LIKE '9.5%' OR raw_type LIKE '9.6%'
                OR raw_type LIKE '9.8%' OR raw_type IN (
                    'Duplex', 'Triplex', 'QuatroPlex', 'Townhouse',
                    'Townhouse - Condominium', 'Semi Detached Dwelling',
                    'Semi Detached - Condominium', 'Single Family Detached',
                    'Single Dwelling - Condominium', 'Single BLDG Site',
                    'Two Unit Dwelling', 'Two Unit Dwelling - 9.8 Retrofit',
                    'Three Unit Dwelling', 'Stacked Townhouses', 'Garden Suite')
                OR raw_subtype LIKE '%Second Unit%')
                THEN 'RESIDENTIAL'
            WHEN municipality_code = 'BRAM'
                AND raw_type IN ('Mixed Use', 'Live/Work')
                THEN 'MIXED_USE'
            WHEN municipality_code = 'BRAM' AND (
                raw_type LIKE 'A2:%' OR raw_type LIKE 'B%:%')
                THEN 'INSTITUTIONAL'
            WHEN municipality_code = 'BRAM' AND (
                raw_type LIKE 'Site Service%' OR raw_type IN (
                    'Communication Tower', 'Crane Runway'))
                THEN 'INFRASTRUCTURE'
            WHEN municipality_code = 'BRAM' THEN 'OTHER'
        END AS use_type_code,
        CASE
            WHEN municipality_code = 'TOR' AND status_raw = 'Application Received'
                THEN 'APPLIED'
            WHEN municipality_code = 'TOR' AND status_raw IN (
                'Application Acceptable', 'Application On Hold',
                'Examiner''s Notice Sent', 'Response Received', 'Under Review ')
                THEN 'UNDER_REVIEW'
            WHEN municipality_code = 'TOR' AND status_raw IN (
                'Approved', 'Issuance Pending', 'Ready for Issuance',
                'Permit Issued', 'Inspection', 'Open', 'Revision Issued')
                THEN 'ISSUED'
            WHEN municipality_code = 'TOR' AND status_raw IN (
                'Closed', 'Closed - Dormant', 'Closed Permit/Incomplete Work')
                THEN 'CLOSED'
            WHEN municipality_code = 'TOR' THEN 'CANCELLED'
            WHEN municipality_code = 'MISS' AND status_raw = 'ISSUED PERMIT'
                THEN 'ISSUED'
            WHEN municipality_code = 'MISS' AND status_raw LIKE 'COMPLETED%'
                THEN 'CLOSED'
            WHEN municipality_code = 'MISS' THEN 'CANCELLED'
            WHEN municipality_code = 'BRAM' AND status_raw = 'Applied'
                THEN 'APPLIED'
            WHEN municipality_code = 'BRAM' AND status_raw IN ('Zoning Certified')
                THEN 'UNDER_REVIEW'
            WHEN municipality_code = 'BRAM' AND status_raw IN (
                'Ready to Issue', 'Issued', 'Occupancy Granted')
                THEN 'ISSUED'
            WHEN municipality_code = 'BRAM' AND status_raw IN ('Closed', 'Registered')
                THEN 'CLOSED'
            WHEN municipality_code = 'BRAM' THEN 'CANCELLED'
        END AS status_code
    FROM collapsed c
)
SELECT
    ROW_NUMBER() OVER (ORDER BY t.municipality_code, t.permit_number) AS permit_sk,
    m.municipality_sk,
    t.permit_number,
    g.geography_sk,
    u.use_type_sk,
    t.raw_type AS use_type_raw,
    'source-field-mapped' AS use_type_classification_method,
    s.status_sk,
    t.status_raw,
    d1.date_sk AS date_applied_sk,
    d2.date_sk AS date_issued_sk,
    d3.date_sk AS date_closed_sk,
    CASE WHEN t.dwelling_units_created IS NOT NULL AND t.dwelling_units_lost IS NOT NULL
         THEN t.dwelling_units_created - t.dwelling_units_lost
         ELSE t.units_single END AS unit_count_net_new,
    'unknown' AS unit_count_basis,
    t.construction_value_cad,
    CASE WHEN t.municipality_code = 'TOR'
         THEN t.area_assembly + t.area_institutional + t.area_residential
            + t.area_business_personal + t.area_mercantile + t.area_industrial
            + t.area_interior_alterations + t.area_demolition
         WHEN t.municipality_code = 'MISS' THEN t.appl_area
         ELSE t.floor_area_single END AS floor_area_sqm,
    CAST(NULL AS VARCHAR) AS related_application_number,
    '{INGEST_DATE}' AS ingest_batch_id,
    CURRENT_TIMESTAMP AS row_loaded_at
FROM typed t
JOIN gold.dim_municipality m ON m.municipality_code = t.municipality_code
JOIN gold.dim_use_type u ON u.use_type_code = t.use_type_code
JOIN gold.dim_status s
    ON s.status_code = t.status_code AND s.applies_to = 'permit'
LEFT JOIN gold.dim_date d1 ON d1.calendar_date = t.date_applied
LEFT JOIN gold.dim_date d2 ON d2.calendar_date = t.date_issued
LEFT JOIN gold.dim_date d3 ON d3.calendar_date = t.date_closed
LEFT JOIN gold.dim_geography g
    ON g.municipality = 'Mississauga' AND g.ward_code = t.ward_ref
    AND g.vintage = 'mississauga-wards-current'
    AND t.municipality_code = 'MISS';
