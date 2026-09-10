-- Silver: application status history (SCD Type 2, bronze-snapshot-diff).
-- Grain: one row per (municipality, application_number, status) contiguous
-- validity period. No source publishes a native status log (A6 confirmed),
-- so history is reconstructed by diffing each run's snapshot against the
-- persisted table: granularity is the ingest cadence, left-truncated at
-- pipeline launch, and only "first observed between run A and B" is known —
-- never the true change date (schema design §5). detection_method records
-- this plainly on every row.
-- This script is re-runnable: it merges the current snapshot into the
-- persisted table (created on first run), closing stale `is_current` rows
-- and opening new ones. Brand-new applications open a row; unchanged ones
-- are untouched.

CREATE SCHEMA IF NOT EXISTS silver;

CREATE TABLE IF NOT EXISTS silver.application_status_history (
    municipality VARCHAR,
    application_number VARCHAR,
    status_raw VARCHAR,
    effective_start DATE,
    effective_end DATE,
    is_current BOOLEAN,
    detection_method VARCHAR
);

CREATE OR REPLACE TEMP VIEW _snapshot AS
SELECT 'Toronto' AS municipality, application_number, status_raw
FROM silver.toronto_applications
UNION
SELECT 'Mississauga', application_number, status_raw
FROM silver.mississauga_applications
UNION
SELECT 'Brampton', file_number, status_raw
FROM (SELECT DISTINCT file_number, status_raw FROM silver.brampton_applications);

-- Close rows whose status no longer matches the snapshot.
UPDATE silver.application_status_history AS h
SET effective_end = DATE '{INGEST_DATE}' - INTERVAL 1 DAY,
    is_current = FALSE
WHERE h.is_current
  AND NOT EXISTS (
    SELECT 1 FROM _snapshot s
    WHERE s.municipality = h.municipality
      AND s.application_number = h.application_number
      AND s.status_raw IS NOT DISTINCT FROM h.status_raw
);

-- Open rows for new applications and for changed statuses.
INSERT INTO silver.application_status_history
SELECT s.municipality, s.application_number, s.status_raw,
    DATE '{INGEST_DATE}', NULL, TRUE, 'bronze-snapshot-diff'
FROM _snapshot s
WHERE NOT EXISTS (
    SELECT 1 FROM silver.application_status_history h
    WHERE h.is_current
      AND h.municipality = s.municipality
      AND h.application_number = s.application_number
      AND h.status_raw IS NOT DISTINCT FROM s.status_raw
);
