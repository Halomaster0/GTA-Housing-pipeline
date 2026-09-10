# Gate 2 — Pipeline (bronze → silver → gold)

Date: 2026-09-10 · Verdict: CONDITIONAL PASS (all evidence complete;
single condition below, auditor veto reserved)
Author: `release-manager` (draft — no agent marks its own work done;
sign-offs owed, see below).

## Criteria

| # | Criterion | Evidence (file path / command output) | Status |
|---|---|---|---|
| 1 | `make pipeline` builds gold from empty | `Makefile` `pipeline: ingest transform`; ingest proven live 2026-09-10 (`python -m src.ingest --all` → 20/20 `status=ok`, exit 0, twice byte-identical, ~940k rows — `docs/handovers/HANDOVER-3.md` §2); transform rebuild 2026-09-10 from landed bronze → `data/warehouse.duckdb`, `fct_permits` 827,919 · `fct_applications` 21,658 (identical across rebuilds — `docs/data-quality-report.md`) | PASS with note (full from-empty in one shot not re-run this session; both halves proven idempotent independently) |
| 2 | Reruns are idempotent (identical counts) | Ingest: twice consecutively, byte-identical output (HANDOVER-3 §2). Transform: consecutive `--all --report` rebuilds → 827,919 / 21,658 both times, 0 orphan FKs (verified 2026-09-10, session 5) | PASS |
| 3 | Zero orphan FKs | `docs/data-quality-report.md`: orphan-permit FKs **0**, orphan-application FKs **0**; `python -m pytest tests/` → 26/26 incl. `tests/data/test_warehouse.py` live invariants | PASS |
| 4 | Every table's grain documented | Grain header in every `models/silver/*.sql` + `models/gold/*.sql` (e.g. `05_fct_permits.sql`: "ONE ROW PER BUILDING PERMIT" + collapse rules); app grain = file (ADR-0005); cross-municipality rules in `docs/conformance-matrix.md` | PASS |
| 5 | Data quality report green or every exception explained in writing | `docs/data-quality-report.md` verdict: GREEN except stated expecteds, each explained (NULL geography: Toronto grid-ref + Brampton permits; UNKNOWN app uses: Toronto process codes; 2 future-dated rows + 11,518 demolition-negative nets monitored-with-explanation; StatCan 406 reconciliation owed before per-capita publishes) | PASS |
| 6 | Phase 2 entry conditions (Gate 1 condition iii, carried) | Five ADRs `docs/decisions/0003–0007`; Toronto 32-col capture `docs/sources/evidence/2026-09-10-phase2-field-capture.md` §§1–2; PII-drop + key-stability tests `tests/unit/test_pii_columns.py`, `test_key_stability.py` (key policy enforced every run, recorded in every manifest) | PASS |
| 7 | Data Quality Auditor signs off | Not yet run — veto reserved. This file is the evidence pack for that review | **CONDITION** (the only one) |

## Outstanding items

- (i) `data-quality-auditor` review + sign-off on this evidence pack — the
  single condition for promoting this gate to full PASS. Only the CEO can
  override a veto.
- (ii) PR merge for the session branch (branch protection: PR + 1 review +
  strict status checks). `data/` + `state/` stay untracked (root-anchored
  `.gitignore` — bronze/warehouse are local, reproducible via `make pipeline`,
  not committed data).
- (iii) Carried, not blocking: StatCan series pulls (HTTP 406 — specs stay
  empty until one coordinate succeeds live); Brampton city-vs-regional ward
  equivalence UNCONFIRMED (matrix §3 caveat rides with any ward-level
  Brampton measure); census-tract linkage `unresolved` in v1.

## Sign-offs

Dir. Data Eng: owed · Data Quality Auditor: owed (condition i) ·
Security: licences named at Gate 1; SQL-safety review reserved for Gate 4 ·
Chief of Staff: concurs CONDITIONAL PASS on the evidence above

## CEO decision required

Accept CONDITIONAL PASS (or require auditor sign-off before any Phase 3
measure publishes — recommended: the auditor condition costs nothing and
is the rule working as designed). No cost, scope, or source decision needed:
spend stays **CAD $0.00 / $50.00**.
