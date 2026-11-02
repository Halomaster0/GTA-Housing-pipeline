DECISION 2026-10-31 — DATA VINTAGE
Working source (not the published source since Update 2026-11-02): current gold warehouse (data/warehouse.duckdb, 833,848 permit rows; 652,715 issued via date_issued_sk IS NOT NULL).
Held / comparison: data/gold-sept-csv/ (September export from gtb-housing-v1.pbix, ~827,919) preserved as audit comparison only.
Toronto unit exception — DECISION MADE 2026-10-31 by agent (delegate): EXCLUDE from all published measures. Reason: placeholder/data-entry artifact (status_raw="Application On Hold", not issued; 100,000 vs realistic max ~1,408; alone accounts for +100,803 of Toronto unit move; no human auditor assigned yet per data-exceptions.yml). Card/measure notes must state: "Toronto net-units: excluded pending audit — unverified 100k-unit placeholder (2026-10-22)". Update decision in docs/data-exceptions.yml from UNRESOLVED -> EXCLUDED-PENDING (with this note) when audit completes.
Published measures re-derived from warehouse: superseded by Update 2026-11-02 below. Published figures stay on the September export until October Toronto data is validated.

## Update 2026-11-02

The user decided that the published Power BI figures stay on the September export until October Toronto data is validated. This supersedes the "published measures re-derived from warehouse" wording above.

- Published: September export (data/gold-sept-csv/, 2026-09-10 ingest). Permit Records 827,919; Permits Issued 647,589 (TOR 462,039 / MISS 34,614 / BRAM 150,936).
- Working: October warehouse (data/warehouse.duckdb, 833,848 permit rows; 652,715 issued; TOR 465,637 / MISS 35,041 / BRAM 152,037). It is the working source only and does not replace the published figures until October Toronto data is validated.
- The Toronto 100,000-unit placeholder (permit 26 256637 BLD) stays EXCLUDED from published Toronto net units pending audit. It is not in the September data at all.
- Still open: whether CANCELLED permits with an issue date count as issued. This needs a director decision and must be recorded in docs/data-dictionary.md.
