# Source: CMHC — Housing Starts (optional)

**Status: NOT ADOPTED — pending verification, blocked this session.** Raw evidence:
`docs/sources/evidence/2026-09-10-verification.md` §6.

| Field | Content |
|---|---|
| Portal + canonical URL | `https://www.cmhc-schl.gc.ca`; the Housing Market Information Portal at `https://www03.cmhc-schl.gc.ca/hmip-pimh/en`. Neither reachable this session. |
| API type | **Unknown.** CMHC's public-facing Housing Market Information Portal is, from general knowledge, primarily an interactive web application for building custom table exports (CSV/Excel) rather than a documented open REST API. Whether a stable, unauthenticated, machine-readable API exists behind it was **not confirmed** this session because the host was unreachable. |
| Auth required | UNVERIFIED |
| Licence | UNVERIFIED — no licence page reached. This matters more than usual for CMHC: if the only access path is the interactive portal's table-builder UI, pulling data through it programmatically would functionally be scraping a web application, not calling an open-data API — which conflicts directly with the build plan's own non-goal in §1 ("Not a scraper: official APIs and open-data endpoints only"). |
| Update cadence | UNVERIFIED |
| Row count on 2026-09-10 | **UNVERIFIED — reason: `curl: (56) CONNECT tunnel failed, response 403`** on both candidate hosts. |
| Fields available | UNVERIFIED |
| Fields we need | UNVERIFIED |
| Known gaps | UNVERIFIED |
| Rate limits / pagination | UNVERIFIED |
| Verified live on | **Not verified.** Attempted 2026-09-10 06:11 UTC: `curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://www.cmhc-schl.gc.ca"`; `curl ... "https://www03.cmhc-schl.gc.ca/hmip-pimh/en"`. Both `CONNECT tunnel failed, response 403`. |

## What this source can and cannot answer

**Intended role (optional, per build plan):** a possible cross-check or supplementary series for
housing starts/completions, feeding a control-total comparison against the municipal permit
data — the same reconciliation role StatCan's building-permits survey could also fill.

**What it cannot answer right now:** whether it should be adopted at all. Two separate open
questions block that decision, and both require live access to resolve: (1) does CMHC expose an
actual open API/bulk-download endpoint, as opposed to only an interactive report-builder UI, and
(2) under what licence. Until both are answered "yes, machine-readable API" and "yes, licence
permits public portfolio reuse and redistribution," this source should stay **not adopted**,
consistent with the build plan marking it optional.

## Recommendation

**Do not adopt CMHC in Phase 2 pipeline work.** Statistics Canada's own building-permits and
housing-starts survey tables (see `docs/sources/statcan.md`) are a confirmed-API-shaped
alternative for the same "control total" role, without CMHC's open questions about API existence
and licence terms. Revisit CMHC only if a future network-enabled session confirms a genuine
open, licensed, machine-readable endpoint — and if so, route the licence finding through the
same CEO-escalation path as any other source, per the build plan's instruction that an ambiguous
or restrictive licence is "a CEO escalation, not a footnote."
