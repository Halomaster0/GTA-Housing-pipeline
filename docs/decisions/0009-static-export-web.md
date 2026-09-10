# ADR-0009: Web app ships as a static export over committed artifacts

Status: Accepted · Date: 2026-09-10 · Decider: `director-product-frontend` ·
Reviewed by: Chief of Staff

## Context

The public site must show real numbers with $0 serving spend and no backend
to operate: `/ask` needs an API key (Phase 4, funded) and `/dashboard` needs
a published Power BI report (Phase 3, funded). A server-rendered Next.js app
would buy nothing until those backends exist — but would cost an always-on
server surface and an API route with nobody to call it securely.

## Options considered

1. Full Next.js server app now (API routes stubbed). Rejected: server
   surface with no backend behind it; `/ask` without rate limiting + spend
   ceiling design live is a billing incident waiting for a key.
2. Wait for backends before any web work. Rejected: landing, data-quality,
   and architecture pages need no backend at all — their numbers already
   exist in committed files.
3. Static export (`output: 'export'`) with build-time data imports (accepted).

## Decision

- `web/` is Next.js App Router + TypeScript, statically exported. No server,
  no runtime data fetching, no API routes.
- Numbers are imported at build time from committed artifacts only:
  `docs/measure-reconciliation.json` (measures) and generated SVG assets.
  A page with no data renders the design-plan §5 empty state — never a
  placeholder, never a hardcoded figure.
- `/ask`, `/dashboard`, `/evals` ship as specified empty states (design-plan
  §5 vocabulary) naming the funded backend each waits on. They become real
  pages when Phase 3/4 land; the routes, nav, and layout already exist.
- Generated assets committed to the repo (`web/public/gta-map.svg`) carry a
  provenance header naming the generating script + source ingest date.
  Regenerate via script; never hand-edit.
- `test:a11y` is a static-HTML assertion script over the exported `out/`
  (one h1, lang, titles, alt text, table captions) — runs in CI free, no
  browser. Lighthouse ≥ 95 stays the human-verified bar at review time.

## Consequences

- Deploy is a static file host (Vercel free tier or equivalent) — no server
  cost, ever, for the current routes. `/ask` will need the API + key later;
  that is a deliberate, separately-gated addition, not a migration.
- Fresh-clone web build needs only `npm ci && npm run build` (fonts load
  from Google Fonts at view time; no build-time network beyond npm).

## Revisit if

`/ask` gets its FastAPI backend (add the route's client + server wiring as
its own ADR), or the project outgrows static hosting.
