# Handover 5 — Web scaffold (static site live from committed artifacts)

**Date:** 2026-09-10 · **Covers:** session 9 (continues `HANDOVER-4.md`)
**Status: the site builds, passes lint + static a11y, and renders real
numbers on 3 routes; /ask, /dashboard, /evals are specified empty states
awaiting funded backends. Spend CAD $0.00. Work uncommitted — commit
decision owed.**
**Branch state:** `main` (`18d4cb1`, only branch) + uncommitted web pack ·
pytest 32/32 · ruff clean · `npm run lint/build/test:a11y` all green.

Detail lives elsewhere: ADR-0009 (static-export decision) ·
`docs/design-plan.md` (the token/component law) · `web/` (the app).

---

## 1. What shipped

| Artifact | What it is | Verified how |
|---|---|---|
| `web/` Next.js 15 + React 19 + TS strict | 6 routes: `/`, `/data-quality`, `/architecture` (real), `/ask`, `/dashboard`, `/evals` (empty states). Static export, no server | `npm run build` → 9 static pages in `web/out/` |
| Design tokens (`app/globals.css`) | Palette, type scale (Plex Condensed / Source Serif / Plex Mono), components from the approved plan; dark mode via `prefers-color-scheme`; zero animations | Built CSS inspected; contrast pairs per plan §2 |
| Map (`scripts/build_map_svg.py` → `web/public/gta-map.svg`) | Real Peel boundary rings (3857) + Toronto ward polygons, fills by gold volume, Caledon no-data state, counts from reconciliation JSON | Regen byte-identical (SHA256 match); inlined at build so page CSS owns fills |
| `scripts/a11y-check.mjs` + `npm run test:a11y` | Static HTML assertions (one h1, lang, titles, captions, alts, skip link, map role) | 7/7 pages pass |
| Reconcile `bronze` + `integrity` sections | Landing status table + data-quality page read committed JSON only | 2 new contract tests (32 total) |
| ADR-0009 | Static export, JSON-baked data, committed generated assets, empty-state routes | Accepted |

## 2. Deliberate deviations / judgement calls (for reviewers)

- jsx-a11y forbids `tabIndex` on scroll regions; the approved plan §7
  mandates it. Plan wins — documented disable/enable pairs in code.
- No Tailwind: hand-rolled tokens match the plan exactly and keep the
  bundle at 103 kB first load. No `next/image`, no client JS beyond hydration.
- Fonts via Google Fonts `<link>` (runtime fetch, no build-time network
  beyond npm); system fallbacks if offline.
- `web/out/` gitignored; `package-lock.json` committed (`npm ci` contract).

## 3. Next agent actions (also in `OUTSTANDING.md`)

- Commit this pack (suggested: one `feat(web)` commit — everything is new
  except 4 small Python edits) on a fresh branch → PR → CI (`web.yml` fires
  on `web/**`) → merge.
- Deploy preview: `web/out/` on any static host (Vercel free tier); record
  the URL at Gate 4b per the plan — do NOT print a subdomain (build-plan header rule).
- Human Lighthouse pass (≥ 95 a11y) at review time; the script is the floor.
- Funded backends flip empty states to real pages: Fabric trial → dashboard
  embed; API key → `/ask`; eval harness → `/evals` (each its own ADR).

## Rules that do not bend (restated, still enforced)

Every rendered number comes from a committed artifact produced by a committed
script. Empty states state the specific reason, never a placeholder. No secrets,
ever. No paid resource without a CEO decision in the cost log.
