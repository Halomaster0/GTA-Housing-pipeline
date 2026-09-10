# ADR-0005: Application grain is the administrative file, not the project

Status: Accepted · Date: 2026-09-10 · Decider: `director-data-engineering` · Reviewed by: Chief of Staff

## Context

The schema design (§6 row 1) proposed `fct_applications` at one row per
municipally-assigned application/file number, explicitly not one row per
development project. Live evidence now pins down what each source actually
publishes (field capture, 2026-09-10):

- Toronto applications (26,613 rows): grain is **one row per
  application-address**. `limit=100` returned 47 distinct `APPLICATION#`;
  application `22 114201 WET 05 OZ` has 6 rows differing only by street
  address (`5A/7/1/3/5/9 OXFORD DR`) and X/Y. Counting rows as applications
  overstates by ~2x on this sample.
- Mississauga: two separate feeds (site plan 1,138; rezoning 290) with an
  identical 34-field schema keyed on `APP_FILE_NO` — plus `APPLICATION_NO`
  integer and `PLNG_APP_ID`. Two feeds, one grain each.
- Brampton: five planning layers (minor variance 6,989; OPA/ZBA 1,451;
  pre-consultation 2,100; consent 1,031; condo 182), Minor Variance keyed on
  `FILE_NUMBER`. No cross-layer key observed.
- Toronto active + cleared permits share an identical 32-column schema; a
  single-probe overlap check (one active `PERMIT_NUM` against cleared)
  returned 0 matches. Full dedup across the two resources is still owed.

A single physical project routinely spans multiple file numbers (e.g. an OPA,
a rezoning, and a site-plan application for one building — A11), and no
source publishes a project-level master key.

## Options considered

1. Grain at the administrative file number, deduplicating multi-row
   publications to one row per file (adopted).
2. Grain at the development project, rolling file numbers up. Rejected: no
   published project key exists; any rollup would be a heuristic join —
   barred independently by ADR-0006.
3. Grain at the raw publication row (one Toronto address-row = one fact row).
   Rejected: "count of applications" would then count addresses, silently
   doubling project-scale activity in address-rich applications.

## Decision

- `fct_applications` grain: **one row per (municipality, application/file
  number)** as an accumulating snapshot (current status + milestone dates as
  of the latest run). `silver.application_status_history` (SCD2 via
  bronze-snapshot-diff) carries history; the fact carries current state.
- Toronto ingestion deduplicates address-rows to one row per `APPLICATION#`:
  keep the minimum `_id` row as the survivor, plus `address_count` and the
  address list (or a bridge if the list proves analytically needed — decide
  at silver time, document the choice in the model header).
- Mississauga's site-plan and rezoning feeds union into one silver entity on
  `APP_FILE_NO` with a `source_feed` discriminator; a file number appearing
  in both feeds is one application with two facets, not two applications.
- Brampton's five planning layers land as one silver entity keyed on each
  layer's file number with a `planning_layer` discriminator; cross-layer
  project rollups are out of scope for v1.
- Toronto active + cleared permits: treat as two bronze partitions of one
  permit population; dedup on `PERMIT_NUM` with the cleared resource as the
  survivor on collision (cleared = terminal state), and log every collision
  count per run. If collision analysis shows the resources are disjoint in
  practice, the rule stays as a guard, not an assumption.
- "Count of applications" always means count of administrative files. Any
  project-level language in docs, measures, or UI is banned until a real
  project key exists.

## Consequences

- Toronto application counts drop ~2x versus raw row counts. The README and
  dashboard never quote the raw 26,613 as "applications" without the grain
  note — the data-quality report states both numbers.
- `unit_count_proposed` (Mississauga `TOTAL_RES_UNITS`) is per-file, like
  permits per-permit: the two unit measures stay non-comparable (ADR-0003).

## Revisit if

- A source publishes a genuine project/master key (then project rollups
  become real-key work, ADR-0006-compliant).
- Collision analysis on active-vs-cleared contradicts the survivor rule
  (e.g. divergent field values for the same `PERMIT_NUM` beyond status).
