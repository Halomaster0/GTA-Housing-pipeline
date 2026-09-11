# Power BI master document — the complete solo runbook

Owner: whoever builds the report (CEO practicing for PL-300, or
`report-builder`). Scope: workspace → import → model → verify → 5 pages →
publish → embed test → refresh. Every number to check against is printed
inline; sources of truth are `docs/measure-reconciliation.json` (values),
`docs/fabric-dax.md` (DAX), `docs/report-plan.md` (page specs).

Status: model proven 2026-09-11 (Toronto 571,986 / 259,840 verified in a
table visual). Pages 2–5, publish, and embed test are still ahead.

## 0. Prerequisites (all free, all $0)

- Power BI Desktop installed (Windows, school or personal machine).
- Repo cloned; gold CSVs present: run `make export-csv` (or
  `python scripts/export_gold_parquet.py --format csv`). Files land in
  `data/gold-csv/` (gitignored, ~125 MB total, biggest file 123 MB).
- School login able to create a **Power BI Pro** workspace (ADR-0010 —
  PPU rejected, no lakehouse on this tenant).

## 1. Workspace

Power BI service → Workspaces → New workspace → name `gta-housing` → Pro →
Apply. Keep it separate from coursework. Leave it empty.

## 2. Import (Desktop)

Home → Get Data → **Text/CSV** (not Parquet — Desktop's Parquet connector
is URL-only and will prompt for a web address). Select all 7
`data/gold-csv/gold.*.csv` files → Load. In Data view confirm row counts:
`fct_permits` 827,919 · `fct_applications` 21,658 · `dim_date` 6,940 ·
`dim_geography` 89 · `dim_municipality` 5 · `dim_use_type` 6 ·
`dim_status` 15. Any mismatch: stop, the export is stale — re-run it.

## 3. Rename tables (Model view, do this before anything else)

Strip any import prefix so names match every doc in this repo:
`gold fct_permits` → `fct_permits`, same for `fct_applications`,
`dim_date`, `dim_municipality`, `dim_use_type`, `dim_status`,
`dim_geography`. Relationships follow renames automatically.

## 4. Relationships (Model view → Manage relationships, one pair per dialog)

All many-to-one, single filter direction. Delete anything auto-detected
beyond this list.

`fct_permits` (7): `municipality_sk`, `use_type_sk`, `status_sk`,
`geography_sk` → matching dims (all **active**); `date_issued_sk` →
`dim_date[date_sk]` **active**; `date_applied_sk`, `date_closed_sk` →
`dim_date` **inactive**.

`fct_applications` (6): `municipality_sk`, `use_type_sk`, `status_sk`,
`geography_sk` → matching dims (all **active**); `date_submitted_sk` →
`dim_date` **active**; `date_decision_sk` → `dim_date` **inactive**.

Two traps: geography joins on **`geography_sk`** (unique 1–89), never
`ward_code` (repeated across vintages — Power BI rejects it); only one
active date link per fact table or time-based numbers silently corrupt.

## 5. Date table

Select `dim_date` → Table tools → Mark as Date Table → `calendar_date`.

## 6. Measures (Report view → right-click table → New measure)

Copy the 8 blocks from `docs/fabric-dax.md` verbatim (M1–M8). Three rules:
names left of `=` are plain letters/spaces only (no `M1 — …` labels, no
comments in the name box); paste formula only; a "name already used" error
means the measure exists — find it in the Data pane, check it, keep or
delete it, don't duplicate it.

## 7. Verify the model (gate before any page)

Table visual with `dim_municipality[municipality_name]` × `Permits Issued`
× `Net New Units`. Required, exact:

| Municipality | Permits | Net units |
|---|---|---|
| Toronto | 571,986 | 259,840 |
| Brampton | 221,319 | 78,957 |
| Mississauga | 34,614 | 30,968 |

(Caledon/Peel rows may appear blank — correct by construction, ADR-0004.)
Off by even 1: stop, do not build pages. Save as `gta-housing-v1.pbix`.

## 8. The five pages (`docs/report-plan.md` is the spec; this is the checklist)

1. **GTA Overview** — cards (Permits Issued, Net New Units, Active
   Applications); bar (year × permits, legend municipality, data labels);
   donut (application `status_code` legend × `Count of application_number`);
   one-sentence text box with last refresh 2026-09-10.
2. **Municipal Comparison** — same volumes; per-capita panel is an EXPLICIT
   empty state ("pending StatCan census profiles", P1) plus the Caledon
   no-data card (never a zero).
3. **Pipeline Velocity** — applied→issued histogram with medians TOR 28d /
   MISS 34d / BRAM 44d (coverage n in `measure-reconciliation.json`);
   submitted→decision Mississauga-only (385d); Toronto/Brampton decision
   panels + application→permit timing are empty states citing the reason.
4. **Geography** — ward map for Mississauga + Toronto applications (ward-
   attributed rows only: state the denominator); Brampton ward view carries
   the UNCONFIRMED-equivalence footnote; Toronto permits are NOT mapped.
5. **Data Quality & Freshness** — refresh date, per-source counts, gold
   totals, 0/0 orphans, null-geography + unknown-use counts with reasons,
   unit-basis banner, P1–P3 list. Generated from the reconciliation JSON +
   quality report, never hand-typed.

## 9. Publish

Desktop: File → Publish → Publish to Power BI → `gta-housing` workspace.
Then in the service, open the report and re-check the §7 table values —
publish must not change numbers.

## 10. Embed test (decides `/dashboard`)

Report → File → Embed report → Publish to web (public). If the tenant
allows it: copy the iframe URL — that URL is the Gate 3 dashboard criterion
and the `/dashboard` embed source. If blocked: fallback is a private report
link + committed screenshots (decide then; `OUTSTANDING.md` tracks it).

## 11. Refresh SOP (each new ingest date)

`make export-csv` → Desktop: refresh/replace the 7 CSV sources → re-check
§7 table → `make reconcile` → republish → confirm embed still loads. If any
measure drifts beyond ±20% with no explanation, the publish fails and the
dashboard keeps showing the last good refresh with its date.

## 12. Troubleshooting (every wall hit in v1, with fixes)

| Symptom | Cause | Fix |
|---|---|---|
| Parquet import asks for a URL | Connector is URL-only | Use Text/CSV (§2) |
| Table names contain spaces (`gold fct_permits`) | Filename prefix import | Rename once (§3), don't bracket forever |
| "Enclose the name in brackets" on paste | Non-plain text in the measure name box | Plain names only, formula only (§6) |
| "Name already used" | Measure exists from an earlier attempt | Inspect in Data pane; keep or delete (§6) |
| Geography link refused ("unique values") | Used `ward_code` | Use `geography_sk` both sides (§4) |
| Time visuals look doubled | Two active date links on one fact | Exactly one active date role per fact (§4) |
| Counts mismatch §7 | Stale CSVs or wrong relationship | Re-export; re-check §4; stop, don't build |
