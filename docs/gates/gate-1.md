# Gate 1 — Foundations & source truth

Date: 2026-09-10 · Verdict: PASS (promoted from CONDITIONAL PASS — all
conditions cleared below, evidence inline)
Author: `release-manager`.

## Criteria

| # | Criterion | Evidence (file path / command output) | Status |
|---|---|---|---|
| 1 | Every source confirmed live with committed row count and licence | `config/sources.yml` (26 entries, `observed_rows` + licences); `scripts/verify_sources.py` → 25/25 pass, exit 0, run 2026-09-10; `docs/sources/evidence/2026-09-10-local-verification.md`; `docs/sources/verification-latest.json` | PASS |
| 2 | Verify script exits 0 | `python scripts/verify_sources.py` → `EXIT:0` (24 OK + CMHC reachability-only, `not-adopted`) | PASS |
| 3 | Cold clone drill passes | Fresh `git clone` of `main` at merge `efabb92`: full tree, `verify_sources.py` 25/25 exit 0, `pytest` 3 passed — run 2026-09-10 in a clean temp dir | PASS (cleared by PR #43 merge) |
| 4 | Repo public with full OSS scaffolding | Public repo; `LICENSE` (MIT), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue/PR templates, `.github/labels.yml` — all committed on the session branch | PASS (branch protection itself is CEO-manual — condition (ii)) |
| 5 | Milestones and issues mirror the phase plan | 42 issues + milestones #1–#6 (Gates 0–5) created via API 2026-09-10; Gate 0 closed, Gates 1–5 open | PASS |
| 6 | Schema design reviewed by Director + ADR for contested decisions | `docs/reviews/director-data-engineering-schema-design.md` — CONDITIONAL PASS with 3 conditions; 5 ADRs (unit-basis, Peel framing, app grain, linkage, ward versioning) owed at Phase 2 start before gold SQL | PASS with condition (iii) |
| 7 | `docs/design-plan.md` submitted for Director review | Submitted; `docs/reviews/director-product-frontend-design-plan.md` — APPROVED with 1 condition (Caledon no-data map state) | PASS |

Decisions closed this gate: Brampton `_DEV` resolved (production MapServer,
guard test `tests/unit/test_sources_registry.py` — 3 passed); all six source
licences named; StatCan product IDs catalogue-copied; CMHC NOT ADOPTED
(data via StatCan); Caledon gap surfaced (scope decision owed Phase 2).

## Outstanding items — all Gate 1 conditions cleared 2026-09-10

- (i) CLEARED — PR #43 merged (`efabb92`); cold clone drill re-run on `main`: PASS.
- (ii) CLEARED — milestones #1–#6, 19 labels synced from `.github/labels.yml`,
  10 topics, branch protection on `main` (PR + 1 review + conversation
  resolution + strict status checks on the 6 `pr.yml`/`web.yml` contexts;
  `verify-sources.yml` deliberately excluded — schedule-only, would deadlock PRs).
- (iii) Phase 2 entry conditions (carried, not blocking): 5 ADRs before gold SQL;
  Toronto 32-column field capture before silver SQL; PII-drop + key-stability
  tests with first ingestion code. `data-quality-auditor` veto applies throughout.

## Sign-offs

Dir. Data Eng: CONDITIONAL PASS (review note) · Dir. Product & Frontend:
APPROVED with condition · Data Quality Auditor: not yet run (no pipeline data
yet — veto reserved) · Security: licences named; SQL-safety review reserved
for Gate 4 · Chief of Staff: concurs CONDITIONAL PASS

## CEO decision required

None outstanding — CEO accepted the verdict by executing this handoff
(PR #43 reviewed and merged; closeout in PR #44).
