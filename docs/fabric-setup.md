# Fabric setup — DRAFT, UNPROVISIONED (no trial, no spend)

Status (2026-09-11, supersedes the trial plan per ADR-0010): the school
tenant offers Power BI Pro / PPU only — no Fabric capacity, so §§1–2
(lakehouse/OneLake) are the upgrade path, not the plan. Serving v1 is
Power BI Desktop → Pro workspace (see ADR-0010). Nothing below the lakehouse
line has been clicked or provisioned. Until then the local path
(`make transform` → DuckDB → `data/gold-parquet/`) is the entire serving
story and every demo runs from it.

Cost gate: provisioning anything here needs a CEO decision recorded in
`docs/cost-log.md` BEFORE the click. Current serving spend: CAD $0.00.

## 1. OneLake folder convention

```
OneLake / gta-housing-lh /
  Files / gold-parquet / gold.{table}.parquet   # uploaded from data/gold-parquet/
  Tables / dim_date | dim_municipality | dim_geography | dim_use_type |
             dim_status | fct_permits | fct_applications   # 1:1 from parquet
```

## 2. Lakehouse tables mapped 1:1 from gold parquet

| Lakehouse table | Source file | Rows 2026-09-10 | Notes |
|---|---|---|---|
| `dim_date` | `gold.dim_date.parquet` | 6,940 | Mark as date table in the semantic model |
| `dim_municipality` | `gold.dim_municipality.parquet` | 5 | |
| `dim_geography` | `gold.dim_geography.parquet` | 89 | |
| `dim_use_type` | `gold.dim_use_type.parquet` | 6 | |
| `dim_status` | `gold.dim_status.parquet` | 15 | |
| `fct_permits` | `gold.fct_permits.parquet` | 827,919 | |
| `fct_applications` | `gold.fct_applications.parquet` | 21,658 | |

Export verified locally: `scripts/export_gold_parquet.py` prints per-table
counts; `scripts/reconcile_measures.py` re-verifies them against the
warehouse. The upload step copies bytes; it does not transform them.

## 3. Publish path

`data/gold-parquet/*.parquet` (local, `make export-gold`) → OneLake Files →
Lakehouse Tables (shortcut or load) → SQL endpoint → semantic model
(relationships per `docs/data-dictionary.md`, measures M1–M8) → Power BI
report (`docs/report-plan.md`) → publish to web → URL recorded here and in
the README. The `/dashboard` page embeds that URL.

## 4. Execution checklist (for the provisioned session — all owed)

- [ ] Trial workspace created (URL + date recorded here)
- [ ] Lakehouse `gta-housing-lh` created (screenshot, dated)
- [ ] Parquet uploaded, 7 tables loaded, row counts match §2 (paste output)
- [ ] SQL endpoint reachable; semantic model relationships set, single filter direction
- [ ] Measures M1–M8 created in DAX; values match `measure-reconciliation.json`
- [ ] Report pages 1–5 published per `report-plan.md`; public URL recorded
- [ ] Refresh strategy set (weekly, after `pipeline.yml`); failure behaviour documented
- [ ] `reconcile_measures.py` re-run post-refresh as the publish gate

## 5. Refresh strategy + what breaks if refresh fails

Weekly scheduled refresh after the GitHub `pipeline.yml` run lands a new
`ingest_date`. Refresh re-runs export → upload → model refresh, then the
reconcile script: any measure drift beyond the ±20% data-test guard fails
the publish and opens an issue — the dashboard keeps showing the last good
refresh with its date, never a half-loaded model. If the Fabric trial
lapses, §3 collapses back to the local path with zero rework: the parquet,
the dictionary, and the report plan are all trial-independent.
