# ADR-0008: Fabric serving deferred — parquet export is the serving contract

Status: Accepted · Date: 2026-09-10 · Decider: Chief of Staff (CEO directive:
maximum no-cost distance) · Reviewed by: `director-platform`

## Context

Phase 3 (Serving & BI) assumes a Microsoft Fabric trial for the lakehouse +
semantic model + Power BI report. A trial is a cost/subsidy decision owned
by the CEO, and the directive for this session is to ship everything that
costs nothing and leave paid components as specified-but-unprovisioned. The
risk this ADR closes: half the Phase 3 deliverables silently depending on a
trial that does not exist yet, blocking the BI work that needs no trial at
all.

## Options considered

1. Provision the Fabric trial now. Rejected: needs a CEO cost decision
   first (cost-controller rule); the whole session brief is to avoid it.
2. Stall all of Phase 3 until the trial. Rejected: the data dictionary,
   measure library, reconciliation, report plan, and publish-path spec are
   trial-independent and are most of the engineering value.
3. Defer provisioning; define the serving contract in repo artifacts.
   Accepted (below).

## Decision

- The serving contract is `data/gold-parquet/*.parquet` (7 files, 1:1 with
  gold tables), produced by `scripts/export_gold_parquet.py` (`make
  export-gold`). A future session uploads bytes; it transforms nothing.
- Measure values are pinned by `scripts/reconcile_measures.py` →
  `docs/measure-reconciliation.json` (committed). A dashboard number that
  disagrees with that file is wrong until proven otherwise — this holds
  with or without Fabric.
- `docs/data-dictionary.md` (tables, columns, M1–M8 + P1–P3 pending,
  DAX sketches, PL-300 mapping), `docs/report-plan.md` (5 pages with
  denominators and empty states specified), and `docs/fabric-setup.md`
  (DRAFT, UNPROVISIONED — execution checklist owed) are the complete
  `report-builder` / `fabric-architect` input pack.
- DuckDB remains the source of truth for development (build-plan §5.8
  constraint, unchanged). If the trial lapses later, serving collapses
  back to the local path with zero rework.

## Consequences

- Gate 3 cannot fully pass without the trial (dashboard URL criterion) —
  the gate file will record a scoped partial with exactly one outstanding
  item: provisioning + execution checklist in `fabric-setup.md` §4.
- `cost-controller`: serving spend stays CAD $0.00; the trial decision and
  its date get logged before any click.

## Revisit if

The CEO approves the Fabric trial (execute `fabric-setup.md` §4), or the
project pivots to a different serving layer (then this ADR is superseded,
not edited).
