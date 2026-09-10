# Director of Data Engineering — schema design review

**Reviewer:** `director-data-engineering` · **Date:** 2026-09-10
**Under review:** `docs/schema-design.md` (DRAFT, 25 assumptions, 7 gold tables)
**New evidence since draft:** `docs/sources/evidence/2026-09-10-local-verification.md`
(all sources verified live; Brampton `_DEV` resolved; all licences named)

## Checklist (per §5.2 — applied to the design, not to merged SQL; no SQL exists yet)

- [x] Ingest idempotence — design assumes business-key dedup (A9); keys observed
  (`PERMITNUMBER`, `FOLDERRSN`, CKAN resource ids). Phase 2 must prove key
  stability with a live sample before trusting the merge — condition (c) below.
- [x] Bronze immutable, partitioned by `ingest_date` — architecture-level, unchanged.
- [x] Grain declared per table (§1) — present and precise; geography grain
  (ward-version, not ward) is the strongest section.
- [ ] PK uniqueness/non-null tests — no tests exist yet; required with Phase 2 code.
- [x] Timezone handling explicit — §7 bare-date rule is correct and avoids a real
  DST-shift bug. Confirmed approach stands.
- [x] Units/CRS conformed — §7 + per-row `geometry_crs`. Stands.
- [x] Gold SQL hand-written — no SQL written yet, as required. Stands.
- [ ] Schema-drift loud failure — required in Phase 2 connectors.

## Rulings on the six §8 open questions

1. **Dwelling-unit ADR granularity:** one umbrella ADR for the `unit_count_basis`
   mechanism now; per-source appendices as each source's semantics are confirmed.
   (Brampton `DWELLINGS` exists but net-vs-gross is still unknown — A12 stands as
   the top risk. Toronto permit unit fields still uncaptured.)
2. **Peel's place:** `is_permit_issuing_authority` flag confirmed sufficient, AND
   the charter/README "four portals" framing must change to three permit
   authorities + Peel as geography/demographics source. Semantic → ADR required.
3. **Linkage policy:** real-key-only confirmed. `FOLDERRSN` appears in both
   Toronto applications and Brampton permits — a shared key MAY exist, but it is
   unproven and cross-municipal. No heuristic join; evaluate the key in Phase 2.
4. **Tract allocation:** plurality-overlap acceptable for v1, flagged per-row via
   `census_tract_allocation_method`, with aggregates carrying a comparability
   caveat. (Peel's 282-tract `Pop21` layer gives a direct denominator regardless.)
5. **Fiscal year:** calendar-year assumption accepted for v1; StatCan period
   mapping is the Data Quality Auditor's reconciliation job, not a schema change.
6. **Ward versioning ADR:** yes — warranted. 26-vs-27 Peel wards observed live;
   the meaning change is demonstrated, not hypothetical.

## Assumption updates from live evidence

Confirmed/answered: A1 (Toronto exposes separable datasets — in fact three:
active/cleared/applications), A5+A14 (Peel is not a permit source; no Peel
application feed found — non-contributor for v1), A6 (no native history;
Toronto apps carry only `DATE_SUBMITTED` — snapshot-from-now rule stands),
A8 (stable ids observed), A16–A19 (real vintages observed), A25 (all licences
named). Still open: A2/A3/A4/A12 (unit semantics), A7 (link key — FOLDERRSN lead),
A9 (key stability — must prove), A20 (accepted per ruling 5).

## Verdict: CONDITIONAL PASS — Phase 2 SQL unblocked subject to

- (a) Four ADRs written before dependent gold SQL merges: unit-basis mechanism,
  Peel framing, application grain, real-key-only linkage (+ ward-versioning ADR).
- (b) Toronto permit 32-column field lists captured before silver SQL assumes columns.
- (c) PII-drop tests (`CONTACT_*`, Peel councillor columns) + key-stability check
  land with the first ingestion code. `data-quality-auditor` veto applies throughout.
