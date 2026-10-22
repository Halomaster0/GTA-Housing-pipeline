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
- **Windows / PowerShell: `make` is not installed by default.** Every `make X`
  in this document is a wrapper; run the command it wraps instead. The ones this
  manual needs:
  | Instead of | Run |
  |---|---|
  | `make export-csv` | `uv run python scripts/export_gold_parquet.py --format csv` |
  | `make export-gold` | `uv run python scripts/export_gold_parquet.py` |
  | `make reconcile` | `uv run python scripts/reconcile_measures.py` |
  | `make test` | `uv run pytest` |
  `make help` lists the rest with the command each one runs.
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

**Corrected 2026-10-22.** This table previously listed 571,986 / 221,319 /
34,614 under `Permits Issued`. Those are permit *record* counts, so a correctly
built model failed this gate and the instruction below told you to stop. The
two measures are now separate (§14) and both are checked here.

Table visual with `dim_municipality[municipality_name]` × `Permits Issued`
× `Permit Records` × `Net New Units`. Required, exact:

| Municipality | Permits issued | Permit records | Net units |
|---|---|---|---|
| Toronto | 462,039 | 571,986 | 259,840 |
| Brampton | 150,936 | 221,319 | 78,957 |
| Mississauga | 34,614 | 34,614 | 30,968 |
| **Total** | **647,589** | **827,919** | **do not total** |

Mississauga's two permit columns are equal because every Mississauga permit
carries an issue date inside `dim_date`'s range. Toronto and Brampton differ by
109,947 and 70,383 — partly permits with no issue date, partly permits issued
before 2010, which the date dimension does not cover.

**Never total the net units column** (ADR-0003, review D1): Toronto subtracts
demolition losses and the other two do not, so 369,765 is not a figure.

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

`make export-csv` (PowerShell: see §0) → Desktop: refresh/replace the 7 CSV sources → re-check
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

---

## 14. Generated PBIP path (makes §§2-6 unnecessary)

Source of truth: `scripts/generate_pbip.py`. Output, committed: `powerbi/`.
The semantic model (tables, columns, relationships, measures) is emitted as
TMDL text, so it is diffable and reproducible instead of living in a binary
that someone rebuilt by hand. Hand-building drifted once already: the
2026-10-22 review (D2) found a card whose formula did not match
`docs/fabric-dax.md`.

> **Status: generated, never opened in Desktop.** It was produced on a
> machine with no Power BI. The PBIP/TMDL format is version-sensitive, so the
> files may be rejected by your Desktop build or load with a surprise. Treat
> the first open as a test. **Nothing is published until §14.3 passes**, and
> §14.4 says what to do if a file is rejected.

### 14.1 What it replaces

| Manual | Done by the generated project |
|---|---|
| §2 Import | 7 table partitions: `Csv.Document` on `gold.<table>.csv`, `PromoteHeaders`, then an explicit type for every column (no type inference). One parameter, `GoldCsvFolder`, holds the folder for all seven. |
| §3 Renames | Table names are fixed in the model (`dim_date` ... `fct_applications`). |
| §4 Relationships | 13, all many-to-one, single direction. Both facts to the four dimensions (`municipality_sk`, `use_type_sk`, `status_sk`, `geography_sk`), all active. Date roles: `fct_permits[date_issued_sk]` and `fct_applications[date_submitted_sk]` are the only active links; `date_applied_sk`, `date_closed_sk`, `date_decision_sk` are inactive (`USERELATIONSHIP`). |
| §5 Date table | `dim_date` has `dataCategory: Time`; `calendar_date` is the key column. |
| §6 Measures | 8, with a description (and the reference value) on each: `Permits Issued`, `Permit Records`, `Net New Units`, `Date Coverage Pct`, `Median Applied to Issued Days`, `Construction Value CAD` on `fct_permits`; `Active Applications`, `Median Submitted to Decision Days` on `fct_applications`. **Do not paste the `fabric-dax.md` blocks**: they would collide ("name already used"). |

Every column and measure carries its definition as a TMDL description, so it
shows in the Data pane tooltip. `Net New Units` carries the ADR-0003 mixed-basis
caveat in its description: it travels with the measure wherever it is dragged.

### 14.2 First open

1. `make export-csv` (PowerShell:
   `uv run python scripts/export_gold_parquet.py --format csv`); check the row
   counts in §2 against `data/gold-csv/`. `fct_permits` must report 827,919.
2. Open `powerbi/gta-housing.pbip` in Power BI Desktop. If Desktop reports that
   the Power BI Project or TMDL format is a preview feature, enable it under
   File > Options > Preview features, restart, and reopen.
3. Home > Transform data > Manage parameters > `GoldCsvFolder` > set **Current
   value** to the absolute folder, e.g. `C:\Users\you\GTA-Housing-pipeline\data\gold-csv\`
   (trailing slash optional). This is the only path you set; all seven tables
   read it. The committed default, `..\data\gold-csv\`, is repo-relative from
   `powerbi/`, but Power Query may not resolve relative paths against the
   `.pbip`, so expect to overwrite it. Close & Apply and let all seven refresh.
4. Model view: confirm 13 relationships, three of them dashed (inactive).
5. Run the gate in §14.3.
6. **Before committing anything, regenerate** (`python scripts/generate_pbip.py`).
   Desktop re-saves the TMDL, and your absolute path would land in
   `expressions.tmdl`, i.e. your home directory in a public repo. Regenerating
   restores the relative default and discards Desktop's re-serialisation.
   `python scripts/generate_pbip.py --verify-output` fails if the model files
   differ from the generator, so run it before every commit.

### 14.3 Verification gate (replaces §7 for this path)

Table visual: `dim_municipality[municipality_name]` with `Permits Issued`,
`Permit Records`, `Net New Units`, `Date Coverage Pct`. Required, exact
(`docs/measure-reconciliation.json`):

| Municipality | Permits Issued | Permit Records | Net New Units | Date Coverage Pct |
|---|---|---|---|---|
| Toronto | 462,039 | 571,986 | 259,840 | 80.4% |
| Brampton | 150,936 | 221,319 | 78,957 | 68.1% |
| Mississauga | 34,614 | 34,614 | 30,968 | 99.9% |
| Total row | **647,589** | **827,919** | *delete this total* | 78.0% |

Then: `Active Applications` 2,668 (Toronto 1,694, Brampton 719, Mississauga
255); `Median Applied to Issued Days` Toronto 28, Mississauga 34, Brampton 44;
`Median Submitted to Decision Days` Mississauga 385, others blank;
`Construction Value CAD` Toronto $100,991,303,902, Mississauga $18,269,933,097,
Brampton blank. Caledon and Peel rows are blank by construction (ADR-0004).

**§7's table is superseded.** It lists 571,986 / 221,319 / 34,614 under
`Permits Issued`. Those are all permit rows, which is now the separate
`Permit Records` measure. The issue-date-filtered `Permits Issued` returns
462,039 / 150,936 / 34,614 (647,589 in total). If `Permits Issued` ever shows
827,919 it is counting every row, which is the 21.8% overstatement in review D2.
Any page-1 card labelled "Permits Issued" must read 647,589; a card showing
827,919 is `Permit Records` and must be labelled that way.

`Net New Units` is mixed-basis (review D1): never show a total across
municipalities, and keep the basis and 64.3% NULL-coverage note beside it.

Off by even 1: stop, do not build pages. A mismatch means the model is wrong,
never the JSON.

### 14.4 If Desktop rejects something

| Symptom | Likely cause | What to do |
|---|---|---|
| Desktop will not open the `.pbip` | Desktop older than the format, or the project/TMDL preview switch is off | Update Desktop; enable the preview features (§14.2 step 2) |
| Error naming a `.tmdl` file and line | A syntax detail the generator assumed (see §14.5) | Note the file, line and message. Fix `scripts/generate_pbip.py` and regenerate. Do not hand-edit the output and commit it. Use the fallback below to keep working meanwhile |
| Error naming `report.json`, `definition.pbir` or `.platform` | The deliberately minimal report shell | Fallback below. The report holds no visuals, so nothing is lost |
| Refresh fails with "file not found" | `GoldCsvFolder` | Set the absolute path (§14.2 step 3) |
| `row_loaded_at` shows blank | Timestamp text not parsed by Power Query | Harmless: lineage only, and no measure reads it |
| Hidden `LocalDateTable_*` tables appear | Auto date/time is on | File > Options > Current file > Data load > Time intelligence off |
| §14.3 values differ | Stale CSVs, or a relationship/measure fault | Re-export; then §12; do not build on it |

**Fallback (Desktop provides the shell, the generator provides the model):**
(1) In Desktop create a blank report and File > Save as > Power BI Project in a
scratch folder, then close it. (2) In that scratch project's
`*.SemanticModel` folder, replace `definition/` with the generated
`powerbi/gta-housing.SemanticModel/definition/`. (3) Open the scratch `.pbip`.
If it now loads, the fault was in the report shell or `.pbip` wrapper; if it
still fails, the fault is TMDL syntax inside `definition/` and the error
message names the line.

### 14.5 What is pinned, and what is a guess

- `compatibilityLevel: 1567` (`database.tmdl`). It is the long-standing level
  that PBIP/TMDL samples use. Everything this model needs (M partitions,
  parameters, inactive relationships, `dataCategory`/`isKey` date tables) exists
  at or below it, so a Desktop build that reads TMDL should accept 1567 (not
  verified here); Desktop raises the level itself when it saves. Pinning higher
  buys nothing we use and risks a "created with a newer version" refusal.
- `definition.pbism` `version: 4.0`, the first version that means "TMDL folder".
- Report: the legacy `report.json` format (`definition.pbir` version 1.0), one
  empty page. A Desktop that defaults to the newer PBIR folder format may offer
  to upgrade it on save; accept, nothing is lost.
- **Unverified, check first if a file is rejected:** descriptions written as
  `///` doc-comments; DAX bodies in triple-backtick fences; relationship names
  quoted; `isKey: true` written explicitly; `database` declared with no name;
  `ref table` lines in `model.tmdl` with no `ref expression`; the minimal
  `report.json` fields and its `config` version string; the `$schema` URLs;
  `annotation __PBI_TimeIntelligenceEnabled = 0`.

### 14.6 Guards and ownership

| Command | Purpose | Exit 1 when |
|---|---|---|
| `python scripts/generate_pbip.py` | (Re)write the model | never |
| `python scripts/generate_pbip.py --check-schema [warehouse]` | Compare the embedded gold spec with the live warehouse (default `data/warehouse.duckdb`) | any missing table or column, extra column, type change or reordering |
| `python scripts/generate_pbip.py --verify-output` | Compare `powerbi/` with what the generator would write | a model file differs or is missing |

Run `--check-schema` after every `make transform` that touches `models/gold/`.
When it fails, update `GOLD_SPEC` in the script, regenerate, and redo §14.3.
Exit code 2 means the check could not run (no warehouse file).

The generator **owns the semantic model** and rewrites it every run. The
`.pbip` and `gta-housing.Report/` are created once and never overwritten, so
pages you build in Desktop survive regeneration. A model change made in Desktop
(a new measure or column) exists only in your local copy until it is added to
the script, and the next run erases it.

### 14.7 Not in the generated project

- **Report pages**: build per `docs/report-plan.md` and §13.
- **§13 calculated columns** (`Days Applied to Issued`, `Days Bucket`,
  `Days Bucket Sort`) and the §13.4 measures that depend on them. Create them
  in Desktop, then port them into the generator or the next regeneration drops
  them. **Skip `Date Coverage Pct` in §13.4**: the generated model already has
  it, computed directly from the two date keys, and a second one gives "name
  already used".
- Hierarchies, the documented RLS role, and the per-capita measures (P1-P3).
  The first two belong to the model but were out of scope for this change.
