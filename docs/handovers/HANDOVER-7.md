# Handover 7 — Fabric kickoff on the school account

**Date:** 2026-09-11 · **Covers:** session 16 (continues `HANDOVER-6.md`)
**Status: PR #49 merged (`fb02c8e`); branches cleaned (only `main`).
CEO switched serving from trial plan to school-account capacity ($0
personal, logged). Nothing is provisioned yet — the portal clicks are human
work this agent cannot perform. Spend CAD $0.00.**

---

## 1. What changed on the repo side

- `main` @ `fb02c8e` (PR #49: UI fixes + Gate-2 merge resolution). Verified
  merged via API; local `main` fast-forwarded, clean.
- `claude/ui-ux-pass-touch-a11y` deleted local + remote (was merged).
- `docs/cost-log.md`: school-capacity decision line ($0.00 personal) +
  free-tier inventory updated (borrowed capacity, still below trial risk).
- `docs/fabric-dax.md`: M1–M8 in DAX mirroring the verified DuckDB
  definitions, with reference values + the relationship map (one active date
  role per fact). First refresh MUST confirm model values against
  `measure-reconciliation.json` before publishing.
- `OUTSTANDING.md` §2 + standup updated (this session).

## 2. Capability checklist — answer from the school tenant BEFORE creating anything

At https://app.fabric.microsoft.com (school login). Paste back the answers;
each one routes differently:

1. **Capacity:** create (don't finish) a workspace → what license options
   are offered (Trial / Fabric capacity F-SKU / Power BI shared)? Is there
   an existing capacity you can see under Settings → Admin portal (or ask:
   does your program grant one)? No capacity = lakehouse won't run — stop
   and report; trial becomes the fallback.
2. **Publish to web:** school tenants often disable it (Admin portal →
   Tenant settings → Publish to web). If OFF and unchangeable, `/dashboard`
   cannot embed publicly — fallback is a private report link + committed
   screenshots, decided then, not now.
3. **Separation:** workspaces are cheap — the project gets its OWN workspace
   (`gta-housing`), never mixed with coursework. Confirm you can create one.
4. **Upload path:** confirm Files → Upload works in a lakehouse (needed for
   the 7 parquet files; the big one is ~13 MB, trivial).

## 3. Execution order once capabilities are confirmed

1. Create workspace `gta-housing` on the confirmed capacity.
2. Create lakehouse `gta-housing-lh`; upload `data/gold-parquet/*.parquet`
   (`make export-gold` regenerates them; row counts in §1 of HANDOVER-4).
3. Load 7 tables 1:1 (§2 of `fabric-setup.md`); verify counts match.
4. Build semantic model: relationships + M1–M8 from `fabric-dax.md`;
   confirm every value against the reconciliation JSON.
5. Build the 5 report pages (`report-plan.md`); publish; test the embed
   visibility rule from checklist item 2; record the URL.
6. Gate 3 file (scoped: dashboard-URL criterion flips to PASS).

## 4. Standing caveats (unchanged)

- PII: none in the data (dropped bronze→silver) — safe to upload to any tenant.
- DuckDB remains the source of truth; losing school access degrades serving
  only, never the build. Graduation = migrate workspace or export the report.
- Weekly refresh is MANUAL until automated (re-upload + refresh button +
  `make reconcile` as the publish gate).

## Rules that do not bend (restated, still enforced)

No paid resource without a CEO decision in the cost log (school capacity:
logged). Every published number traces to a committed script + output.
