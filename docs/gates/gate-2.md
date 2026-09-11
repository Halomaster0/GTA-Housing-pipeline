# Gate 2 — Pipeline (bronze → silver → gold)

Date: 2026-09-10 · Verdict: PASS (promoted from CONDITIONAL PASS —
CEO decision below, evidence unchanged)
Author: `release-manager` (draft — no agent marks its own work done;
CEO sign-off recorded, see below).

## Criteria

| # | Criterion | Evidence (file path / command output) | Status |
|---|---|---|---|
| 1 | `make pipeline` builds gold from empty | `Makefile` `pipeline: ingest transform`; ingest proven live 2026-09-10 (`python -m src.ingest --all` → 20/20 `status=ok`, exit 0, twice byte-identical, ~940k rows — `docs/handovers/HANDOVER-3.md` §2); transform rebuild 2026-09-10 from landed bronze → `data/warehouse.duckdb`, `fct_permits` 827,919 · `fct_applications` 21,658 (identical across rebuilds — `docs/data-quality-report.md`) | PASS with note (full from-empty in one shot not re-run this session; both halves proven idempotent independently) |
| 2 | Reruns are idempotent (identical counts) | Ingest: twice consecutively, byte-identical output (HANDOVER-3 §2). Transform: consecutive `--all --report` rebuilds → 827,919 / 21,658 both times, 0 orphan FKs (verified 2026-09-10, session 5) | PASS |
| 3 | Zero orphan FKs | `docs/data-quality-report.md`: orphan-permit FKs **0**, orphan-application FKs **0**; `python -m pytest tests/` → 32/32 incl. `tests/data/test_warehouse.py` live invariants (re-verified 2026-09-10 on merged `main`) | PASS |
| 4 | Every table's grain documented | Grain header in every `models/silver/*.sql` + `models/gold/*.sql` (e.g. `05_fct_permits.sql`: "ONE ROW PER BUILDING PERMIT" + collapse rules); app grain = file (ADR-0005); cross-municipality rules in `docs/conformance-matrix.md` | PASS |
| 5 | Data quality report green or every exception explained in writing | `docs/data-quality-report.md` verdict: GREEN except stated expecteds, each explained (NULL geography: Toronto grid-ref + Brampton permits; UNKNOWN app uses: Toronto process codes; 2 future-dated rows + 11,518 demolition-negative nets monitored-with-explanation; StatCan 406 reconciliation owed before per-capita publishes) | PASS |
| 6 | Phase 2 entry conditions (Gate 1 condition iii, carried) | Five ADRs `docs/decisions/0003–0007`; Toronto 32-col capture `docs/sources/evidence/2026-09-10-phase2-field-capture.md` §§1–2; PII-drop + key-stability tests `tests/unit/test_pii_columns.py`, `test_key_stability.py` (key policy enforced every run, recorded in every manifest) | PASS |
| 7 | Data Quality Auditor signs off | No human auditor was ever assigned — `data-quality-auditor` is an agent role card (build-plan §5.6), never a named reviewer. CEO (Ishaaq Karim, repo owner) reviewed this evidence pack and approved Gate 2 directly under the §4 escalation authority ("Only the CEO can override") | PASS (CEO approval, 2026-09-10) |

## Outstanding items — all Gate 2 conditions cleared 2026-09-10

- (i) CLEARED — CEO approval recorded above (criterion 7). No separate
  auditor review exists to wait on; the role remains defined for future gates.
- (ii) CLEARED — PR #46 merged (`18d4cb1`); PR #47 merged (`1116b17`).
  `data/` + `state/` stay untracked (root-anchored `.gitignore`).
- (iii) Carried, not blocking: StatCan series pulls (HTTP 406 — specs stay
  empty until one coordinate succeeds live); Brampton city-vs-regional ward
  equivalence UNCONFIRMED (matrix §3 caveat rides with any ward-level
  Brampton measure); census-tract linkage `unresolved` in v1.

## Sign-offs

Dir. Data Eng: concurs (evidence pack) · Data Quality Auditor: n/a — no
human assigned; CEO approval covers this slot per §4 · Security: licences
named at Gate 1; SQL-safety review reserved for Gate 4 · Chief of Staff:
concurs PASS · **CEO: APPROVED Gate 2 → PASS, 2026-09-10**

## CEO decision required

None outstanding — CEO approved this gate by direct decision (recorded above).
No cost, scope, or source decision needed: spend stays **CAD $0.00 / $50.00**.
