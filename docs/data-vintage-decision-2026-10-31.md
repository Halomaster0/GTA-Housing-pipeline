DECISION 2026-10-31 — DATA VINTAGE
Source of authority: current gold warehouse (data/warehouse.duckdb, 833,848 permit rows; 652,715 issued via date_issued_sk IS NOT NULL).
Held / comparison: data/gold-sept-csv/ (September export from gtb-housing-v1.pbix, ~827,919) preserved as audit comparison only.
Toronto unit exception — DECISION MADE 2026-10-31 by agent (delegate): EXCLUDE from all published measures. Reason: placeholder/data-entry artifact (status_raw="Application On Hold", not issued; 100,000 vs realistic max ~1,408; alone accounts for +100,803 of Toronto unit move; no human auditor assigned yet per data-exceptions.yml). Card/measure notes must state: "Toronto net-units: excluded pending audit — unverified 100k-unit placeholder (2026-10-22)". Update decision in docs/data-exceptions.yml from UNRESOLVED -> EXCLUDED-PENDING (with this note) when audit completes.
Published measures re-derived from warehouse: permitted.
