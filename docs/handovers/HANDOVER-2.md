# Handover 2 — local verification + GitHub closeout (Gate 1 PASS)

**Date:** 2026-09-10 · **Covers:** sessions 2–3 (continues `HANDOVER-1.md`, which
covered session 1: Gate 0 + Phase 1 scaffolding + runner-side discovery)
**Status: Gate 1 PASS. Phase 2 entry conditions recorded below.**
**Branch state:** `main` at `164afac` (PRs #43 + #44 merged) · CI green · tree clean

Detail lives elsewhere and is not repeated here:
`docs/gates/gate-1.md` (the verdict) · `docs/standups/2026-09-10.md` (sessions 2+3)
`docs/sources/evidence/2026-09-10-local-verification.md` (every live fact from session 2)
`docs/reviews/director-*.md` (the two Director verdicts)

---

## 1. Session 2 — local verification (the environment changed the plan)

Session 1's sandbox blocked all municipal/StatCan egress, so verification ran on
GitHub runners. This session ran on a network-enabled machine, which allowed
every HANDOVER-1 open item to be closed with direct live calls — no new runner
round-trips needed.

### 1.1 Toronto: both permit feeds resolved, licence unblocked

`package_show` + `datastore_search(limit=0)` on all four slugs:

| Package slug | Resource id | Rows | Cols | Refresh |
|---|---|---|---|---|
| `building-permits-active-permits` | `6d0229af-bc54-46de-9c2b-26759b01dd05` | **206,259** | 32 | Daily |
| `building-permits-cleared-permits` | `a96c0ba4-3026-402b-b09d-5b1268b8f810` | **435,942** | 32 | Daily |
| `development-applications` | `8907d8ed-c515-4ce9-b674-9f8c6eefcf0d` | **26,613** | 25 | Daily |
| `city-wards` | `7672dac5-b383-4d7c-90ec-291dc69d37bf` | **25** | 20 | Semi-annual |

**Licence (was HANDOVER-1 blocker #2, now closed).** The CKAN API returns
`license_title: "License not specified"`, but all four dataset pages on
`open.toronto.ca` render `Licence: Open Government Licence - Toronto` linking
to `https://open.toronto.ca/open-data-licence/` (spelled `licence`; the
`-license` spelling 404s). Licence text fetched live: worldwide, royalty-free,
perpetual, commercial use allowed, attribution
`Contains information licensed under the Open Government Licence - Toronto`,
excludes Personal Information. **Ruling: the portal page governs; the API field
is incomplete metadata, not an ambiguous licence.** Registry records both.
Open: active-vs-cleared overlap semantics (Phase 2 conformance, not assumed).

### 1.2 Brampton `_DEV` — RESOLVED (was HANDOVER-1 item #1, highest danger)

| Feed | URL host | Rows | Currency signal |
|---|---|---|---|
| **Production `Building_Permits/MapServer/0`** ✅ ADOPTED | `maps1.brampton.ca` | **222,263** | `INDATE` up to **2026-09-10** (current) |
| `_DEV` copy `Building_Permits_DEV/FeatureServer/0` ❌ REJECTED | `services3.arcgis.com/rl7ACuZkiFsmDA2g` | 141,886 | max `ISSUEDATE` **2018-10-17** (frozen ~8 yrs) |

`_DEV` is smaller AND staler in every comparable pair (Minor Variance 6,989 vs
5,117; OPA/ZBA 1,451 vs 1,036; Pre-Consultation 2,100 vs 681; Consent 1,031 vs
859). The authoritative AGOL item `Building Permits` (owner `BramptonMaps`,
licence **CC BY**) points at production; nothing authoritative points at `_DEV`.
Brampton's Hub sites are literally named `GeoHub DEV`/`GeoHub UAT` — the suffix
is their staging convention leaking into public names.
**Rule: ingest production `MapServer/0`; no `_DEV`/`_UAT` URL registers without
written justification — enforced by `tests/unit/test_sources_registry.py`.**
Production fields include `PERMITNUMBER`, `DWELLINGS` (unit count; net-vs-gross
still open — A12 stands), nullable `ISSUEDATE`. Layer 1 Activity log (2,494,357
rows) is NOT the permit grain, not registered.

### 1.3 Remaining licences (all closed)

- **Mississauga — Terms of Use** (PDF, 4 pages, fetched live): worldwide,
  royalty-free, non-exclusive licence to use/modify/distribute for any lawful
  purpose. Counts re-confirmed: permits 34,615; site plan 1,138; rezoning 290;
  wards 11.
- **Peel — Open Data Licence v1.0** (Hub page item read live): commercial use
  allowed, attribution `Contains public sector Information made available under
  The Regional Municipality of Peel's Open Data Licence - Version 1.0.`
  Service-name correction: the boundary service is `Municipal_Boundary`
  (layer 0 named `MunicipalBoundary_Peel`); the literal name returns
  `Token Required`. Boundary 3 · wards 27/26 · CT census 282 (`Pop16/Pop21`).
  Prior-ward layer carries councillor contact columns → silver-drop like Toronto
  `CONTACT_*`.
- **StatCan — Open Licence** (page fetched live). Catalogue re-confirmed
  (8,270 cubes); IDs 34100292/34100143/34100148/98100002/98100014/98100041
  transcribed as **catalogued** (per-product metadata still owed).
- **CMHC — NOT ADOPTED** (data via StatCan 34100143/34100148; zero new data).

### 1.4 Registry + guards

`config/sources.yml` rewritten: **26 entries** with `observed_rows`, calibrated
`expected_min_rows` (~75–80% of observed), named licences, `verified_on`.
`python scripts/verify_sources.py` → **25/25 pass, exit 0**
(24 OK + CMHC reachability-only). New `tests/unit/test_sources_registry.py`
(3 tests: `_DEV`/`_UAT` justification guard, verified-live evidence guard,
unique ids) — 3 passed. Per-source docs + sources README index updated.

### 1.5 Director reviews (HANDOVER-1 step 4)

- **Data Engineering → schema design: CONDITIONAL PASS**
  (`docs/reviews/director-data-engineering-schema-design.md`). Six §8 rulings:
  (1) one umbrella unit-basis ADR + per-source appendices; (2) Peel flag stands
  AND README "four portals" framing must become three authorities + Peel;
  (3) real-key-only linkage (`FOLDERRSN` appears in Toronto apps AND Brampton
  permits — a lead, not proof); (4) plurality-overlap tract approximation OK v1,
  flagged per-row; (5) calendar-year fiscal accepted v1; (6) ward versioning gets
  its own ADR (26-vs-27 observed). Confirmed: A1/A5/A6/A8/A14/A16–A19/A25.
  Still open: A2/A3/A4/A12 (unit semantics), A7 (link key), A9 (key stability).
- **Product & Frontend → design plan: APPROVED with 1 condition**
  (`docs/reviews/director-product-frontend-design-plan.md`): the landing map
  must render Caledon as explicit no-data, never zero. UI code unblocked 4b.

---

## 2. Session 3 — GitHub closeout (everything CEO-manual, executed)

No UI clicks; all via git + GitHub API using the stored credential (in-memory
only, never printed/logged). The environment's network made the "not
automatable here" list automatable.

| Item | Result |
|---|---|
| 4 scoped commits + push (session branch) | `68e37a8`, `0a4b426`, `6689dfd`, `e8450d8` (last: ruff-format fix after CI caught it) |
| Milestones Gates 0–5 | #1–#6 created (Gate 0 closed) |
| Labels from `.github/labels.yml` | 19 synced (18 updated, 1 created) |
| Topics from `docs/repo-metadata.md` | 10 set |
| Branch protection on `main` | PR + 1 review + conversation resolution + strict checks |
| PR #43 (Gate 1 work, Director checklists in body) | CI red on `ruff format` → fixed → green → merged (`efabb92`) |
| Cold clone drill on `main` | **PASS** (full tree, verify 25/25, pytest 3/3) |
| Gate 1 promoted | CONDITIONAL → **PASS** |
| PR #44 (closeout) | green → merged (`164afac`) |

Two self-found config fixes, both recorded in `gate-1.md`:
(a) required contexts set to the 5 `pr.yml` jobs only — `verify-sources.yml`
is schedule-only (would deadlock PRs) and `web.yml` is path-filtered to
`web/` (would stall docs-only PRs); re-add web context when `web/` exists.
(b) lint job runs `ruff check` + `ruff format --check` — both proven green.

`main` is now at `164afac`, tree clean, pytest 3/3.

## 3. opencode GitHub agent workflow (this session's third ask)

`.github/workflows/opencode.yml`: triggers on issue/PR comments containing
`/oc` or `/opencode`, runs `anomalyco/opencode/github@latest` with
`opencode/big-pickle` (currently FREE on Zen pricing).
Changes this session: permissions widened to write across all valid scopes
(`models: read` and `id-token: write` are the only values those scopes accept)
**plus** a trigger guard restricting invocation to
OWNER/MEMBER/COLLABORATOR commenters — write power without that guard would let
any stranger's `/oc` comment drive code pushes (prompt injection → repo
takeover). Do not remove the guard without replacing it.
**Still required: `OPENCODE_API_KEY` repo secret** (Settings → Secrets and
variables → Actions). Key source: sign up at `opencode.ai/zen`, open account
details, copy the API key; add credits if prompted (Big Pickle itself is free
per current Zen pricing). Without the secret the workflow fails at its first run.

## 4. Numbers (all from live runs 2026-09-10, or explicit "not yet measured")

Toronto active 206,259 · cleared 435,942 · apps 26,613 · wards 25;
Mississauga permits 34,615 · site plan 1,138 · rezoning 290 · wards 11;
Brampton prod permits 222,263 (DEV 141,886 frozen) · planning 6,989 / 2,100 /
1,451 / 1,031 / 182; Peel boundary 3 · wards 27/26 · CT census 282 · permits
service 684 (liveness only); StatCan 8,270 cubes. Verify 25/25 exit 0; pytest
3/3; CI green on PRs #43 + #44. **Cost: CAD $0.00 / $50.00.**
Eval scores, gold rows, dashboard: not yet measured (nothing built — Phases 2+).

## 5. Phase 2 entry (in order; unchanged from Gate 1 condition iii)

1. Five ADRs before gold SQL: unit-basis mechanism, Peel framing, application
   grain, real-key-only linkage, ward versioning.
2. Toronto permit 32-column field capture before silver SQL assumes columns.
3. PII-drop tests (`CONTACT_*`, Peel councillor columns) + key-stability check
   with first ingestion code. `data-quality-auditor` veto applies throughout.
4. Caledon scope decision (no permit feed exists — scope out explicitly or surface).
5. StatCan per-product `getCubeMetadata` before ingesting any series.

## 6. Needs you — one item

Add the `OPENCODE_API_KEY` secret (source in §3). Nothing else is owed by a human:
Gate 1 is PASS, `main` is green and protected, Phase 2 is unblocked on conditions
owned by agents.

## Rules that do not bend (restated, still enforced)

Every published number comes from a real run with a committed script and output.
Evidence is a file path or command output, never an assertion. No secrets, ever.
No agent marks its own work done (Director reviews + CI + release-manager gate).
