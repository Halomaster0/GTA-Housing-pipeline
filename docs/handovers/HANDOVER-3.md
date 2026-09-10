# Handover 3 — Phase 2 entry + bronze ingestion (Gate 2 opened)

**Date:** 2026-09-10 · **Covers:** session 4 (continues `HANDOVER-2.md`;
updated end of session 4 with transform results)
**Status: Phase 2 entry + bronze + transform ALL DONE. `make pipeline`
(a real target now, not an equivalent) runs green end to end. Gate 2 file
drafted (`docs/gates/gate-2.md`, CONDITIONAL PASS, auditor sign-off owed).
Session 5: lint fixed, rebuild re-proven idempotent, branch pushed — PR
opening + auditor review are the next human steps.**
**Branch state:** uncommitted work on top of `main` (`5ba5199`) · pytest
26/26 · ruff clean · `data/` + `state/` gitignored (bronze/warehouse local, not committed)

Detail lives elsewhere and is not repeated here:
`docs/decisions/0003–0007` (the five ADRs) ·
`docs/sources/evidence/2026-09-10-phase2-field-capture.md` (§§1–12, every live fact)
`config/ingest.yml` + `src/ingest/` (the pipeline) ·
`docs/standups/2026-09-10.md` (session 4 entry)

---

## 1. Phase 2 entry conditions — all five closed

| # | Condition (Gate 1 iii / Handover 2 §5) | Evidence |
|---|---|---|
| 1 | Five ADRs before gold SQL | `docs/decisions/0003` (unit-basis mechanism, umbrella + appendices) · `0004` (Peel framing + Caledon scope) · `0005` (app grain = file, with Toronto address-dedup + Mississauga/Brampton union rules) · `0006` (real-key-only linkage) · `0007` (ward versioning) |
| 2 | Toronto 32-column field capture before silver SQL | Evidence §§1–2: both permit resources share an identical 32-col schema; full field tables + sample rows |
| 3 | PII-drop tests + key-stability check with first ingestion code | `src/ingest/pii.py` + `tests/unit/test_pii_columns.py` (7 tests); `src/ingest/keys.py` + `tests/unit/test_key_stability.py` (6 tests); key policy enforced on every run, recorded in every manifest |
| 4 | Caledon scope decision | ADR-0004: in scope as geography, out of scope as facts, explicit no-data UI state — never zero |
| 5 | StatCan per-product `getCubeMetadata` | Evidence §8: 34100292 / 34100143 / 98100002 / 98100014 all `SUCCESS` + `CURRENT`, dimensions recorded |

## 2. Bronze ingestion — built and proven live

`src/ingest/` (9 modules): shared runtime (`base.py`: retried HTTP,
checkpoints, manifests, parquet landing) + one connector per family
(`toronto_ckan.py` CKAN paging · `arcgis_hub.py` OID-range paging ·
`statcan.py` metadata-first) + `drift.py` (field-hash, loud fail + diff to
`docs/drift/`) + `pii.py` + `keys.py` + `spec.py` (registry-validated
`config/ingest.yml`, 20 feeds) + `__main__.py` (`--all` / `--source` /
`--ingest-date`). `Makefile ingest` now runs the real command (replacing
the Phase 1 honest no-op per ADR-0001's own rule).

**Prove-out (all live 2026-09-10):** `python -m src.ingest --all` → **20/20
`status=ok`, exit 0, twice consecutively with byte-identical output.**
~940k rows: Toronto active 206,259 · cleared 435,942 · apps 26,613 · wards
25; Mississauga permits 34,615 · site plan 1,138 · rezoning 290 · wards 11;
Brampton permits 222,276 (grew +13 during the day — live feed) · planning
6,989 / 2,100 / 1,451 / 1,031 / 182; Peel boundary 3 · wards 27/26 · CT 282 ·
stats table 684; StatCan 34100292 metadata doc. Landed counts equal reported
totals on every feed. **Cost: CAD $0.00 / $50.00.**

## 3. What the guards caught (all resolved with evidence, §§10–12)

- Row keys are composite everywhere it matters: Toronto permits
  (PERMIT_NUM, REVISION_NUM, PERMIT_TYPE, _id) — revisions, then
  conditional-vs-definitive pairs, then 9+15 double-entered rows (builder
  reassignment); Brampton permits (PERMITNUMBER, FOLDERRSN, OBJECTID) —
  folder spans shell+finish sub-permits, plus 4 re-processed doubles;
  Mississauga/Brampton-planning composites over source-side double
  publications. Business-key dup counts ride in every manifest as observe
  tails for silver dedup rules.
- Toronto apps grain is per-address (100 rows / 47 distinct APPLICATION#;
  one app = 6 address rows) — ADR-0005 dedup rule written before any silver SQL.
- Peel `Building_Permits` is an aggregate stats table (Year/Quarter/
  Geography grain), not permits — resolved, key amended, registry note
  superseded.
- ArcGIS paging needed two live fixes: OID-field discovery (not always
  `OBJECTID`) + range paging (MapServer truncates at maxRecordCount=1,000
  silently). No-resume rule: same-date reruns replace partitions (a failed
  run's landed files + a resume caused one false drift; file deleted).
- StatCan series pulls return HTTP 406 from here (metadata proven, series
  unproven — specs stay empty until one coordinate succeeds live).
  34100292 geography is CMA-level (no municipal members).

## 4. Transform — DONE (same session, appended)

1. ~~Silver models~~ DONE: `models/silver/00–09` — dedups, PII drops,
   casts, cleared-survivor union, SCD2 status history (21,658 rows seeded,
   all current, `bronze-snapshot-diff`).
2. ~~`docs/conformance-matrix.md` + gold SQL~~ DONE: full raw→conformed
   crosswalks (§§1–4, every value observed live) + `models/gold/00–06`
   (dim_date 6,940 · dim_geography 89 · fct_permits **827,919** ·
   fct_applications **21,658**).
3. ~~`tests/data/` + report~~ DONE: `invariants.py` (orphans/grain/PII) +
   `test_transform_logic.py` (6 fixture tests, CI-safe) +
   `test_warehouse.py` (live); `make transform` + `make report` wired;
   first `docs/data-quality-report.md` written from the build.
4. Live findings fixed in-session: Mississauga ward fan-out (facts now pin
   one dim vintage each; Brampton city-vs-regional equivalence flagged
   UNCONFIRMED in matrix §3); 2 future-dated Brampton rows + 11,518
   demolition-negative nets reclassified as monitored-with-explanation
   (matrix §3); parquet page-schema variance → `union_by_name`.
5. Session 5 closeout: `tests/data/test_transform_logic.py` lint-fixed
   (`ruff check` + `format --check` + pytest 26/26 green); `Makefile`
   gains a real `pipeline: ingest transform` target (Gate 2 criterion is
   now literally true); transform rebuilt → 827,919 / 21,658 identical,
   0 orphans; `docs/gates/gate-2.md` drafted CONDITIONAL PASS with the
   auditor sign-off as the single condition. STILL OWED (human steps):
   open the PR, get 1 review, merge; `data-quality-auditor` review of the
   gate pack. `data-quality-auditor` veto reserved.
6. `.gitignore` fix (same session): `data/`, `bronze/`, `silver/`, `gold/`
   were unanchored and silently ignored `models/silver/`, `models/gold/`,
   `tests/data/` — now root-anchored (`/data/` etc.). `git status` verified
   to show all new source dirs.

## 5. Needs you — nothing blocking

No CEO decision required. Anthropic API key is still a Phase 4 need (unchanged).
Suggested PR reviewers' note: bronze row counts above are local-run numbers
with committed code + committed specs — reproducible via `make ingest`, not
committed data.

## Rules that do not bend (restated, still enforced)

Every published number comes from a real run with a committed script and output.
Evidence is a file path or command output, never an assertion. No secrets, ever.
No agent marks its own work done (Gate 2 needs auditor sign-off + release-manager).
