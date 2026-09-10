# ADR-0003: Dwelling-unit canonical measure and `unit_count_basis` mechanism

Status: Accepted · Date: 2026-09-10 · Decider: `director-data-engineering` · Reviewed by: Chief of Staff

## Context

Assumption A12 (schema design) is the highest-risk assumption in the whole
project: if a source's unit field means gross units, project-level totals, or
per-trade duplicates — and the pipeline sums it as net-new units — every
headline metric ("units approved", per-capita comparisons) is internally
consistent, plausible, and wrong. The Phase 2 field capture
(`docs/sources/evidence/2026-09-10-phase2-field-capture.md`) now gives real
field shapes, and they differ per source with semantics unresolved in every
case:

- Toronto permits: `DWELLING_UNITS_CREATED` + `DWELLING_UNITS_LOST` as
  **text**, nullable (`"0"` and null both observed live). Two fields suggest a
  created-minus-lost net is computable — but whether "created" is net-new or
  gross is undocumented.
- Mississauga permits: `RES_UNITS` integer; applications:
  `TOTAL_RES_UNITS` integer plus a `RES_DET/SEMIS/ROWS/APTS/OTH` breakdown.
- Brampton permits: `DWELLINGS` **string**. Brampton planning layers: no unit
  field at all. Toronto applications: no unit field at all.

No source documents net-vs-gross in its schema. Schema alone cannot resolve
A12.

## Options considered

1. One umbrella ADR for the mechanism now, per-source semantic appendices as
   each source is confirmed (Director ruling §8-1 — adopted).
2. One ADR per source now. Rejected: semantics are unconfirmed for all four,
   so four ADRs would record four guesses. The mechanism is the decision that
   unblocks SQL; the semantics are findings that arrive later.
3. No `unit_count_basis` flag; coerce everything to net-new at ingest.
   Rejected: this is exactly the silent-overstatement failure mode A12 names.

## Decision

- Canonical gold measures are `fct_permits.unit_count_net_new` and
  `fct_applications.unit_count_proposed` (never summed together), each paired
  with `unit_count_basis` (`net-new` / `gross` / `project-level` /
  `unknown`), **defaulting to `unknown`, never to `net-new`**.
- NULL means "not reported", never coerced to 0. Toronto text fields are
  cast in silver with cast failures logged, not silently nulled.
- Toronto permits compute `created − lost` only as a *candidate* net value,
  still flagged `unknown` until documentation or a hand-labelled sample
  confirms what "created" denotes.
- Any aggregate over unit counts carries the basis mix: if any contributing
  source row is `unknown`, the published measure carries a comparability
  caveat (surfaced in the semantic model and dashboard), not a clean number.
- A source whose units prove irreconcilable (e.g. project-level totals with
  no per-permit attribution) leaves the measure NULL with an explicit basis
  value, per the schema design §6 irreconcilability rule.
- Per-source semantic findings land as dated appendices to this ADR (A12
  resolution per source), each citing the documentation or sample that
  resolved it.

## Consequences

- Gold SQL can be written now: the mechanism is fixed, and `unknown`-basis
  rows degrade safely instead of corrupting sums.
- Early dashboards will show comparability caveats on unit measures. That is
  the honest state and the senior move (report page 5 exists for this).
- `data-quality-auditor` adds a check: no `unit_count_net_new` value may
  carry basis `net-new` without a cited appendix entry.

## Revisit if

- A source publishes explicit unit semantics documentation, or a 100-row
  hand-labelled sample (per the `rag-architect` precision-sample pattern)
  establishes ground truth — write the appendix, flip that source's basis.
- Cross-source reconciliation against StatCan 34100292 control totals shows
  systematic over/under-count attributable to a basis misclassification.
