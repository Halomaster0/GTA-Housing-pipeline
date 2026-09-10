-- Gold: dim_municipality. Grain: one row per municipality in scope (5 rows —
-- Toronto, Mississauga, Brampton, Peel Region, Caledon — per ADR-0004).
-- Population stays NULL until a StatCan CSD pull lands (evidence §8).

CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE TABLE gold.dim_municipality AS
SELECT
    ROW_NUMBER() OVER (ORDER BY municipality_code) AS municipality_sk,
    municipality_code,
    municipality_name,
    municipality_tier,
    parent_region_code,
    is_permit_issuing_authority,
    CAST(NULL AS BIGINT) AS population_latest,
    CAST(NULL AS SMALLINT) AS population_reference_year,
    CAST(NULL AS VARCHAR) AS population_source
FROM silver.municipalities;
