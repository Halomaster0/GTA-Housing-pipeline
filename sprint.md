# PHASE 4 + 5 — REMAINING PHASE (from PHASE_4_5_ORDER.md, vercel installed, data decided)
Completed: Phase 4 AI core (88.3% eval), router switch (/env openrouter), audit decision (Toronto 100k excluded), /ask stub + middleware.
Status: main at 66c7581; workdir clean (only new files).

--- SPRINT: remaining open items — ordered, no waits unless noted ---

## 2. DATA FIXES (Power BI) [BLOCKING]  — your 10/31 morning
a. Remove Net New cross-municipality Total (category error: TOR net vs MISS/BRAM gross) [§2b BLOCKING]
b. Recompute Permits Issued card from current gold → **652,715**; add footnote (warehouse date; Toronto gap held) [§2b BLOCKING]
c. Rule CANCELLED 58,890: count toward "issued" or not → record decision in docs/data-dictionary.md
d. Emit every published measure via scripts/reconcile_measures.py (M1 has no recon value)
e. Fix donut label collision (REFUSED 347 suppressed; visible 21,311 vs total 21,658); prefer sorted bar chart
f. Refresh footer from manifest (currently 2026-09-10 stale); as-of now drives source selection
g. Build page 3 Pipeline Velocity (median TOR 28d / MISS 34d / BRAM 44d + 3 honest empty states)
h. Save Desktop settings: card display units + ward filter; copy into generator before commit
i. Toronto units: EXCLUDE per data-exceptions.yml (audit decided) — card must say gap
j. Permission to publish-to-web requires Power BI Pro workspace login (you do this, not agent)

## 3. PHASE 4 REMAINDER (retrieval + full /ask wiring)
k. Wire /ask route.ts fully to planner graph (src/ai/planner.py + executor.py, OpenRouter endpoint)
l. Cache layer for rate-limited queries; cached fallbacks for SuperRouter routes
m. Cite each answer to a SQL / table row; enforce refusals for uncomputable (per-capita P1 etc.)
n. Full eval re-run (must stay ≥ 60%); committed results preserved (2026-10-31-632ff88)
o. OpenRouter routing logic: free → cheap fallback → super-cheap only on free fail; cap enforced in middleware + DB store

## 4. PHASE 5 WEB DEPLOY (Vercel CLI installed)
p. Deploy scaffold web/ via Vercel (`vercel --prod`, URL at Gate 4b, no subdomain per plan)
q. Lighthouse ≥ 95 + ninety-second UX test; deploy preview first, then public
r. Create /dashboard and /evals routes as empty states until §2 backend lands (stays empty)

## 5. CLEAN-UP / VERIFY
s. `verify_sources` on clean clone + `uv run pytest` — cold-clone check
t. Close 19 done issues (needs GitHub auth with write access — you)
u. Recruiter-lens passes Gates 3, 4, 5 (adversarial reviews, note: agent role per OUTSTANDING)
v. Remove docs/build-plan.md before live deployment (Gate 5 criterion)
w. Confirm default deployment URL recorded (Gate 4b)
x. Final PASS of gates 0-5 per build-plan §0 & gate table

--- BLOCKERS ( YOU, not the code) ---
- Power BI Pro workspace create + publish-to-web login (step 2a–i; next morning)
- Power BI Desktop settings (card units + ward filter) — step 2h; next morning
- 100k-unit audit CLOSURE if desired by director (documented EXCLUDED; record decision when delivered)
- OpenRouter key already in .env (sk-or-v1-...); ANTHROPIC cleared; no new auth needed
- Vercel CLI: already installed (`vercel --version` works) — tomorrow use it directly
- 19 issue closures: need your GitHub write auth
