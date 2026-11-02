=== TOMORROW RESUME PROMPT (paste to me, session restart handles Vercel CLI) ===

Context (in repo at main 66c7581, all committed):
- Phase 4 AI core: 88.3% eval (evals/results/2026-10-31-632ff88.json); planner (date_issued_sk IS NOT NULL refusal guard); executor (SQL anti-pattern block).
- Router: .env => openrouter endpoint; ANTHROPIC empty; cap 1000/day; $10 ceiling; free/cheap/super-cheap.
- Data decision (docs/data-vintage-decision-2026-10-31.md, Update 2026-11-02): published figures stay on the Sept export (Permit Records 827,919 / Permits Issued 647,589) until October Toronto data is validated. Oct warehouse (833,848 rows / 652,715 issued) is the working source only. Toronto 100k placeholder => EXCLUDED (not published; docs/data-exceptions.yml EXCLUDED-PENDING).
- Phase 4 remainder: /ask stub (web/app/ask/route.ts) + middleware (cap/routing); full graph wiring open.
- Phase 5 web: web/ scaffold exists; deploy preview needed; Lighthouse ≥95; 90s UX test.
- Sprint.md (in repo): 7 steps; BLOCKING items marked; your Power BI login + Vercel deploy + 19 issue closures listed.

Quick resume order (pick one):
1. Power BI BLOCKING (step 2 of sprint.md): remove Net-New cross-muncipality total, Permits Issued card on Sept 647,589 (not Oct 652,715), CANCELLED rule, donut fix, footer refresh, page 3 Pipeline Velocity, save Desktop settings (card units + ward filter).
2. Phase 4 /ask FULL WIRING: connect route.ts to src/ai/planner.py graph (OpenRouter endpoint), retrieval + cache, citations format.
3. Vercel deploy (step 4): CLI installed; deploy preview (`vercel --prod`); Lighthouse pass.
4. Clean-up / verify (step 6): pytest + verify_sources + 19 issues + gate passes + remove docs/build-plan.md.

Published data: data/gold-sept-csv/ (Sept, 2026-09-10 ingest) until October Toronto data is validated. Working source: data/warehouse.duckdb (Oct 2026). Toronto gap held (see data-exceptions.yml).
Router authority: .env OPENROUTER_API_KEY (redacted); base URL openrouter; cap enforced in middleware.

What needs YOU tomorrow (not the agent): Power BI Pro workspace login + publish (step 2); Power BI Desktop settings save (step 2h); Vercel deploy URL decision (step 4); 19 issue auth (step 6w); 100k-unit audit closure (optional, EXCLUDED is default); October Toronto validation (decides when Oct figures replace Sept as published).
