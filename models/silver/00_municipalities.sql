-- Silver: municipalities (seed).
-- Grain: one row per municipality in project scope (Toronto, Mississauga,
-- Brampton, Peel Region, Caledon). Hand-curated scope metadata, not a live
-- source. Peel/Caledon carry is_permit_issuing_authority = FALSE per
-- ADR-0004 (their absence from facts is structural, never a data gap).
-- Population stays NULL until a StatCan CSD pull lands (evidence §8).

CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE TABLE silver.municipalities AS
SELECT * FROM (VALUES
    ('TOR', 'Toronto', 'single-tier', NULL, TRUE),
    ('MISS', 'Mississauga', 'lower-tier', 'PEEL', TRUE),
    ('BRAM', 'Brampton', 'lower-tier', 'PEEL', TRUE),
    ('PEEL', 'Peel Region', 'upper-tier', NULL, FALSE),
    ('CALE', 'Caledon', 'lower-tier', 'PEEL', FALSE)
) AS t (
    municipality_code, municipality_name, municipality_tier,
    parent_region_code, is_permit_issuing_authority
);
