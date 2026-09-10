# ADR-0004: Peel Region framing and Caledon scope

Status: Accepted · Date: 2026-09-10 · Decider: `director-data-engineering` · Reviewed by: Chief of Staff

## Context

The charter and README frame the project as "four incompatible portals"
(Toronto, Mississauga, Brampton, Peel). Live verification falsified the
four-peer reading: Peel Region is the upper-tier government and publishes no
permit register — its `Building_Permits` layer holds 684 rows for a region of
~1.5M people (Mississauga alone reports 34,615) and is registered
liveness-only. Peel's real contributions are geography and demographics:
`Municipal_Boundary` (3 rows: Mississauga, Brampton, **Caledon**),
`Wards_20222026` (27) + `Ward_Boundary_2018_2022` (26), and the 2021 census
tract layer (282 tracts with `Pop21`/`Dwell21`). No Peel-authored application
feed with decision authority was found (A14 answered for v1).

Caledon appears in the municipal boundary but has no discovered permit or
application feed of its own. It is the third lower-tier municipality of Peel
and cannot be wished away — nor can a zero be fabricated for it.

## Options considered

1. Keep the "four municipalities compared" framing and show Peel/Caledon as 0.
   Rejected: a structural absence rendered as a finding is a false statement,
   the exact failure the truth discipline (§4) exists to prevent.
2. Drop Peel and Caledon from the model entirely. Rejected: Peel's ward
   vintages and census tracts are load-bearing for geography and per-capita
   denominators, and Caledon's absence must be visible, not silent.
3. Three permit authorities + Peel as geography/demographics source; Caledon
   as an explicit no-data scope entry (adopted).

## Decision

- `dim_municipality.is_permit_issuing_authority` (TRUE for
  Toronto/Mississauga/Brampton, FALSE for Peel Region) is the mechanism, per
  the schema design. Every per-municipality permit/application chart filters
  or annotates on this flag.
- Public framing changes from "four portals" to **three permit authorities
  plus Peel Region as the geography/demographics source**. README and
  dashboard text are updated accordingly (owned by `technical-writer` /
  `report-builder`; tracked as a Phase 2 conformance task, not this ADR).
- Caledon scope ruling: **in scope as geography, out of scope as facts.**
  Caledon gets a `dim_municipality` row (via the Peel boundary seed) with
  `is_permit_issuing_authority = FALSE`, zero fact rows by construction, and
  every UI surface renders it as an explicit no-data state — never zero, per
  the Director of Product & Frontend's approval condition on the design plan.
  The landing map, the municipal comparison page, and the data-quality page
  all name the gap: "no public permit feed discovered for Caledon as of
  2026-09-10."
- Revisit trigger is explicit: if a Caledon (or Town of Caledon) permit feed
  is discovered, this ADR is amended and the feed enters the registry like
  any other source — the gap text is not load-bearing architecture.

## Consequences

- `fct_permits` / `fct_applications` structurally exclude Peel Region and
  Caledon. Data-quality row-count checks must not flag their absence as a
  freshness failure.
- The municipal-comparison narrative becomes "who is actually building
  (among the three issuing authorities), normalised per capita" — a
  defensible, documented comparison instead of a four-way chart with a
  fabricated fourth bar.

## Revisit if

- Peel Region is found to independently decide a class of applications
  (re-open A14 with evidence), or a Caledon permit feed is discovered.
- Ontario municipal restructuring changes the two-tier structure.
