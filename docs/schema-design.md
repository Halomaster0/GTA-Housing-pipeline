# Star Schema Design — GTA Housing Pipeline

**Status: DRAFT — submitted for `director-data-engineering` review. Not yet approved. No SQL may be written against this design until it is.**
**Date: 2026-09-10**
**Designed against: UNVERIFIED sources.** Every one of the four municipal source families (Toronto CKAN, Mississauga ArcGIS, Brampton ArcGIS, Peel ArcGIS) plus StatCan and CMHC is recorded as `UNVERIFIED-BLOCKED` in `docs/sources/README.md` as of this date — the sandbox's network egress policy rejected every canonical host before any application response was returned (see `docs/sources/evidence/2026-09-10-verification.md`). Nothing in this document should be read as a claim about what any source actually contains. It is a hypothesis for `director-data-engineering` to review, and a target for `source-scout`/`ingestion-engineer` to confirm or falsify on the next network-enabled run.

This is the Phase 1 "draft the star schema on paper, before writing SQL" deliverable (`docs/build-plan.md` §6 Phase 1, Gate 1 criterion: "schema design reviewed by Director + ADR for any contested modelling decision"). It produces no `models/silver/*.sql` or `models/gold/*.sql` — those are Phase 2, gated on this document's approval per the `transform-engineer` role card's own process step 1.

Every source column name that appears below is a **hypothesis**, tagged `(ASSUMED)` on first use per subsection, meaning: not read from a live schema response, carried over from general knowledge of how municipal open-data portals of this type are commonly shaped, and to be treated as false until a live `package_show` / `?f=json` / `getCubeMetadata` call says otherwise. Gold and silver column names that are **our own invention** (the conformed vocabulary this design proposes) are not tagged, because we are defining them, not claiming to have observed them.

---

## Assumptions register — read this before anything else

Twenty-five assumptions. Each is written as a falsifiable question the first live source verification will answer. "If false" states the consequence for this design. Risk tier: **High** means the failure would change what a published metric *means*, not just which SQL statement produces it.

### A. Source existence and schema shape

| ID | Assumption | If false | Risk |
|---|---|---|---|
| A1 | Toronto's CKAN catalogue exposes "building permits" and "development applications" as two separably identifiable datasets, not one combined package. | Low structural effect — `source-scout` re-maps which package feeds which fact table; the two-fact-table design itself does not need to change. | Low |
| A2 | Toronto's building-permits dataset exposes a dwelling-unit count field at all, and if so, that its semantics (net-new / gross / project-level) can be determined from documentation or a data sample. | If no unit field exists, `fct_permits.unit_count_net_new` is `NULL` for every Toronto row and any "units approved" metric either excludes Toronto or is reported with an explicit per-municipality completeness flag — never silently treated as zero. | **High** |
| A3 | Mississauga's and Brampton's ArcGIS permit layers expose the same field set as each other (unit counts, use-type text, construction value). | If one has fields the other lacks, cross-municipality comparisons on that measure become asymmetric; the affected measure gets a `data_completeness` note per municipality rather than being computed silently for one and imputed for the other. | Medium |
| A4 | Brampton's permits dataset lacks unit counts before some cutoff year — the build plan's own illustrative example, not a confirmed finding. | If real, any pre-cutoff Brampton unit trend must render as "incomplete" rather than a real dip in construction. If the example is fictional, no gap needs modelling. | Medium |
| A5 | Peel Region publishes some open dataset relevant to this schema (regional boundaries, or a region-level applications set); if it publishes nothing at all, Peel remains a `dim_municipality` row for scope-completeness only. | Every permit/application fact for Peel Region is structurally absent. The dashboard must render this as "not applicable — upper-tier government, does not issue permits," never as "0 permits," which would misreport a structural fact as a data-quality problem. | **High** |
| A6 | None of the four sources publish a native status-change history or audit log; each publishes only a current-state snapshot on every extract. | If a source *does* publish real history (e.g. a status-log sub-table), that source should feed SCD2 directly instead of the bronze-snapshot-diff technique this design defaults to (§5), which is materially lower fidelity and left-truncated at pipeline launch. | **High** |
| A7 | At least some permit records carry an explicit cross-reference field to a prior development-application number. | If no source ever publishes this field, `fct_permits.related_application_number` is `NULL` for 100% of rows, the two fact tables are never joinable, and the golden eval question "how has Brampton's application-to-permit time changed" (build plan §5.13) must be answered with an explicit refusal or scoped down to "cannot be computed — no linking key published," not an inferred address/date-proximity join. | **High** |
| A8 | ArcGIS layers expose a stable per-record object ID / GlobalID independent of the business-facing permit/application number. | Lineage tracking (bronze row → silver row) falls back to the business number alone, which is acceptable but weaker for detecting a source-side record replacement versus a genuine business-key reuse. | Low |
| A9 | Permit/application business keys (`permit_number`, `application_number`) are stable and unique *within a municipality* across repeated extracts — the same real-world permit always republishes under the same key. | If keys are reused or reissued, both idempotent silver merge (dedup on business key) and the bronze-snapshot-diff SCD2 technique (A6) would misattribute an unrelated record's history to the wrong permit. This must be checked with a live sample before Phase 2 ingestion is trusted, not assumed. | **High** |

### B. Semantic / definitional (the R3 problem)

| ID | Assumption | If false | Risk |
|---|---|---|---|
| A10 | Toronto tracks Committee of Adjustment (minor variance) applications separately from Community Planning applications (rezoning, site plan, subdivision, OPA), as distinct systems with distinct numbering/status vocabularies. | If it is one combined system, the application-grain conformance decision (§6, row 1) simplifies for Toronto specifically; the general principle (application ≠ project) still likely holds for the other municipalities. | Medium |
| A11 | A single physical development project can appear as multiple, separately numbered application records within one municipality (e.g. an OPA, a rezoning, and a site-plan application for the same building, three file numbers). | If every municipality maintains one master project number spanning all stages, "count of applications" and "count of development projects" converge and ADR-1 (§6) becomes unnecessary — a genuinely good outcome, but not one to assume in advance. | Medium |
| A12 | Where a dwelling-unit field exists, it records **net new units created by that specific permit/application row** — not gross units in the resulting building, and not a project-level total repeated across every permit belonging to one project. | **This is the single highest-risk assumption in the whole design.** If units are gross, project-level, or duplicated across sibling permits, summing `unit_count_net_new` across permits **overstates** true unit production, silently, per municipality, in a way that would not show up as an error — the query still runs and returns a plausible number. This is the literal failure mode named in the `transform-engineer` mission brief ("a `fct_permits` table that sums cleanly and is wrong"). See §6 for the proposed mitigation (`unit_count_basis` flag, default `unknown`, never defaulted to `net-new`). | **High** |
| A13 | Permit status vocabularies differ in what an "issued" or "active" status actually denotes (paperwork issued vs. construction physically underway) across the three permit-issuing municipalities. | If the vocabularies turn out to align exactly, the status crosswalk in `dim_status` collapses to a simple rename (mechanical); if they diverge, individual value mappings need their own documented judgment call (semantic), not a blanket rename. | Medium |
| A14 | Development-application approval authority sits entirely with the lower-tier municipality (Toronto, Mississauga, Brampton); Peel Region (upper-tier) has no independent decision-making role, at most a circulated-comment role. Believed true under Ontario's two-tier Planning Act structure, not yet confirmed against Peel's actual published data. | If Peel Region *does* independently approve a class of regionally-significant applications, `fct_applications` needs a Peel-sourced feed after all, and `dim_municipality.is_permit_issuing_authority` (true for permits) is a separate flag from an application-approval-authority flag this design does not currently carry. | Medium |
| A15 | Building permits (Building Code Act process) do not universally require a preceding, trackable development application (Planning Act process) — the two regulatory tracks are genuinely independent for a meaningful share of records. | If in practice nearly every permit does trace to an application in the same dataset family, the two fact tables are more tightly coupled than this design treats them, and a stronger default join (still real-key-only, not inferred) might be justified. | **High** |

### C. Geography

| ID | Assumption | If false | Risk |
|---|---|---|---|
| A16 | Ward boundaries are published as real polygons (not just centroid points or ward names) by at least Toronto, Mississauga, and Brampton. | If a source publishes only a ward code/name with no geometry, `dim_geography` for that municipality degrades to a flat code lookup with no polygon-based census-tract linkage — `geometry_precision = 'unknown'` for every row from that source. | Medium |
| A17 | Permit/application records carry, or can be geocoded to, a specific point location (address or lat/long) rather than only a ward code. | If only ward-level location exists, census-tract linkage can only use the lossy plurality-overlap approximation described in §4, and `geography_precision = 'centroid-approximated'` for that source, which must be visible to anyone consuming a per-tract measure. | Medium |
| A18 | Raw geometries are published in EPSG:4326 (WGS84 lat/long), the common default for ArcGIS Hub and CKAN geospatial resources. | If a source instead publishes a different CRS (e.g. a provincial projected system), the reprojection step in §7 needs a source-specific transform, which is a mechanical fix, not a redesign. | Low |
| A19 | Each municipality's current ward-boundary vintage and its effective start date (e.g. Toronto's 25-ward map effective for the 2018 election) can be determined and is stable enough to seed `dim_geography`'s SCD2 `effective_start_date`. | If effective dates cannot be sourced reliably, ward-vintage rows still exist but with a best-effort `effective_start_date` flagged low-confidence, which weakens (but does not break) historical ward comparisons. | Medium |

### D. Date and fiscal calendar

| ID | Assumption | If false | Risk |
|---|---|---|---|
| A20 | All four municipalities' fiscal years align with the calendar year (January–December), consistent with Ontario's Municipal Act municipal budget cycle. Not independently verified against any of the four entities' actual financial statements this session. | If any municipality's *reported series* (not just its budget cycle) uses a non-calendar reference period, `dim_date.fiscal_year`/`fiscal_quarter` as designed (shared, muni-agnostic columns) is wrong for that municipality and fiscal attributes must move into a date × municipality bridge instead of living on a shared `dim_date` — an open question for the Director (§8). | Medium |
| A21 | Any adopted StatCan series' reference period can be mapped cleanly onto this project's calendar-year date grain. | If not, the reconciliation logic in the Data Quality Auditor's cross-source check needs its own explicit period-mapping rule, documented separately — not designed here because no StatCan product ID is confirmed yet. | Low |

### E. Units, currency, CRS mechanics

| ID | Assumption | If false | Risk |
|---|---|---|---|
| A22 | Where floor area is published, sources are inconsistent with each other in units (sq ft vs. sq m). | If all four sources turn out to use the same unit, the conversion step in §7 is a no-op for three of them — harmless to have designed for the general case. | Low |
| A23 | All monetary construction-value fields are denominated in CAD with no foreign-currency records. | Near-certain for Canadian municipal permit data; if false, a currency column and FX handling would need to be added — not currently designed. | Low |
| A24 | Date-only fields (applied/issued/decision dates) are published as bare calendar dates with no time-of-day or timezone marker. | If a source instead publishes a full timestamp for one of these fields, that specific field needs `TIMESTAMPTZ`/UTC treatment (§7) instead of the bare-date treatment — a per-field, not per-design, fix. | Medium |

### F. Licensing

| ID | Assumption | If false | Risk |
|---|---|---|---|
| A25 | Every adopted source's licence, once actually read, permits the public, redistributive use this project requires (public dashboard, public repo, MIT-licensed code operating on the data). Currently unconfirmed for all four municipal sources and both national sources per `docs/sources/*.md`. | A source found to be licence-incompatible must be **dropped from the star schema entirely** — not just delayed — which could remove one full municipality from every fact table it feeds, not merely one column. This is a `security-and-licence-reviewer` blocking condition, not a `transform-engineer` judgment call, but it changes this schema's actual coverage if triggered. | **High** |

**The single assumption whose failure would most damage this design is A12** (dwelling-unit semantics: net-new vs. gross vs. project-level). It is the only assumption that could make every headline metric in the project — "units approved," "who is actually building," the per-capita municipal-comparison page the analytics-engineering framing leans on hardest — sum to a number that is internally consistent, looks correct, and is wrong. Sections 2 and 6 build in an explicit `unit_count_basis` flag defaulting to `unknown` specifically so this failure mode cannot hide inside a clean-looking `SUM()`.

---

## 1. Grain statements

One sentence each. This is the section a review should not proceed past disagreement on.

| Table | Grain |
|---|---|
| `fct_permits` | One row per building permit, uniquely identified within a municipality by its permit number. Not one row per status change (permits are not SCD2 in this design — see §5) and not one row per unit or work-type line item (unit-level and work-type-level detail, where a source publishes it, lives in a supporting silver bridge and is summed up to permit grain — see §2.1 and §6). |
| `fct_applications` | One row per development application, uniquely identified within a municipality by its application/file number, as an **accumulating snapshot**: current status plus the key lifecycle milestone dates known as of the latest pipeline run. It is explicitly **not** one row per development project (§6, row 1) and **not** one row per status change (full status history lives in the supporting silver SCD2 entity `silver.application_status_history`, §5). |
| `dim_municipality` | One row per municipality participating in this project's scope (four rows: Toronto, Mississauga, Brampton, Peel Region). Not versioned — municipal identity itself is treated as static across the project's timeframe, unlike ward boundaries within a municipality. |
| `dim_date` | One row per calendar date, 2010-01-01 through 2028-12-31 (today is 2026-09-10; "two years forward" is computed from the current year, not hardcoded, and this table needs a documented periodic extension as calendar years pass — an operational note for `cicd-engineer`, not a schema change). |
| `dim_geography` | One row per **version of a ward boundary** — i.e. one row per (municipality, ward source code, effective date range) combination. This is deliberately **not** "one row per ward" because a ward code is not a stable identifier across redistricting (§4); the grain is the ward-as-drawn-for-a-period, not the ward-as-a-name. |
| `dim_use_type` | One row per conformed use-type code in a small, hand-curated vocabulary (aligned with the taxonomy `rag-architect` already commits to in `docs/build-plan.md` §5.11: residential / mixed-use / institutional / infrastructure / other, plus `unknown`). Not one row per raw source category string — those map many-to-one into this table via a crosswalk documented in `docs/conformance-matrix.md`, not stored as rows here. |
| `dim_status` | One row per conformed status code in a small, hand-curated vocabulary, covering **both** permit-status and application-status domains (distinguished by an `applies_to` column), because the build plan names exactly one `dim_status` table, not two, and permit and application status vocabularies are genuinely different domains that must not be silently merged into one flat list without that distinction. |

---

## 2. The seven gold tables

Conventions used throughout: surrogate keys are `_sk` suffixed, generated integers; natural/business keys from source systems are retained as plain (non-`_sk`) degenerate columns for traceability and are never assumed globally unique — only unique within `municipality_sk`. All foreign keys reference a surrogate key. Any field name written with a trailing "(ASSUMED)" is a hypothesis about source shape, not a confirmed field.

### 2.1 `fct_permits`

**Grain:** one row per building permit. **Fed by:** silver entity `silver.permits`, itself fed by Toronto's building-permits CKAN dataset(s) (ASSUMED to exist as such, A1) and Mississauga's and Brampton's ArcGIS building-permits layers (ASSUMED to exist, A3). **Peel Region does not feed this table** — Peel is the upper-tier government and is not expected to be a permit-issuing authority (A5, A14); its absence here is a structural fact to surface in the dashboard, not a data gap to explain away.

| Column | Type | Notes |
|---|---|---|
| `permit_sk` | BIGINT | Surrogate PK. |
| `municipality_sk` | BIGINT | FK → `dim_municipality`. |
| `permit_number` | VARCHAR | Degenerate dimension — the source's business key. Unique within `municipality_sk` only (A9). |
| `geography_sk` | BIGINT | FK → `dim_geography`, resolved to the ward-vintage row in effect on `date_issued` (or `date_applied` if not yet issued) — see §4. |
| `use_type_sk` | BIGINT | FK → `dim_use_type`. |
| `use_type_raw` | VARCHAR | Degenerate — lossless copy of the source's raw work-type/building-type string (ASSUMED field name, e.g. `permit_type` or `work_type`). |
| `use_type_classification_method` | VARCHAR | `'source-field-mapped'` \| `'zero-shot-classified'` \| `'unknown'` — records whether this row's `use_type_sk` came from a direct crosswalk or from the Phase 4 zero-shot fallback (`rag-architect`'s classifier, cached not called at query time per its role card). |
| `status_sk` | BIGINT | FK → `dim_status` (`applies_to = 'permit'`). Latest known status as of the most recent load — see §5 for why this is not versioned. |
| `status_raw` | VARCHAR | Degenerate — lossless copy of the source's raw status string. |
| `date_applied_sk` | INTEGER | FK → `dim_date`, role-playing as "applied." |
| `date_issued_sk` | INTEGER | FK → `dim_date`, nullable, role-playing as "issued." NULL until issuance. |
| `date_closed_sk` | INTEGER | FK → `dim_date`, nullable, role-playing as "closed" (conforms whatever source-specific term applies — "finaled," "completed," "closed" — see §6; mechanical rename once the real field is seen). |
| `unit_count_net_new` | INTEGER | Nullable. **NULL means "not reported," never coerced to 0.** Canonical measure — see A12 and §6. |
| `unit_count_basis` | VARCHAR | `'net-new'` \| `'gross'` \| `'project-level'` \| `'unknown'`. Defaults to `'unknown'` until a source's true semantics are confirmed; never defaults to `'net-new'`. |
| `construction_value_cad` | DECIMAL(14,2) | Nullable. Currency assumed CAD (A23). |
| `floor_area_sqm` | DECIMAL(12,2) | Nullable. Canonical unit — see §7. |
| `floor_area_raw_value` / `floor_area_raw_unit` | DECIMAL / VARCHAR | Traceability pair for the conversion in `floor_area_sqm`. |
| `related_application_number` | VARCHAR | Nullable. Populated **only** if the source publishes an explicit cross-reference (A7) — never inferred from address or date proximity. |
| `source_record_id` | VARCHAR | Source's own row identifier if distinct from `permit_number` (e.g. an ArcGIS `OBJECTID`/`GlobalID`, A8). |
| `ingest_batch_id` | VARCHAR | Pipeline lineage — the bronze ingest run that produced the current state of this row. Not a role-playing business date. |
| `row_loaded_at` | TIMESTAMPTZ | ETL metadata, stored UTC. |

### 2.2 `fct_applications`

**Grain:** one row per development application (accumulating snapshot). **Fed by:** silver entity `silver.applications`, which is itself derived from the current-row view of `silver.application_status_history` (the SCD2 entity, §5) plus milestone dates. Source families: Toronto's development-applications CKAN dataset(s) (ASSUMED possibly split into Community Planning vs. Committee of Adjustment per A10) and Mississauga's/Brampton's ArcGIS development-applications layers. **Peel Region's role here is unresolved** (A14) — treated as a non-contributor for v1 unless verification finds a genuine Peel-authored applications dataset with real decision authority.

| Column | Type | Notes |
|---|---|---|
| `application_sk` | BIGINT | Surrogate PK. |
| `municipality_sk` | BIGINT | FK → `dim_municipality`. |
| `application_number` | VARCHAR | Degenerate business key. Unique within `municipality_sk` only. See §6 row 1 — this is an administrative file number, **not** a development-project identifier (A11). |
| `application_type_raw` | VARCHAR | Degenerate (ASSUMED categories such as "Rezoning," "Site Plan," "Minor Variance," "OPA," "Subdivision" — not confirmed to exist as named). |
| `geography_sk` | BIGINT | FK → `dim_geography`, resolved to the ward-vintage in effect on `date_submitted`. |
| `use_type_sk` | BIGINT | FK → `dim_use_type`. |
| `use_type_classification_method` | VARCHAR | Same domain as `fct_permits`. |
| `current_status_sk` | BIGINT | FK → `dim_status` (`applies_to = 'application'`). |
| `status_raw` | VARCHAR | Degenerate. |
| `date_submitted_sk` | INTEGER | FK → `dim_date`, role-playing as "submitted." |
| `date_deemed_complete_sk` | INTEGER | FK → `dim_date`, nullable, role-playing as "deemed complete" — may not exist as a source concept (unconfirmed). |
| `date_decision_sk` | INTEGER | FK → `dim_date`, nullable, role-playing as "decided" (approval or refusal). |
| `date_appeal_filed_sk` | INTEGER | FK → `dim_date`, nullable, role-playing as "appeal filed," if the source tracks appeals (e.g. to the Ontario Land Tribunal) at all. |
| `unit_count_proposed` | INTEGER | Nullable. **Deliberately a separate measure from `fct_permits.unit_count_net_new`** — a proposed unit count in an application can change through revisions and may never match what is ultimately permitted or built. These two numbers must never be summed together or treated as comparable without saying so. |
| `unit_count_basis` | VARCHAR | Same domain as `fct_permits`. |
| `source_record_id`, `ingest_batch_id`, `row_loaded_at` | — | Same as `fct_permits`. |

**Note on the permit ↔ application relationship:** the cross-reference is stored exactly once, on `fct_permits.related_application_number`, pointing outward to `fct_applications.application_number`. `fct_applications` does not carry a reverse array of related permits — a single source of truth for the relationship, queried by joining outward from whichever side is needed, avoiding two copies of the same fact drifting out of sync.

### 2.3 `dim_municipality`

**Grain:** one row per municipality in project scope. **Fed by:** a hand-curated seed (four rows), not a live source — this is metadata about the project's own scope, not something any API returns. Optionally enriched with StatCan population once a real product ID is confirmed (currently none is, per `docs/sources/statcan.md`).

| Column | Type | Notes |
|---|---|---|
| `municipality_sk` | BIGINT | Surrogate PK. |
| `municipality_code` | VARCHAR | Our own short code (`TOR`, `MISS`, `BRAM`, `PEEL`) — invented by this project, not a source-provided code. |
| `municipality_name` | VARCHAR | `Toronto`, `Mississauga`, `Brampton`, `Peel Region`. |
| `municipality_tier` | VARCHAR | `'single-tier'` (Toronto), `'lower-tier'` (Mississauga, Brampton), `'upper-tier'` (Peel Region). Ontario's two-tier municipal structure, general knowledge, not independently reconfirmed this session. |
| `parent_region_sk` | BIGINT | Nullable, self-referencing FK. Mississauga/Brampton point to the Peel Region row; Toronto and Peel Region itself are NULL. |
| `is_permit_issuing_authority` | BOOLEAN | TRUE for Toronto/Mississauga/Brampton, FALSE for Peel Region (A5, A14) — exists specifically so a dashboard never renders Peel's structural absence as a "0 permits" finding. |
| `population_latest` | BIGINT | Nullable, populated only once a StatCan product is confirmed. |
| `population_reference_year` | SMALLINT | Nullable, paired with the above. |
| `population_source` | VARCHAR | Nullable (e.g. `'2021 Census'` once confirmed) — never fabricated in the interim. |

### 2.4 `dim_date`

**Grain:** one row per calendar date, 2010-01-01 through 2028-12-31. **Fed by:** generated programmatically (a DuckDB date spine), not sourced from any of the blocked APIs — the one gold table fully buildable today, independent of source verification. See §3 for the full column list and the fiscal-year caveat (A20).

### 2.5 `dim_geography`

**Grain:** one row per ward-boundary version (municipality × ward source code × effective date range). **Fed by:** silver ward-boundary entities, themselves fed by Toronto's ward-boundary CKAN dataset (ASSUMED to exist, per `config/sources.yml`'s `toronto-wards` entry) and Mississauga's/Brampton's ArcGIS ward-boundary layers (existence unconfirmed, A16), cross-referenced with StatCan census-tract boundary files (unconfirmed, no product ID recorded). See §4 for the full design, including census-tract linkage and the redistricting problem.

### 2.6 `dim_use_type`

**Grain:** one row per conformed use-type code. **Fed by:** not a live source — a hand-curated vocabulary, deliberately aligned with the taxonomy the AI track already commits to (`docs/build-plan.md` §5.11: residential / mixed-use / institutional / infrastructure / other). The many-to-one crosswalk from each source's raw category field into this vocabulary is documented in `docs/conformance-matrix.md`, populated once real category values are observed.

| Column | Type | Notes |
|---|---|---|
| `use_type_sk` | BIGINT | Surrogate PK. |
| `use_type_code` | VARCHAR | `RESIDENTIAL`, `MIXED_USE`, `INSTITUTIONAL`, `INFRASTRUCTURE`, `OTHER`, `UNKNOWN`. |
| `use_type_label` | VARCHAR | Display label. |
| `applies_to` | VARCHAR | `'permit'` \| `'application'` \| `'both'` — permit "work type" and application "application type" are different raw vocabularies (ASSUMED) and may not conform identically. |

### 2.7 `dim_status`

**Grain:** one row per conformed status code, covering both the permit-status and application-status domains. **Fed by:** not a live source — hand-curated, with a many-to-one crosswalk from each source's raw status field documented in `docs/conformance-matrix.md` once real values are observed.

| Column | Type | Notes |
|---|---|---|
| `status_sk` | BIGINT | Surrogate PK. |
| `status_code` | VARCHAR | Permit domain (example, not yet confirmed against any real vocabulary): `APPLIED`, `UNDER_REVIEW`, `ISSUED`, `CLOSED`, `CANCELLED`, `EXPIRED`, `UNKNOWN`. Application domain: `SUBMITTED`, `UNDER_REVIEW`, `APPROVED`, `REFUSED`, `APPEALED`, `WITHDRAWN`, `CLOSED`, `UNKNOWN`. |
| `status_label` | VARCHAR | Display label. |
| `applies_to` | VARCHAR | `'permit'` \| `'application'` — kept as one physical table per the build plan's naming (exactly one `dim_status`), distinguished by this column rather than silently merging two different vocabularies into one flat list. |
| `status_stage_order` | SMALLINT | Nullable ordering hint within its `applies_to` domain, for the Pipeline Velocity report page. |
| `is_terminal` | BOOLEAN | Whether this status represents an end state (used for "active applications" counts). |

### Role-playing `dim_date`

`dim_date` is joined more than once from each fact table, using the standard technique of one FK column per role rather than one shared "date" column:

- `fct_permits`: `date_applied_sk`, `date_issued_sk`, `date_closed_sk` — three independent joins to `dim_date`.
- `fct_applications`: `date_submitted_sk`, `date_deemed_complete_sk`, `date_decision_sk`, `date_appeal_filed_sk` — up to four independent joins.

Each FK is resolved against `dim_date.date_sk` on that specific event's calendar date; a permit that has not yet been issued simply has a NULL `date_issued_sk`, not a join to a placeholder row.

---

## 3. `dim_date`

Covers 2010-01-01 through two years past the current year, computed relative to the build date rather than hardcoded — as of this document's date (2026-09-10) that is 2028-12-31. This needs a documented periodic re-extension as years pass; it is an operational task, not a schema change, and is flagged for `cicd-engineer` to schedule rather than left implicit.

**Primary key:** `date_sk` — an `INTEGER` in `YYYYMMDD` form (e.g. `20260910`), the standard Kimball convention: human-readable, sortable, and range-filterable without a join.

| Column | Type | Notes |
|---|---|---|
| `date_sk` | INTEGER | PK, `YYYYMMDD`. |
| `calendar_date` | DATE | Unique, not null. |
| `year` | SMALLINT | |
| `quarter` | TINYINT | 1–4. |
| `month` | TINYINT | 1–12. |
| `month_name` | VARCHAR | |
| `month_short_name` | VARCHAR | |
| `day_of_month` | TINYINT | |
| `day_of_week_iso` | TINYINT | 1=Monday…7=Sunday. |
| `day_name` | VARCHAR | |
| `is_weekend` | BOOLEAN | |
| `week_of_year_iso` | TINYINT | |
| `iso_year` | SMALLINT | Distinct from `year` at ISO week boundaries around New Year. |
| `day_of_year` | SMALLINT | |
| `fiscal_year` | SMALLINT | **Assumed equal to `year`** (A20) — Ontario municipal budgeting is understood to run calendar-year, but this is not independently confirmed against any of the four entities' financial statements, and StatCan series adopted later may carry a different reference period. |
| `fiscal_quarter` | TINYINT | Assumed equal to `quarter`, same caveat. |
| `fiscal_month` | TINYINT | Assumed equal to `month`, same caveat. |

**Open design risk, stated plainly (A20):** these fiscal columns live directly on the shared `dim_date` table, which implicitly assumes one fiscal calendar for every municipality and every source. If verification finds that any municipality's *reported series* (not its budget cycle — its actual published data cadence) uses a non-calendar period, fiscal attributes cannot correctly stay on a municipality-agnostic `dim_date` and must move into a `date × municipality` bridge instead. This is not built now because there is no confirmed need for it yet — see §8.

---

## 4. `dim_geography`

**CRS:** raw geometries are assumed published in EPSG:4326 (WGS84 lat/long) — the common default for ArcGIS Hub and CKAN geospatial resources (A18, unconfirmed for any of the four sources specifically). Any area, centroid, or distance calculation reprojects to EPSG:26917 (NAD83 / UTM Zone 17N), the standard projected CRS for the GTA, because EPSG:4326 is angular and area/distance math on it is wrong without projection. Storage and any map-facing output (Power BI map visuals, a future web map) stays in EPSG:4326 for compatibility with standard web-mapping tooling. `dim_geography` carries a constant `geometry_crs` column recording the storage CRS directly in the data, not only in this document, so a stranger querying the table without reading documentation still sees it.

**The redistricting problem, addressed directly:** a ward code or number is not a stable identifier over time. Toronto's ward map changed from 44 to 25 wards effective for the 2018 municipal election (general knowledge, not reconfirmed this session, A19); Mississauga and Brampton have had their own boundary revisions on their own schedules. A ward numbered "5" before and after a redistricting event can refer to two materially different areas. **The consequence of ignoring this is silent corruption of any multi-year, by-ward comparison** — exactly the failure mode this design exists to prevent.

The proposed handling: `dim_geography` is versioned. Its grain is not "one row per ward" but **one row per ward-boundary-as-drawn-for-a-period**:

| Column | Type | Notes |
|---|---|---|
| `geography_sk` | BIGINT | Surrogate PK. |
| `municipality_sk` | BIGINT | FK → `dim_municipality`. |
| `ward_source_code` | VARCHAR | The source's own ward identifier for this vintage. **Never assumed unique on its own** — see below. |
| `ward_name` | VARCHAR | Nullable. |
| `ward_boundary_vintage_year` | SMALLINT | Year this boundary set took effect (A19). |
| `effective_start_date` | DATE | When this version becomes the correct attribution target for a fact. |
| `effective_end_date` | DATE | Nullable; NULL = current version. |
| `is_current` | BOOLEAN | |
| `census_tract_id` | VARCHAR | Nullable. See allocation method below. |
| `census_tract_allocation_method` | VARCHAR | `'point-in-polygon-per-record'` (preferred, requires A17) \| `'plurality-overlap-v1'` (fallback, ward-level approximation) \| `'unresolved'`. |
| `geometry_precision` | VARCHAR | `'exact-boundary'` \| `'centroid-approximated'` \| `'unknown'` — whether the underlying source geometry is a real polygon or only a point (A16). |
| `geometry_crs` | VARCHAR | Constant, `'EPSG:4326'` (storage). |
| `source_dataset_vintage` | VARCHAR | Traceability — which raw ward-boundary publication this row came from. |

**Natural key for uniqueness:** `(municipality_sk, ward_source_code, effective_start_date)` — never `(municipality_sk, ward_source_code)` alone, precisely because the code can be reused across a redistricting event with a different meaning.

**Fact-side resolution:** `fct_permits.geography_sk` and `fct_applications.geography_sk` are resolved to whichever `dim_geography` row was in effect on that fact's relevant date (issued date for permits, submitted date for applications) — not the current ward map. A 2015 Toronto permit in old-Ward-5 links to the pre-2018 boundary row, so a "permits in Ward 5" query does not silently blend two different geographic areas depending on the year filtered.

**Census tract linkage — a known simplification, stated rather than hidden:** wards (municipal political boundaries) and census tracts (StatCan statistical geography) are two independent systems that do not nest. The correct approach is to resolve census tract per fact record from its own point location, independent of ward (A17). Where a fact record has no point location — only a ward attribution — this design falls back to a "plurality overlap" approximation: the tract that covers the largest share of a given ward's area is assigned as *the* tract for that ward-boundary version, flagged with `census_tract_allocation_method = 'plurality-overlap-v1'`. This is lossy for wards that straddle multiple tracts and is proposed here as a v1 simplification given the project's timeline, not as a correct general solution — see §8 for the question this raises for the Director.

---

## 5. Slowly changing dimensions

**Where SCD Type 2 applies: development application status.** This matches the build plan's explicit scope (`transform-engineer`'s "Owns": *"SCD Type 2 logic on application status, where supported"*) and is not extended to permit status in this design (see below).

**Where it almost certainly is not natively supported by the source, and how this design compensates:** no source is confirmed (A6) to publish a genuine status-change audit log — a field that records *when* a status changed, as opposed to only the current status at extract time. This design assumes the worst case (A6 false) and builds SCD2 by **diffing successive full bronze snapshots**, not by trusting a native history field that may not exist:

- Supporting silver entity `silver.application_status_history` — **grain: one row per (municipality, application_number, status_value) contiguous validity period**, reconstructed by comparing an application's `status_raw` value across consecutive bronze partitions (partitioned by `ingest_date`, per the architecture's bronze-immutability rule).
- Columns: `municipality_sk`, `application_number`, `status_raw`, `status_sk`, `effective_start_date` (the `ingest_date` on which this status was *first observed*), `effective_end_date` (the `ingest_date` immediately before the status was next observed to differ, NULL if still current), `is_current`, and a constant `detection_method = 'bronze-snapshot-diff'` recording plainly that this is reconstructed, not sourced from a true change log.
- **Explicit consequence, stated per the process's own instruction:** granularity is capped at "however often the pipeline ingests" (weekly, per the build plan's stated cadence). A status change that occurs and reverts between two scheduled ingests is invisible. The *true* real-world change date is unknown — only "detected as different between ingest run A and ingest run B" is known. History is also **left-truncated at pipeline launch**: nothing about an application's status before this project started ingesting can be recovered unless a source turns out to publish real history after all (A6).
- `fct_applications.current_status_sk` is populated from the current row of this table (`is_current = TRUE`); anyone needing "what was the status of application X on date Y" queries `silver.application_status_history` directly, not the gold fact table, because the gold `fct_applications` grain (§1) does not carry history.

**Where it does not apply: permit status.** This design does **not** apply SCD2 to permits. Stated plainly: **the consequence is that this model cannot answer "what was the status of permit X on date Y" for any date other than the most recent load** — only the milestone dates (`date_applied`, `date_issued`, `date_closed`), which are treated as immutable once populated, are recoverable historically. This is a deliberate scope decision under the build plan's explicit SCD2 mandate ("on application status," not permit status), not an oversight, and is called out here so it is not mistaken for one. If the Director judges permit status history equally necessary (e.g. because a "time in review" metric turns out to need it), the same bronze-snapshot-diff technique could be extended to permits in Phase 2 — flagged as an open question in §8, not built now.

**`dim_geography` is also versioned (§4), but this is not conventional SCD2** — it versions the *dimension's own definition* (ward boundaries) against calendar time, using the same effective-dated-row technique, rather than tracking changes to an attribute of a stable business entity. Worth noting because it is easy to conflate the two: application-status SCD2 tracks *the same application* changing state; `dim_geography` versioning tracks *the geography itself* being redrawn.

---

## 6. The conformance problem

Toronto, Mississauga, Brampton, and Peel are assumed (not yet confirmed for any) to define "development application," "dwelling unit," and "status" in ways that do not automatically align. This section lays out the likely differences, proposes a conformed definition for each, classifies the decision per the ADR-0002 threshold, and states where a difference is irreconcilable rather than papering over it.

**ADR-0002's test, applied throughout:** *would a BI consumer reading the measure definition get a different answer because of this choice?* If yes, it is semantic and needs an ADR before dependent SQL merges. If it is a rename, a cast, or a unit conversion with one obviously correct answer, it is mechanical — a SQL comment plus a `docs/conformance-matrix.md` row is sufficient.

| # | Concept | Toronto (ASSUMED) | Mississauga (ASSUMED) | Brampton (ASSUMED) | Peel Region (ASSUMED) | Likely definitional difference | Proposed conformed definition | Classification |
|---|---|---|---|---|---|---|---|---|
| 1 | Development application (grain) | Possibly splits Community Planning applications from Committee of Adjustment applications into separate systems/numbering (A10) | Single development-applications layer covering site plan/rezoning/minor variance (unconfirmed) | Same pattern as Mississauga (unconfirmed) | Likely not an approving authority at all (A14) | A single physical project may surface as multiple, separately numbered application records within one municipality's own system (A11) — "one application" is an administrative-file concept, not a development-project concept. | `fct_applications` grain is fixed at "one row per municipally-assigned application/file number," explicitly not reconciled to "one row per development project." Project-level rollups are out of scope for v1 pending a confirmed cross-linking key. | **Semantic** — changes what "count of applications" means. **ADR required.** |
| 2 | Dwelling unit | Possibly reports net-new units, gross units, or a project-level total on a `unit_count`-shaped field (A2, A12) | Possibly reports `number_of_units` inconsistently populated for non-residential permits (A3, A12) | Possibly lacks unit counts before some year (A4); same semantic ambiguity as Mississauga (A12) | N/A (not a permit source) | "Dwelling unit" could mean net-new units created by this permit, gross units in the resulting building, or a project-level total duplicated across every permit belonging to one project — these produce different, non-comparable sums. | Canonical measure `unit_count_net_new`, always paired with `unit_count_basis` (`net-new`/`gross`/`project-level`/`unknown`), defaulting to `unknown` — **never defaulted to net-new** — until each source's real semantics are confirmed from a live schema or documentation. | **Semantic** — this is the flagship risk (A12) and the literal example in the `transform-engineer` mission brief. **ADR required**, likely one per source once real field semantics diverge, rather than one blanket ADR (see §8). |
| 3 | Status | Possibly a larger vocabulary (~10–15 codes) distinguishing paperwork stages from construction stages (A13) | Possibly a smaller enumerated ArcGIS domain (e.g. Issued / In Progress / Cancelled) (A13) | Same pattern as Mississauga (unconfirmed) | N/A for permits; application-status vocabulary for any Peel-authored applications unconfirmed | An "issued" permit status may mean "paperwork issued" in one system and be conflated with "construction underway" in another; application "approved" may mean delegated staff approval in one municipality and committee/council approval in another. | `dim_status`, split by `applies_to` (permit/application), with a small conformed vocabulary per domain and every raw source value's mapping recorded in `docs/conformance-matrix.md`, `status_raw` retained losslessly on the fact row. | **Mixed.** The mechanical act of building the crosswalk (a rename with a clear target) is mechanical once the source vocabulary is read. Any individual raw value whose real-world meaning is ambiguous (e.g. what "Issued" actually denotes) is semantic and gets its own documented decision, not folded silently into the general rename. |
| 4 | Permit ↔ application linkage | Building Code permits are not universally expected to require a preceding tracked Planning Act application (A15) — believed structurally independent processes for a meaningful share of records | Same expectation | Same expectation | N/A | A permit can exist with no corresponding application in the dataset (as-of-right construction needing no planning approval), and an approved application can exist with no resulting permit within the observation window (project stalls or is sold). The two fact tables are related-but-independent, not parent-child. | Cross-reference stored only where a source explicitly publishes one (`fct_permits.related_application_number`, A7) — never inferred by matching address or date proximity, which would produce a plausible-looking but unvalidated join. Metrics requiring this link (e.g. "application-to-permit time," a named golden eval question) are computed **only** over the subset with a real linking key, with the excluded share reported, not silently dropped. | **Semantic** — a golden eval question's correctness depends directly on this. **ADR required.** |
| 5 | Municipality participation / comparability | Full participant in `fct_permits` and `fct_applications` | Full participant | Full participant | Structurally not a permit-issuing authority (A5, A14); application-approval role unconfirmed | A naive "permits issued by municipality, including Peel Region" chart would render Peel's structural absence as if it were a finding ("Peel: 0 permits") rather than an artifact of Ontario's two-tier government structure. | `dim_municipality.is_permit_issuing_authority` flag; any per-municipality chart or measure filters or annotates on this flag rather than presenting a structural zero as a comparable data point. | **Semantic** — changes what "the four GTA municipalities compared" means in every dashboard page and the README framing. **ADR required.** |

**Expected ADRs for Phase 2** (per the classifications above): (1) application grain is the administrative file, not the project; (2) dwelling-unit canonical measure and basis handling — granularity of this ADR (one blanket ADR vs. one per source) is itself an open question for the Director, §8; (3) any individually ambiguous status-value mapping, written once real vocabularies are read, not preemptively; (4) permit-to-application linkage is real-key-only, never inferred; (5) Peel Region's non-permit-issuing status and its effect on cross-municipality comparison framing. A sixth candidate — versioning `dim_geography` for ward redistricting (§4) — is treated here as a mechanical design pattern (effective-dated rows) rather than a contested semantic call, but if the Director judges that a by-ward year-over-year comparison changes meaning enough to warrant its own record, it should be added to this list rather than assumed settled by this document alone.

**Where a difference may be genuinely irreconcilable:** if verification finds that dwelling-unit semantics differ across sources in a way that cannot be normalized even with the `unit_count_basis` flag (for example, a source that reports unit counts only at a multi-permit project level with no way to attribute a share back to an individual permit), the honest outcome is **not** to force a number into `unit_count_net_new` — it is to leave the field NULL for that source, set `unit_count_basis = 'unknown'` or a new explicit value describing the irreconcilable case, and let any aggregate measure that depends on it carry a `comparability_caveat` note (a per-municipality flag surfaced in the semantic model / dashboard) rather than silently averaging incompatible definitions into one clean-looking bar chart.

---

## 7. Timezone, units, currency

**Timestamps.** All stored timestamps are UTC (`TIMESTAMPTZ`), displayed in America/Toronto at the presentation layer (Power BI, the web app) — per `director-data-engineering`'s standing review checklist.

**Bare dates (the likely common case, A24).** Permit and application milestone dates (applied, issued, submitted, decision, etc.) are assumed to arrive as bare calendar dates with no time-of-day or timezone marker — the typical shape for a municipal CSV/ArcGIS export. These are handled as **local calendar dates, not as UTC-midnight timestamps to be localized**: a bare date like `2023-03-12` maps directly to `dim_date.calendar_date` (a `DATE`, not a `TIMESTAMP`) via its surrogate key, with no timezone conversion applied at all. This deliberately avoids a real and easy-to-introduce bug: naively parsing a bare date as UTC midnight and then converting to America/Toronto for display can shift the displayed date by one calendar day depending on the time of year (DST boundary) and the library used. Any field that *does* arrive as a genuine timestamp (e.g. a system-generated last-modified field) gets the full `TIMESTAMPTZ`/UTC treatment instead — the two are not to be confused, and if a field's true shape turns out to differ from this assumption once observed, it is reclassified per-field, not by revisiting this whole design.

**Area units.** Floor area, where published, is conformed to square metres (SI, Canada's official standard) as the canonical unit, with `_raw_value`/`_raw_unit` pairs retained for traceability. The conversion factor (1 sq ft = 0.092903 m²) is fixed and uncontested once the source's actual unit is confirmed (A22) — this is mechanical, not semantic, and needs only a SQL comment and a matrix row, not an ADR.

**Currency.** All monetary fields (construction value) are assumed CAD (A23) — no FX conversion is designed, on the reasoning that a foreign-currency field on a Canadian municipal permit record would be a genuine surprise, not merely unconfirmed. If wrong, this is a straightforward addition, not a redesign.

**CRS.** See §4 — storage in EPSG:4326, projected math in EPSG:26917, documented per-row via a constant `geometry_crs` column, not only in this prose.

---

## 8. Open questions for the Director

**Must be ruled on now, before Phase 2 SQL is written:**

1. **ADR granularity for the dwelling-unit conformance decision (§6 row 2).** Should there be one umbrella ADR covering the `unit_count_basis` mechanism generally, with per-source appendices added as each source's real semantics are confirmed — or a separate ADR per source the moment its semantics are found to diverge from the others? This affects how `docs/decisions/` reads to an outside reviewer and should be settled once, not re-litigated per source.
2. **Peel Region's place in the model (§2.3, §6 row 5).** Confirm the `is_permit_issuing_authority` flag design is sufficient, or rule that Peel Region should be represented purely as a `dim_geography`/reference contributor and excluded from `dim_municipality` comparisons entirely — a framing decision with direct README and dashboard consequences, since the charter's "four incompatible municipal portals" framing currently implies four comparable peers.
3. **Permit-application linkage policy (§6 row 4).** Confirm real-key-only (this design's default) versus permitting a clearly labeled, opt-in heuristic join (address + date proximity, with a documented false-match rate) specifically to make the named golden eval question ("how has Brampton's application-to-permit time changed") answerable if no real source-published key exists. This design's default is to let that question be refused rather than answered on an unvalidated join — the Director may weigh this differently given the eval harness's refusal-accuracy metric.
4. **Census-tract allocation method for v1 (§4).** Confirm the plurality-overlap ward-to-tract approximation is acceptable simplification for the project's timeline, or that per-record point-in-polygon geocoding (more correct, more engineering) is required before any per-tract or per-capita metric is allowed to publish.
5. **Fiscal-year placement (§3, A20).** Confirm calendar-year-equals-fiscal-year is an acceptable working assumption for all four entities and every adopted source series, or require the fiscal columns be moved off the shared `dim_date` into a date × municipality bridge pre-emptively.
6. **Whether ward-boundary versioning (§4, §6) warrants its own ADR** rather than being treated as an uncontested mechanical modelling pattern, given how directly it affects any multi-year by-ward comparison's meaning.

**Must wait for real source verification — cannot be usefully ruled on yet:**

- Every field-existence question in the Assumptions register, Group A (A1–A9) — no schema has been read.
- Whether SCD2 can use a native source history field instead of bronze-snapshot-diffing (A6) — unknowable until a live schema is read.
- The real dwelling-unit field semantics per source (A2, A3, A4, A12) — the design's mitigation (§6 row 2) is built to degrade safely either way, but the actual ADR content cannot be written until real values exist.
- Whether Peel Region publishes anything at all (A5) — currently a total unknown, not a partial one.
- Licence text for any of the six registered sources (A25) — `security-and-licence-reviewer` blocks on this independently of this design.
- Exact ward-redistricting effective dates for Mississauga and Brampton (A19) — Toronto's 2018 change is reasonably well known; the other two are not confirmed at all.
- StatCan and CMHC product IDs, and therefore whether population enrichment on `dim_municipality` and any cross-source reconciliation control totals are even possible in the timeline (A21, and the broader CMHC adoption question already flagged `not-adopted` in `config/sources.yml`).

---

*This document is designed against zero confirmed rows from any of the six registered sources. Its purpose is to give `director-data-engineering` a concrete, falsifiable structure to approve, amend, or reject — not a claim that any of it has been observed in real data. `docs/conformance-matrix.md` is created and populated once Phase 2 ingestion produces the first real schema to conform.*
