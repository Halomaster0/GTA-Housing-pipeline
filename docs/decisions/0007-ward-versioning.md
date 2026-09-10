# ADR-0007: Ward-boundary versioning (ward-version grain for `dim_geography`)

Status: Accepted · Date: 2026-09-10 · Decider: `director-data-engineering` · Reviewed by: Chief of Staff

## Context

The schema design (§4) proposed versioning `dim_geography` by
ward-boundary-as-drawn-for-a-period rather than treating a ward code as a
stable identifier, and asked (§8-6) whether that warrants its own ADR. Live
evidence answered that the meaning change is demonstrated, not hypothetical
(Director ruling §8-6):

- Peel publishes `Wards_20222026` (**27** wards) alongside
  `Ward_Boundary_2018_2022` (**26** wards) — a real redistricting with a real
  count change, plus councillor contact columns on the prior vintage (PII —
  silver-drop, like Toronto `CONTACT_*`).
- Toronto's `city-wards` resource (25 rows) carries `DATE_EFFECTIVE` /
  `DATE_EXPIRY` plus geometry; the package also publishes historical 44-ward
  and 47-ward files.
- Mississauga publishes 11 wards; Brampton wards ride the Peel vintages.
- Fact-side location differs per source: Toronto permits carry `WARD_GRID`
  (a grid ref, not a ward number); Toronto applications carry
  `WARD_NUMBER`/`WARD_NAME`; Mississauga carries integer `WARD`; Brampton
  planning carries string `WARD`; Brampton permits carry addresses with map
  geometry. Ward attribution is per-source and uneven — the dimension must
  absorb that, not assume it away.

A ward numbered "5" before and after a redistricting can be two materially
different areas. Year-over-year by-ward comparisons across a redistricting
without versioning silently blend different geographies — a meaning change,
which clears the ADR-0002 semantic threshold.

## Options considered

1. Versioned grain: one row per (municipality, ward source code, effective
   date range), facts resolved to the vintage in effect on their event date
   (adopted — the schema design §4 proposal, confirmed).
2. One row per ward code, current boundaries only. Rejected: demonstrated to
   corrupt multi-year by-ward comparison across the Peel 26→27 change and
   Toronto's 44→25 history.
3. Defer geography versioning to post-v1. Rejected: the versioned grain
   costs little now (effective-dated rows) and retrofitting it later
   rewrites every fact-side FK.

## Decision

- `dim_geography` grain is one row per ward-boundary version with
  `effective_start_date` / `effective_end_date` / `is_current`, natural key
  `(municipality_sk, ward_source_code, effective_start_date)` — never the
  code alone.
- Fact FKs resolve to the vintage in effect on the fact's event date
  (permit issued/applied date; application submitted date), not the current
  map.
- Census-tract linkage: per-record point-in-polygon where the record has
  point location (Mississauga lat/long; Toronto application X/Y; Brampton
  permit geometry); plurality-overlap fallback flagged per-row via
  `census_tract_allocation_method` (accepted for v1 per Director ruling
  §8-4, with aggregates carrying a comparability caveat). CRS: storage
  EPSG:4326, projected math in EPSG:26917, recorded per-row in
  `geometry_crs`.
- Peel's 2021 tract layer (`CTUID`, `Pop21`, `Dwell21`) seeds tract-level
  denominators independent of StatCan WDS.
- PII rule (from the live schemas): Peel prior-vintage councillor columns
  and Toronto `CONTACT_*` are dropped at bronze→silver, enforced by a data
  test (Gate 1 condition iii-c, carried into Phase 2).

## Consequences

- By-ward time series are correct across redistrictings by construction;
  queries that ignore vintage do so explicitly, not accidentally.
- Tract-level measures in v1 carry approximation flags — visible on the
  geography dashboard page and in the data-quality report.

## Revisit if

- A source publishes authoritative ward-vintage effective dates that
  contradict the seeded vintages, or per-record geocoding coverage proves
  high enough to retire the plurality-overlap fallback entirely.
