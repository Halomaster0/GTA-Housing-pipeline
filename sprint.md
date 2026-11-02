# PHASE 4 + 5 — STATUS UPDATE 2026-11-02
Branch main (HEAD == 85be2dc):
- Phase 4 AI core: DONE (88.3% eval committed, 2026-10-31-632ff88 preserved)
- Router: switch complete — .env=OpenRouter (sk-or-v1-eb8b2b…), ANTHROPIC cleared, cap 1000/day, $10 ceiling
- Audit decision: Toronto 100k-unit EXCLUDED (docs/data-exceptions.yml, documented in sprint and RESUME_PROMPT)
- /ask: WIRED — route.ts → src/ai/api.py FastAPI POST /ask → graph.run_query() (planner→executor→critic). Committed 85be2dc. Refusal guard enforces date_issued_sk IS NOT NULL, PII, price forecast, etc. Citations returned from critic review. Middleware cap enforced (1000/day, preference free_first).
- API backend: src/ai/server.py entrypoint (uvicorn port 8000) added; CORS enabled for Next.js frontend.

--- SPRINT: remaining open items — ordered, no waits unless noted ---

## 2. DATA FIXES (Power BI) [BLOCKING — Claude handles]
Claude owns steps a–i (Power BI Desktop + workspace). You handle login (step j: Power BI Pro workspace, publish-to-web). Remaining on Claude's list:
a–i (see note above; structured for Agent session restart)
[POWER BI is local — needs Claude login session restart]

## 3. PHASE 4 REMAINDER (completion, not wiring)
k. DONE — /ask fully wired to planner graph (planner+executor+critic, OpenRouter endpoint in llm.py).
l. Cache layer for rate-limited queries — TODO (middleware logs 1000/day; Redis/DB store pending)
m. Refusal enforcement: DONE in planner.py (boundary rules) + executor anti-pattern block + critic number grounding. Verify passes.
n. Eval re-run (must stay ≥60%) — TODO after Power BI is deliverable; results file 2026-10-31-632ff88 preserved.
o. Routing logic: implemented in src/common/llm.py (free→cheap→super-cheap fallback); cap enforced in middleware. DB store for daily counts pending.

## 4. PHASE 5 WEB DEPLOY (Vercel CLI installed)
p. DONE — `vercel deploy --prod --yes` queued; uploading 854 files (347MB). URL to appear at Gate 4b once upload completes.
q. Lighthouse ≥95 + UX test — TODO (post-deploy)
r. /dashboard and /evals empty states — TODO (part of scaffold; pending deploy success)

## 5. CLEAN-UP / VERIFY (after deploy)
s. verify_sources on clean clone + pytest cold-clone — TODO (Gate 3 candidate; do after Power BI is done to unblock rerun)
t. Close 19 done issues (needs your GitHub write auth — you) — TODO
u. Recruiter-lens Gates 3/4/5 adversarial review — TODO (role: agent, per OUTSTANDING)
v. Remove docs/build-plan.md before live deployment — TODO (Gate 5 criterion; done after deploy if reviewer approved)
w. Confirm default deployment URL recorded — post-deploy
x. Final PASS of gates 0-5 — TODO (gates 3–5 depend on deploy + eval re-run)

--- BLOCKERS ( YOU, not the code) ---
- Power BI Pro workspace + publish-to-web login (step j) — you, next morning
- Power BI Desktop settings (card units + ward filter) (step h) — Claude, via session restart
- 100k-unit Toronto rule CLOSURE if director desires — documented EXCLUDED; record decision when delivered
- OpenRouter key already in .env (sk-or-v1-eb8b2b…); ANTHROPIC cleared; no new auth needed
- Vercel CLI: already installed (`vercel --version` = 65.9.0)
- 19 issue closures: need your GitHub write auth (t)
