# OUTSTANDING — everything not yet done (canonical leftover list)

This file is the single list of what remains. Items leave this list only by
being done (with evidence) or by a CEO decision to drop them. Nothing here
blocks anything else unless marked BLOCKING. Spend to date: CAD $0.00 / $50.00.

## 1. Needs you (human steps — no agent can do these)

- [x] PR #46 opened, reviewed, merged (`18d4cb1`); all 4 merged branches
  deleted local + remote.
- [x] PR #47 (`claude/web-scaffold-static-export`) reviewed + merged
  (`1116b17`). `web.yml` CI ran green on the branch before merge (lint,
  build, a11y) after one fix commit (generated `next-env.d.ts` excluded
  from eslint).
- [ ] Deploy preview of `web/out/` (any static host; URL at Gate 4b, no
  subdomain) + human Lighthouse pass (≥ 95) + ninety-second test.
- [x] PR #49 (`claude/ui-ux-pass-touch-a11y`) reviewed + merged (`fb02c8e`).
  Merged branch deleted; only `main` remains.
- [ ] Close the 19 done issues (HANDOVER-6 §4 list: #1, #7–#22, #25, #27)
  with evidence comments. No auth for this exists in the agent environment
  (HANDOVER-6 §5) — needs a human with write access.
- [ ] Verify on `main` (`verify_sources` + pytest) — the cold-clone-style check.
- [x] Gate 2: CEO approved → full PASS → merged to `main` (PR #48,
  `1c89893`). No human auditor was ever assigned (agent role only).
- [ ] Measure-pack review (`docs/measure-reconciliation.json`) — still open;
  fold into the next human review or CEO-accept with Gate 3.

## 2. Needs funding (CEO cost decision BEFORE any click — see ADR-0008)

- [ ] **Power BI Pro workspace `gta-housing`** (school account, $0 personal,
  logged; ADR-0010 — no lakehouse: tenant offers Pro/PPU only). Create it,
  then: Desktop → import 7 parquet → model per `fabric-dax.md` → verify
  values vs reconciliation JSON → 5 pages per `report-plan.md` → publish.
  Publish-to-web still unconfirmed (tested at publish; screenshot fallback
  ready). Gate 3 stays scoped-partial until the dashboard URL exists.
- [ ] **Anthropic API key + spend ceiling** (Phase 4) — the NL query layer
  (`/ask`) cannot run without it. Design guards already exist in the plan
  (rate limits, daily ceiling, cached fallbacks); the key + ceiling number
  are the missing inputs. Owner-to-be: `api-engineer` + `cost-controller`.
- [ ] **Domain/hosting** (Phase 5) — Vercel free tier covers the thin Next.js
  client; record the URL choice at Gate 4b per the build plan. No custom
  domain cost approved or needed yet.

## 2b. Power BI report fixes (review 2026-10-22, pages 1-2 built)

Full findings: `docs/reviews/powerbi-build-review-2026-10-22.md`. Reconciliation
against `docs/measure-reconciliation.json` PASSED — every figure matches the
warehouse. These are labelling and definition defects, not data defects.

- [ ] **BLOCKING — remove the `Net New Units` cross-municipality Total.**
  Toronto is net (`created − lost`), Mississauga and Brampton are gross
  (`res_units`, `dwellings`). Summing them is a category error, not a caveat
  case. ADR-0003 forbids publishing it as a clean number. Add the comparability
  card that `fabric-dax.md` M2 already specifies, plus NULL coverage (64.3% of
  permit rows carry no unit count).
- [ ] **BLOCKING — `Permits Issued` overstates by ~21%.** Published figures stay on the
  September export (decision 2026-11-02; `docs/data-vintage-decision-2026-10-31.md`,
  Update 2026-11-02): Permits Issued 647,589 (TOR 462,039 / MISS 34,614 /
  BRAM 150,936) against 827,919 permit records. The card must not present the
  827,919 records as issued. The October warehouse count (652,715 issued; TOR
  465,637 / MISS 35,041 / BRAM 152,037; 833,848 rows) is the working figure only
  and is not published until October Toronto data is validated. Separately: the
  gap is partly un-issued permits and partly permits issued outside dim_date's
  2010-2028 range, which the file cannot distinguish — state it as such.
- [ ] Rule on whether the 58,890 CANCELLED permits count toward "permits
  issued", and record it in `docs/data-dictionary.md` either way.
- [ ] Emit every published measure (M1 included) from
  `scripts/reconcile_measures.py`. M1 has no reconciliation value today, which
  is why the defect above was not caught by a process built to catch it.
- [ ] Annotate the permits-by-year chart: Mississauga's coverage starts 2018,
  Brampton and Toronto 2010. Add a coverage-start table to page 5.
- [ ] Fix the application-status donut — one slice label (REFUSED, 347) is
  suppressed by collision, so visible labels sum to 21,311 against a centre
  total of 21,658. Prefer a sorted bar chart.
- [x] **Data vintage decided 2026-10-31, revised 2026-11-02**: published figures stay on the
  September export (`data/gold-sept-csv/`, 2026-09-10 ingest; Permit Records 827,919,
  Permits Issued 647,589) until October Toronto data is validated. The October
  warehouse (`data/warehouse.duckdb`, 833,848 rows, 652,715 issued) is the working
  source only. Toronto 100k-unit placeholder (`docs/data-exceptions.yml`,
  EXCLUDED-PENDING) stays excluded from published Toronto net units pending audit.
  See `docs/data-vintage-decision-2026-10-31.md`.
- [ ] Build page 3 (Pipeline Velocity) — fully supported: M6 medians for all
  three municipalities (TOR 28d / MISS 34d / BRAM 44d) plus three honest empty
  states. Strongest page in the deck for the target role.

## 3. Technical work owed (no cost — future sessions)

- [ ] StatCan series pulls return HTTP 406 from here (specs stay empty until
  one coordinate succeeds live). Unlocks: P1 per-capita, P3 control totals,
  `population_latest`. Owner: `ingestion-engineer`.
- [ ] Brampton city-vs-regional ward equivalence UNCONFIRMED (matrix §3) —
  verify before any ward-level Brampton measure publishes without the caveat.
  Owner: `transform-engineer`.
- [ ] Permit↔application linkage needs a proven key (ADR-0006; unlocks P2
  application→permit timing). Owner: `transform-engineer`.
- [ ] Census-tract spatial step (tract linkage `unresolved` in v1; per-capita
  denominators live in `silver.census_tracts`, not on facts).
- [ ] SCD2 status history is seeded all-current — needs a second ingest on a
  later date to demonstrate real diffs.
- [x] Phase 4 AI layer core: golden question set (60 questions, 6 buckets),
  planner/executor/critic graph, and eval harness with a 60% correctness CI
  gate. Full 60q run: **88.3% correctness**, 81.7% faithfulness, 100% refusal
  accuracy (`evals/results/2026-10-31-632ff88.json`). Planner refuses and the
  executor blocks the `dim_status.status_code='ISSUED'` anti-pattern; issued
  permits are `date_issued_sk IS NOT NULL`. Golden facts are re-derived from
  the warehouse by `evals/repair_golden.py` so the baseline cannot drift again.
- [ ] Phase 4 remainder: retrieval paths, a committed eval report, and wiring
  `/ask` in the web app. Owner: `api-engineer`. Blocked on the API key (§2).
- [ ] Phase 5 web app: scaffold DONE uncommitted (`web/`, 6 routes, map,
  a11y script — HANDOVER-5). Still owed: commit → PR (`web.yml` CI) →
  merge → deploy preview (static host, URL at Gate 4b, no subdomain) →
  human Lighthouse pass (≥ 95) + ninety-second test. `/ask`, `/dashboard`,
  `/evals` stay empty states until §2 backends land.
- [ ] Recruiter-lens passes at Gates 3, 4, 5 (adversarial reviews, blunt by design).
- [ ] `docs/build-plan.md` removal before live deployment (Gate 5 criterion —
  `release-manager` verifies, `oss-maintainer` owns).

## 4. Gate status

| Gate | Verdict | Outstanding |
|---|---|---|
| 0 Charter | PASS | — |
| 1 Foundations | PASS | — |
| 2 Pipeline | PASS | CEO-approved 2026-09-10 (no human auditor assigned; §4 authority) |
| 3 Serving & BI | Not opened | Fabric trial (§2) + dashboard build |
| 4 AI query layer | Opened (partial) | Planner→executor→critic graph + eval harness landed (88.3%); API key (§2), retrieval paths, `/ask` wiring remain |
| 5 Launch | Not opened | Web app, build-plan removal, all reviews |

## 5. Post-completion extension: AWS analytics layer (does not reopen any gate)

Added 2026-11-04, outside the gate sequence. It is an optional verification path,
not part of the pipeline or the serving decision. Decision and limits:
[ADR-0011](docs/decisions/0011-aws-analytics-layer.md).

- [x] Stage 0 smoke test (2026-11-04, us-east-2; scanned 0 bytes; torn down).
- [x] Budget edited (2026-11-04): IncludeCredit=false, actual 80% alert added.
      The existing hand-made budget already filters out credit and refund records.
- [ ] **Root MFA is not enabled** (IAM account summary, 2026-11-04). Owner action.
- [ ] Budget alert test or console screenshot confirming it is active (redacted).
- [ ] Terraform PR 1 (`feat/aws-analytics-terraform`, commit `e1573d9`): reviewed,
      not yet merged.
- [ ] Parity PR (commit `c33c6eb`): reviewed, not yet merged. Parity test not yet run.
- [ ] Docs PR: ADR-0011, README section, `.env.example`, this section, cost-log entry,
      HANDOVER-8.
- [ ] **Owner review of the Terraform plan, then `terraform apply`** (creates billable
      resources in the personal account; the owner runs it).
- [ ] Parity run after apply; record bytes scanned in `docs/aws-parity-report.md`.
- [ ] Day-2 cost entry in `docs/cost-log.md` (owner).
- [ ] Decide the lifecycle: destroy after evidence capture (default) or keep the near-free
      parts. Destroy is the owner's command: `terraform -chdir=infra/aws destroy`.
- [ ] Stage 5 (GitHub OIDC parity in CI): skipped unless the owner asks, and only if
      the deployment is kept.
