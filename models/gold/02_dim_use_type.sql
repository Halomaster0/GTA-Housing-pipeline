-- Gold: dim_use_type. Grain: one row per conformed use-type code (hand
-- vocabulary, aligned with the AI track taxonomy). Raw→conformed mapping
-- lives in the fact SQL CASEs; every mapping is row-documented in
-- docs/conformance-matrix.md §1, not here.

CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE TABLE gold.dim_use_type AS
SELECT * FROM (VALUES
    (1, 'RESIDENTIAL', 'Residential', 'both'),
    (2, 'MIXED_USE', 'Mixed use', 'both'),
    (3, 'INSTITUTIONAL', 'Institutional', 'both'),
    (4, 'INFRASTRUCTURE', 'Infrastructure', 'both'),
    (5, 'OTHER', 'Other non-residential scope', 'both'),
    (6, 'UNKNOWN', 'No use signal in source', 'both')
) AS t (use_type_sk, use_type_code, use_type_label, applies_to);
