DECISION 2026-10-31 — DATA VINTAGE
Source of authority: current gold warehouse (data/warehouse.duckdb, 833,848 permit rows; 652,715 issued via date_issued_sk IS NOT NULL).
Held / comparison: data/gold-sept-csv/ (September export from gtb-housing-v1.pbix, ~827,919) preserved as audit comparison only.
Toronto unit exception: docs/data-exceptions.yml entry for permit_number "26 256637 BLD" (100,000 units, status_raw "Application On Hold", first_seen 2026-10-22, decision UNRESOLVED). Not published. Card/measure notes must state gap.
Published measures re-derived from warehouse: permitted.
