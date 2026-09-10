-- Gold: dim_status. Grain: one row per conformed status code, split by
-- applies_to (permit/application are different domains — schema §2.7).
-- Raw→conformed mapping lives in the fact SQL CASEs; every value mapped in
-- docs/conformance-matrix.md §2. stage_order feeds Pipeline Velocity;
-- is_terminal defines "active application" counts.

CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE TABLE gold.dim_status AS
SELECT * FROM (VALUES
    -- permit domain
    (1, 'APPLIED', 'Applied', 'permit', 1, FALSE),
    (2, 'UNDER_REVIEW', 'Under review', 'permit', 2, FALSE),
    (3, 'ISSUED', 'Issued (live permit)', 'permit', 3, FALSE),
    (4, 'CLOSED', 'Closed', 'permit', 4, TRUE),
    (5, 'CANCELLED', 'Cancelled / refused / abandoned', 'permit', 5, TRUE),
    (6, 'EXPIRED', 'Expired', 'permit', 6, TRUE),
    (7, 'UNKNOWN', 'Unknown permit status', 'permit', 0, FALSE),
    -- application domain
    (11, 'SUBMITTED', 'Submitted', 'application', 1, FALSE),
    (12, 'UNDER_REVIEW', 'Under review', 'application', 2, FALSE),
    (13, 'APPROVED', 'Approved', 'application', 3, TRUE),
    (14, 'REFUSED', 'Refused', 'application', 4, TRUE),
    (15, 'APPEALED', 'Under appeal', 'application', 5, FALSE),
    (16, 'WITHDRAWN', 'Withdrawn', 'application', 6, TRUE),
    (17, 'CLOSED', 'Closed', 'application', 7, TRUE),
    (18, 'UNKNOWN', 'Unknown application status', 'application', 0, FALSE)
) AS t (status_sk, status_code, status_label, applies_to, status_stage_order, is_terminal);
