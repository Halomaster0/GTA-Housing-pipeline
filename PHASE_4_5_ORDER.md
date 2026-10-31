# PHASE 4 + 5 — ORDERED TODO (from OUTSTANDING.md + your hits)
Week of 2026-10-31. Status: Phase 4 AI core DONE (88.3%). Phase 4 remainder / Phase 5 / data-vintage decision open.

ORDER (do not skip):
1. DATA VINTAGE DECISION [BLOCKING] — Sept (gold-sept-csv) vs Oct (warehouse.duckdb 833,848).
   - Sept passes gate (matches pbix); Oct has +5,126 permits (refreshed source feeds) + unverified Tokyo.
   - Action: confirm with data-quality-auditor whether Oct Toronto data is safely excluded; if yes → switch default to Oct; else keep Sept + document.
2. DATA FIXES (Power BI) — from review 2026-10-22 / OPEN.
    a. Remove Net New cross-muncipality Total (BLOCKING — category error).
    b. Recompute Permits Issued from current gold (652,715) — fix card + footnote [BLOCKING].
    c. Rule CANCELLED (58,890) whether counts as issued → record in docs/data-dictionary.md.
    d. Emit all measures from scripts/reconcile_measures.py (M1 has no recon value).
    e. Annotate by-year chart coverage starts (MISS 2018; TOR/BRAM 2010).
    f. Fix donut label collision (REFUSED 347 suppressed).
    g. Refresh footer from manifest (2026-09-10 stale).
    h. Build page 3 Pipeline Velocity (supported, median 28/34/44d).
3. API / ROUTER SWITCH (already in .env; needs wiring) [BLOCKING for /ask].
    a. Confirm OPENROUTER_API_KEY present; set ANTHROPIC to empty.
    b. Set API_BASE_URL to OpenRouter endpoint (free tier / cheap routing).
    c. Cap at 1000/day; use super-cheap/free models first (try free routers with 10 credits; fall back cheap paid if free fails). Set LLM_DAILY_SPEND_CEILING_USD accordingly.
    d. Update planner/executor to use openrouter endpoint instead of localhost/anthropic.
4. PHASE 4 REMAINDER — retrieval paths + /ask wiring.
    a. Build /ask endpoint (Next.js / web/app router). Use cached fallbacks for rate/ceiling.
    b. Wire to warehouse query (read-only, date_issued_sk IS NOT NULL guard preserved).
    c. Commit + PR (branch: not needed — use PR if team requires, else direct for speed given restart).
5. PHASE 5 WEB — commit scaffold (web/, 6 routes, map, a11y script, HANDOVER-5) → PR → merge → deploy preview (Vercel free) → Lighthouse ≥95 + 90s test.
6. CLEAN-UP / VERIFY.
    a. verify_sources + pytest on clean clone.
    b. Close 19 done issues (needs human auth — not agent-doable).
    c. Recruiter-lens passes G3/4/5.
    d. Remove docs/build-plan.md at Gate 5.
7. THING YOU ASKED ABOUT OPENROUTER / FREE MODELS / CAP.
    - The 10 credits go further with cheap/free routers. Config: OPENROUTER_API_KEY active; ANTHROPIC dead; ROUTE_TO_FREE=1; FALLBACK_CHEAP=1; DAILY_CAP=1000; CEILING_USD=low.

WHAT I CAN START NOW (without external approvals):
- Update .env with router endpoint + cap settings.
- Write the CLI command chain for Vercel deploy (vercel login + vercel --prod notes).
- Create /ask route stub + wire router endpoint into planner.
- Start the data-vintage decision doc (Sept vs Oct comparison table using gold-csv vs warehouse).

WHAT NEEDS YOU / EXTERNAL (cannot complete):
- Confirm Oct Toronto data safe → switch default.
- Power BI Desktop settings (card display units + ward filter) — needs Desktop open.
- Anthropic removal confirmation for other files (docs/build-plan.md still references Anthropic — needs edit).
- Vercel account / deploy URL confirmation.
- 100k-unit Toronto rule (data-quality-auditor + director).
