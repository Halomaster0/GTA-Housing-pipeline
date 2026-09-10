-- Gold: dim_date. Grain: one row per calendar date, 2010-01-01..2028-12-31.
-- Fiscal = calendar per Director ruling §8-5 (A20 accepted for v1); a
-- non-calendar municipal series would move fiscal attrs to a bridge (ADR).

CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE TABLE gold.dim_date AS
WITH spine AS (
    SELECT (DATE '2010-01-01' + INTERVAL (d) DAY)::DATE AS calendar_date
    FROM range(0, (DATE '2028-12-31' - DATE '2010-01-01') + 1) AS t(d)
)
SELECT
    (YEAR(calendar_date) * 10000 + MONTH(calendar_date) * 100 + DAY(calendar_date)) AS date_sk,
    calendar_date,
    YEAR(calendar_date) AS year,
    QUARTER(calendar_date) AS quarter,
    MONTH(calendar_date) AS month,
    MONTHNAME(calendar_date) AS month_name,
   STRFTIME(calendar_date, '%b') AS month_short_name,
    DAY(calendar_date) AS day_of_month,
    ISODOW(calendar_date) AS day_of_week_iso,
    DAYNAME(calendar_date) AS day_name,
    ISODOW(calendar_date) IN (6, 7) AS is_weekend,
    WEEKOFYEAR(calendar_date) AS week_of_year_iso,
    YEAR(calendar_date) AS iso_year,
    DAYOFYEAR(calendar_date) AS day_of_year,
    YEAR(calendar_date) AS fiscal_year,
    QUARTER(calendar_date) AS fiscal_quarter,
    MONTH(calendar_date) AS fiscal_month
FROM spine;
