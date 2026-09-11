# ADR-0010: Power BI Pro workspace, no lakehouse

Status: Accepted · Date: 2026-09-11 · Decider: CEO (tenant evidence in chat)
· Reviewed by: Chief of Staff

## Context

The school tenant's workspace creation offers only Power BI Pro and Premium
Per-User — no Fabric capacity (F-SKU) and no trial option on this screen.
Without capacity, lakehouse/OneLake items in `fabric-setup.md` cannot run.
The choice is Pro vs PPU for a pure Power BI serving layer.

## Options considered

1. Premium Per-User. Rejected: its advantages over Pro are 48 refreshes/day
   (we need ~weekly), >1 GB semantic models (ours is ~830k fact rows, far
   smaller), and the XMLA endpoint (only matters for external tooling; the
   model is built by hand in Desktop). PPU additionally restricts viewers
   to PPU holders — strictly worse for a public portfolio artifact.
2. Power BI Pro (accepted). 8 refreshes/day exceeds weekly needs; viewers
   inside the tenant are covered by school licensing; the public audience
   goes through publish-to-web (tenant permitting — still unconfirmed,
   tested at publish time with the screenshot fallback ready).

## Decision

- Serving = Power BI Desktop (free) → import the 7 gold parquet files →
  model per `fabric-dax.md` → publish `.pbix` to a dedicated `gta-housing`
  Pro workspace. No lakehouse, no OneLake, no gateway in v1.
- Refresh is manual republish on new ingest dates + `make reconcile` as the
  publish gate (already the documented v1 in `fabric-setup.md` §5).
- `fabric-setup.md` lakehouse sections stay as the capacity-upgrade path,
  not the plan. DuckDB remains the source of truth (unchanged).

## Consequences

- Gate 3's dashboard-URL criterion is reachable without any trial or spend.
- If workspace creation fails on licensing, retry PPU and report back —
  the model artifacts transfer unchanged.
- Graduation/access loss still degrades serving only, never the build.

## Revisit if

A Fabric capacity appears on the tenant (revisit the lakehouse path), or
publish-to-web proves blocked (decide: private link + screenshots).
