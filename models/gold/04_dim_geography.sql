-- Gold: dim_geography. Grain: one row per ward-boundary version
-- (municipality, ward code, effective start) — never the code alone
-- (ADR-0007). Municipality is the lower-tier authority (Toronto /
-- Mississauga / Brampton; Peel wards attach to their Municipali value).
-- census_tract linkage is 'unresolved' in v1 (no spatial step yet);
-- tract denominators live in silver.census_tracts.

CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE TABLE gold.dim_geography AS
SELECT
    ROW_NUMBER() OVER (
        ORDER BY municipality, ward_code, COALESCE(effective_start, DATE '1900-01-01')
    ) AS geography_sk,
    municipality,
    ward_code,
    ward_name,
    vintage,
    effective_start,
    effective_end,
    is_current,
    CAST(NULL AS VARCHAR) AS census_tract_id,
    'unresolved' AS census_tract_allocation_method,
    CASE WHEN geometry_geojson IS NULL THEN 'unknown' ELSE 'exact-boundary' END
        AS geometry_precision,
    'EPSG:4326' AS geometry_crs
FROM silver.wards;
