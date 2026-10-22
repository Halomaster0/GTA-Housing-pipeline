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
3. **Pipeline Velocity** — full step-by-step build in **§13**; applied→issued
   histogram with medians TOR 28d / MISS 34d / BRAM 44d (coverage n in
   `measure-reconciliation.json`);
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

---

## 13. Page 3 — Pipeline Velocity, step by step

The only page whose headline comparison is on a basis that is genuinely
comparable across all three municipalities. Build it carefully; it carries more
weight than page 1.

### 13.0 The trap, before you write any DAX

`dim_date[date_sk]` is `YEAR*10000 + MONTH*100 + DAY`
(`models/gold/00_dim_date.sql:13`). **Never subtract two `date_sk` values.**
`20260301 - 20260228` is 73, not 1. Every duration on this page must come from
real dates. M6 and M7 already avoid this with `LOOKUPVALUE`; the calculated
column below does it with arithmetic.

### 13.1 Calculated column — days from applied to issued

A histogram bins one value per row, so this must be a **column**, not a measure.
Model view → `fct_permits` → New column.

```dax
Days Applied to Issued =
VAR A = fct_permits[date_applied_sk]
VAR I = fct_permits[date_issued_sk]
VAR AppliedDate =
    IF ( NOT ISBLANK ( A ), DATE ( INT ( A / 10000 ), MOD ( INT ( A / 100 ), 100 ), MOD ( A, 100 ) ) )
VAR IssuedDate =
    IF ( NOT ISBLANK ( I ), DATE ( INT ( I / 10000 ), MOD ( INT ( I / 100 ), 100 ), MOD ( I, 100 ) ) )
RETURN
    IF (
        NOT ISBLANK ( AppliedDate ) && NOT ISBLANK ( IssuedDate ),
        DATEDIFF ( AppliedDate, IssuedDate, DAY )
    )
```

The arithmetic is valid only because *we* define `date_sk` as YYYYMMDD. It is
used instead of two `LOOKUPVALUE` calls because those scan `dim_date` twice for
each of 827,919 rows and can take minutes. If you would rather not depend on the
convention, swap in the `LOOKUPVALUE` form from M6 — same answer, much slower.

### 13.2 Check for negatives before building anything on it

Drop a card with `MIN ( fct_permits[Days Applied to Issued] )`.

If it is below zero, some permits are recorded as issued before they were
applied for. That is a real source defect and a finding, not noise. **Do not
filter it away silently** — it gets its own bucket below and a line on page 5.
If the minimum is 0 or above, delete the card and carry on.

### 13.3 Bucket and sort columns

Two more columns on `fct_permits`. Bins from the "New group" dialog produce a
long tail of near-empty bins, so these are explicit.

```dax
Days Bucket =
VAR d = fct_permits[Days Applied to Issued]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( d ), "No dates",
        d < 0, "Issued before applied",
        d <= 7, "0-7",
        d <= 14, "8-14",
        d <= 30, "15-30",
        d <= 60, "31-60",
        d <= 90, "61-90",
        d <= 180, "91-180",
        d <= 365, "181-365",
        "365+"
    )
```

```dax
Days Bucket Sort =
VAR d = fct_permits[Days Applied to Issued]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( d ), 99,
        d < 0, 0,
        d <= 7, 1, d <= 14, 2, d <= 30, 3, d <= 60, 4,
        d <= 90, 5, d <= 180, 6, d <= 365, 7,
        8
    )
```

Then select `Days Bucket` → Column tools → **Sort by column** → `Days Bucket
Sort`. Skip this and the axis sorts alphabetically, putting "0-7" next to
"181-365".

### 13.4 Measures

```dax
/* COUNT ignores blanks, so this is exactly "permits having both dates" */
Permits With Both Dates = COUNT ( fct_permits[Days Applied to Issued] )

/* Independent twin of M6. Must agree with it — see 13.7 */
Median Days Applied to Issued = MEDIAN ( fct_permits[Days Applied to Issued] )

/* Coverage: the denominator differs per municipality and must be visible */
Date Coverage Pct = DIVIDE ( [Permits With Both Dates], COUNTROWS ( fct_permits ) )

/* Share within each municipality, so distribution shapes are comparable */
Share of Dated Permits =
DIVIDE (
    [Permits With Both Dates],
    CALCULATE ( [Permits With Both Dates], REMOVEFILTERS ( fct_permits[Days Bucket] ) )
)
```

`Share of Dated Permits` is the one that matters. Toronto has 460,121 dated
permits against Brampton's 150,680, so a raw-count histogram makes Toronto's
bars dwarf Brampton's and you cannot compare the shapes — which is the entire
question the page asks. Plot the share and state the counts separately.

### 13.5 Visuals

**Top — matrix.** Rows: `dim_municipality[municipality_name]`. Values:
`Median Days Applied to Issued`, `Permits With Both Dates`, `Date Coverage Pct`.
This is the page's answer in one object.

**Middle — clustered column chart** (the histogram). X axis: `Days Bucket`.
Y axis: `Share of Dated Permits`, formatted as a percentage. Small multiples:
`dim_municipality[municipality_name]`. Small multiples beat a legend here —
three side-by-side distributions read instantly, three overlapping series do
not. Sort the X axis by `Days Bucket Sort` ascending, not by value.

**Bottom left — submitted to decision.** A card with
`Median Submitted to Decision Days` (M7) and a card with the application count,
both filtered to Mississauga. Beside them, two text boxes, not blank space:

> **Toronto — no decision dates in source.** The development applications feed
> carries `DATE_SUBMITTED` and a current `STATUS`, with no decision date. The
> measure is defined and cannot be computed.

> **Brampton — no decision dates in source.** The planning layers carry no
> decision date field.

**Bottom right — application to permit timing.** One text box:

> **Not computable.** No permit-to-application key exists in any of the three
> feeds (`related_application_number` is NULL for all 827,919 permits). Linking
> them on address or date would fabricate a relationship the sources do not
> assert. See ADR-0006.

**Footnote.** Coverage denominators, because the histogram hides them:
Toronto 460,121 of 571,986 (80.4%) · Mississauga 34,581 of 34,614 (99.9%) ·
Brampton 150,680 of 221,319 (68.1%).

### 13.6 What the page must not do

Do not fill the three empty states. Do not average the three medians into a
"GTA median" — different coverage rates make that meaningless. Do not trend
medians by year without re-stating coverage per year, since Mississauga has no
permits before 2018.

### 13.7 Verification gate — before you move to page 4

From `docs/measure-reconciliation.json`, confirm on the matrix:

| Municipality | Median days | Permits with both dates |
|---|---|---|
| Toronto | **28** | **460,121** |
| Mississauga | **34** | **34,581** |
| Brampton | **44** | **150,680** |

Total dated permits: **645,382**. Mississauga M7: **385** days over **1,163**
applications.

`Median Days Applied to Issued` and M6 are computed two different ways and must
return the same three numbers. If they disagree, the calculated column is wrong
— most likely a `date_sk` subtraction crept in (13.0). If the matrix disagrees
with the table above, stop and re-export; do not build on it.
