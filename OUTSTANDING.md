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

- [ ] **Fabric on school account** (replaces trial plan — logged, $0
  personal). BEFORE creating anything, answer the 4-item capability
  checklist (HANDOVER-7 §2: capacity, publish-to-web, workspace separation,
  upload path). Then execute HANDOVER-7 §3. Gate 3 stays scoped-partial
  until the dashboard URL exists.
- [ ] **Anthropic API key + spend ceiling** (Phase 4) — the NL query layer
  (`/ask`) cannot run without it. Design guards already exist in the plan
  (rate limits, daily ceiling, cached fallbacks); the key + ceiling number
  are the missing inputs. Owner-to-be: `api-engineer` + `cost-controller`.
- [ ] **Domain/hosting** (Phase 5) — Vercel free tier covers the thin Next.js
  client; record the URL choice at Gate 4b per the build plan. No custom
  domain cost approved or needed yet.

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
- [ ] Phase 4 AI layer: golden question set (~60, written BEFORE tuning),
  planner/executor/critic graph, retrieval paths, eval harness + report.
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
| 4 AI query layer | Not opened | API key (§2) + full layer build (§3) |
| 5 Launch | Not opened | Web app, build-plan removal, all reviews |
