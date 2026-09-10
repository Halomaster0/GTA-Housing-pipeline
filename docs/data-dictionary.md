# Data dictionary — gold star schema + measure library

Owner: `semantic-model-designer`. Every table, column, and measure in the
serving layer, with business definitions. All row counts and measure values
are verified against the warehouse by `scripts/reconcile_measures.py` →
`docs/measure-reconciliation.json` (regenerate, don't hand-edit numbers).
Reconciliation values below are from the 2026-09-10 run
(`fct_permits` 827,919 · `fct_applications` 21,658).

Unit caveat rides with every unit measure: `unit_count_basis = 'unknown'`
everywhere (ADR-0003) — cross-municipality unit sums are NOT comparable.

## Tables

### gold.dim_date — one row per calendar date, 2010-01-01 → 2028-12-31 (6,940 rows)

| Column | Type | Definition |
|---|---|---|
| `date_sk` | BIGINT | Surrogate key (`YYYYMMDD`). Join target for all fact date roles |
| `calendar_date` | DATE | The date |
| `year` / `quarter` / `month` | BIGINT | Calendar parts |
| `month_name` / `month_short_name` / `day_name` | VARCHAR | Display labels |
| `day_of_month` / `day_of_week_iso` / `week_of_year_iso` / `iso_year` / `day_of_year` | BIGINT | Calendar parts |
| `is_weekend` | BOOLEAN | Sat/Sun flag |
| `fiscal_year` / `fiscal_quarter` / `fiscal_month` | BIGINT | Municipal fiscal calendar (April start) |

Mark as the date table in the semantic model (PL-300: Model data).

### gold.dim_municipality — one row per municipality (5 rows)

| Column | Type | Definition |
|---|---|---|
| `municipality_sk` | BIGINT | Surrogate key |
| `municipality_code` | VARCHAR | `TOR` / `MISS` / `BRAM` / `CALE` / `PEEL` |
| `municipality_name` | VARCHAR | Display name |
| `municipality_tier` | VARCHAR | `single-tier` (Toronto), `lower-tier` (Peel members), `upper-tier` (Peel) |
| `parent_region_code` | VARCHAR | `PEEL` for members, NULL otherwise |
| `is_permit_issuing_authority` | BOOLEAN | FALSE for Peel + Caledon — they have zero fact rows by construction (ADR-0004) |
| `population_latest` / `population_reference_year` / `population_source` | BIGINT / SMALLINT / VARCHAR | **All NULL in v1** — populated from StatCan census profiles once series pulls work (Gate 2 item iii). Per-capita measures are defined but uncomputable until then |

### gold.dim_geography — one row per municipality × ward × vintage (89 rows)

| Column | Type | Definition |
|---|---|---|
| `geography_sk` | BIGINT | Surrogate key |
| `municipality` / `ward_code` / `ward_name` | VARCHAR | Ward identity within its vintage |
| `vintage` | VARCHAR | `city-wards-current` (Toronto), `mississauga-wards-current`, `peel-2018-2022`, `peel-2022-2026` (ADR-0007) |
| `effective_start` / `effective_end` / `is_current` | DATE / DATE / BOOLEAN | Vintage validity |
| `census_tract_id` | VARCHAR | **NULL in v1** — tract linkage `unresolved`, no spatial step yet |
| `census_tract_allocation_method` | VARCHAR | Always `'unresolved'` in v1 |
| `geometry_precision` | VARCHAR | `'unknown'` — no geometries stored, codes only |
| `geometry_crs` | VARCHAR | `'EPSG:4326'` convention for any future geometry |

Caveats: Toronto permits and Brampton permits carry NULL `geography_sk`
(grid-ref / no ward in source). Brampton city-vs-regional ward equivalence
is UNCONFIRMED (conformance matrix §3) — any ward-level Brampton measure
publishes with that caveat.

### gold.dim_use_type — one row per conformed use (6 rows)

`RESIDENTIAL` / `MIXED_USE` / `INSTITUTIONAL` / `INFRASTRUCTURE` /
`OTHER` (non-residential scope) / `UNKNOWN` (no use signal in source).
`applies_to` is `'both'` (permits + applications). Raw values preserved on
facts (`use_type_raw`); crosswalk in `docs/conformance-matrix.md` §§1–2.
20,500 applications (all Toronto process-code rows) are `UNKNOWN` — tracked,
not hidden.

### gold.dim_status — one row per conformed status (15 rows)

Permit track (`APPLIED` → `UNDER_REVIEW` → `ISSUED` → terminal
`CLOSED`/`CANCELLED`/`EXPIRED`, plus `UNKNOWN`) and application track
(`SUBMITTED` → `UNDER_REVIEW` → terminal `APPROVED`/`REFUSED`/`WITHDRAWN`/
`CLOSED`, plus `APPEALED`, plus `UNKNOWN`). `status_stage_order` gives the
funnel order; `is_terminal` marks ends. Crosswalk in matrix §4.

### gold.fct_permits — ONE ROW PER BUILDING PERMIT (827,919 rows)

Collapse: Toronto per `PERMIT_NUM` (definitive beats Conditional, then max
revision); Mississauga per `BP_NO` (min OBJECTID); Brampton per
`PERMITNUMBER` (row carrying DWELLINGS wins, then min OBJECTID).
TOR 571,986 · BRAM 221,319 · MISS 34,614.

| Column | Type | Definition |
|---|---|---|
| `permit_sk` / `municipality_sk` / `permit_number` | BIGINT / BIGINT / VARCHAR | Key, owner, business key |
| `geography_sk` | BIGINT | Nullable (see dim_geography caveats) |
| `use_type_sk` / `use_type_raw` / `use_type_classification_method` | INTEGER / VARCHAR / VARCHAR | Conformed use + raw + method |
| `status_sk` / `status_raw` | INTEGER / VARCHAR | Conformed + raw status |
| `date_applied_sk` / `date_issued_sk` / `date_closed_sk` | BIGINT | Role-playing joins to dim_date; nullable per source coverage |
| `unit_count_net_new` | BIGINT | Toronto `created − lost` only when BOTH reported (else NULL); Mississauga `RES_UNITS`; Brampton `DWELLINGS`. Negatives are real demolition losses. Basis `'unknown'` |
| `unit_count_basis` | VARCHAR | Always `'unknown'` in v1 (ADR-0003) |
| `construction_value_cad` | DECIMAL(21,2) | Toronto + Mississauga only — Brampton feed has no value field (all NULL) |
| `floor_area_sqm` | DOUBLE | Where the source reports an area; NULL otherwise |
| `related_application_number` | VARCHAR | **NULL everywhere in v1** — no proven key (ADR-0006) |
| `ingest_batch_id` / `row_loaded_at` | VARCHAR / TIMESTAMPTZ | Lineage |

### gold.fct_applications — ONE ROW PER APPLICATION FILE (21,658 rows)

Collapse: Toronto per file number (address rows collapsed, count kept in
`silver.toronto_applications.address_count`); Mississauga cross-feed union
(site-plan + rezoning, `feeds_seen` kept); Brampton per `FILE_NUMBER`
(multi-polygon rows collapsed). TOR 8,601 · BRAM 11,630 · MISS 1,427.

| Column | Type | Definition |
|---|---|---|
| `application_sk` / `municipality_sk` / `application_number` | BIGINT / BIGINT / VARCHAR | Key, owner, business key (file number) |
| `geography_sk` | BIGINT | 55 rows NULL (unmatched ward codes — measured residual) |
| `use_type_sk` / `use_type_classification_method` | INTEGER / VARCHAR | Mostly `UNKNOWN` for Toronto/Brampton (no use signal) |
| `status_sk` / `status_raw` | INTEGER / VARCHAR | Conformed + raw status |
| `date_submitted_sk` / `date_decision_sk` | BIGINT | Decision date exists only for Mississauga in v1 |
| `unit_count_proposed` | BIGINT | Proposed units where reported; basis `'unknown'` |
| `unit_count_basis` | VARCHAR | Always `'unknown'` in v1 |
| `ingest_batch_id` / `row_loaded_at` | VARCHAR / TIMESTAMPTZ | Lineage |

## Measure library (all reconciled — see `docs/measure-reconciliation.json`)

| # | Measure | Business definition | Gold SQL (DuckDB) | DAX sketch (for Fabric) | Reconciled value 2026-09-10 |
|---|---|---|---|---|---|
| M1 | Permits issued | Permits with a `date_issued_sk`, by municipality × year | `COUNT(*)` on fct_permits joined to dim_date via `date_issued_sk` | `CALCULATE(COUNTROWS(fct_permits), NOT(ISBLANK(fct_permits[date_issued_sk])))` | TOR 571,986-file permits incl. 2025: 34,085; full year table in JSON |
| M2 | Net new units | `SUM(unit_count_net_new)`, NULLs excluded, basis tagged | `SUM(unit_count_net_new)` grouped by municipality | `CALCULATE(SUM(fct_permits[unit_count_net_new]))` + basis card | TOR 259,840 (371,394 null rows) · BRAM 78,957 (132,933 null) · MISS 30,968 (28,003 null) — NOT comparable across municipalities |
| M3 | Active applications | Applications whose status is not terminal | `COUNT(*)` where `dim_status.is_terminal = FALSE` | `CALCULATE(COUNTROWS(fct_applications), dim_status[is_terminal] = FALSE)` | TOR 1,694 (UNDER_REVIEW 1,339 + SUBMITTED 36 + APPEALED 319 — appeal is non-terminal) · BRAM 719 · MISS 255 |
| M4 | Permit status mix | Permits by conformed status | `COUNT(*)` grouped by `status_code` | stacked bar over dim_status | TOR CLOSED 346,694 / ISSUED 168,352 / CANCELLED 48,867; full mix in JSON |
| M5 | Application status mix | Applications by conformed status | `COUNT(*)` grouped by `status_code` | stacked bar over dim_status | BRAM APPROVED 5,704 / CLOSED 4,874; TOR CLOSED 6,090 / UNDER_REVIEW 1,339; full mix in JSON |
| M6 | Median applied→issued days | Median `date_issued − date_applied` over permits having both dates | `MEDIAN(d2.calendar_date − d1.calendar_date)` | `MEDIANX` over datediff, or precompute in SQL view | TOR 28d (n=460,121) · MISS 34d (n=34,581) · BRAM 44d (n=150,680) |
| M7 | Median submitted→decision days | Median `date_decision − date_submitted`; Mississauga only in v1 | same pattern on fct_applications | same | MISS 385d (n=1,163). TOR/BRAM: no decision dates — page states this |
| M8 | Construction value | `SUM(construction_value_cad)` | `SUM(construction_value_cad)` | `SUM(fct_permits[construction_value_cad])` | MISS $18.27B · TOR $100.99B · BRAM: no data (page shows two municipalities, labelled) |

Pending (defined, uncomputable — appear in the report as explicit empty states, never zeros):

| # | Measure | Blocked on | Owner |
|---|---|---|---|
| P1 | Units / permits per capita | `population_latest` NULL; StatCan series HTTP 406 | data-quality-auditor |
| P2 | Application→permit days | No proven key (ADR-0006) | transform-engineer |
| P3 | StatCan control-total reconciliation | StatCan series unpulled | ingestion-engineer |

## PL-300 mapping (CEO study aid)

- Prepare data → bronze/silver modelling, PII drops, unit-basis typing (this repo: `models/`, ADRs 0003–0007).
- Model data → star schema, relationships (fact → dims, many-to-one, single filter direction), dim_date marked as date table, SCD note on `application_status_history` (Type 2-ready, currently all-current).
- Visualize/analyze → measure library above + `docs/report-plan.md` (filter/drill intent per visual).
- Deploy/maintain → `docs/fabric-setup.md` refresh strategy + `scripts/reconcile_measures.py` as the post-refresh gate (re-run after every refresh; a drift fails the publish, not the dashboard).
