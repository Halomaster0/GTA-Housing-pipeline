# Source: City of Toronto — CKAN Open Data

**Status: VERIFIED-LIVE (2026-09-10).** Supersedes the UNVERIFIED-BLOCKED note
below, which describes the sandbox session only. Live confirmation:
`docs/sources/evidence/2026-09-10-local-verification.md` §1; registry:
`config/sources.yml` (`toronto-*`).

| Dataset | Rows (2026-09-10) | Licence |
|---|---|---|
| Building Permits — Active (`6d0229af-…`) | 206,259 | Open Government Licence - Toronto |
| Building Permits — Cleared since 2017 (`a96c0ba4-…`) | 435,942 | Open Government Licence - Toronto |
| Development Applications (`8907d8ed-…`) | 26,613 | Open Government Licence - Toronto |
| City Wards (`7672dac5-…`) | 25 | Open Government Licence - Toronto |

Licence note: the CKAN API returns `License not specified`; every dataset page
on `open.toronto.ca` names `Open Government Licence - Toronto`. The portal page
governs. Outstanding: active-vs-cleared overlap semantics (Phase 2 conformance).

**Status: UNVERIFIED-BLOCKED.** Every field below marked UNVERIFIED reflects a live call that
was attempted and failed at the network layer this session — not a dataset that was checked and
found missing. Raw evidence: `docs/sources/evidence/2026-09-10-verification.md` §1.

| Field | Content |
|---|---|
| Portal + canonical URL | Portal front end: `https://open.toronto.ca`. API base: `https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/`. Neither was reachable this session. |
| API type | CKAN (Action API v3) |
| Auth required | UNVERIFIED — Toronto's CKAN API is documented elsewhere as not requiring a key for read access, but this could not be confirmed by an actual unauthenticated call this session. |
| Licence | UNVERIFIED — could not fetch the licence page. Prior general knowledge only (not confirmed live): Toronto's open data catalogue publishes under an **"Open Government Licence – Toronto"**, linked from `https://open.toronto.ca/open-data-license/`. **Do not treat this as confirmed** until that URL has actually been fetched and its text read. |
| Update cadence | UNVERIFIED |
| Row count on 2026-09-10 | **UNVERIFIED — reason: `curl: (56) CONNECT tunnel failed, response 403` on every attempt** (both direct `curl` through the sandbox agent proxy and an independent `WebFetch` call, which returned `EGRESS_BLOCKED`). No package list, no resource id, no `datastore_search` count was ever obtained. |
| Fields available | UNVERIFIED — no schema was returned by any call. |
| Fields we need | UNVERIFIED — cannot state whether permit number, application number, address, ward, ward id, ward centroid, use type/description, unit count, status, submitted date, decision date, or issued date exist, because no resource was ever reached. |
| Known gaps | UNVERIFIED — cannot state any known gap (e.g. field coverage by year) without having seen the data. |
| Rate limits / pagination | UNVERIFIED — CKAN's `package_search`/`datastore_search` conventionally page via `rows`/`start`, but this is from general API knowledge, not confirmed against Toronto's deployment this session. |
| Verified live on | **Not verified.** Attempted 2026-09-10 06:09–06:11 UTC. Exact calls attempted (all failed identically): `curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_search?q=permit&rows=50"` (and the same with `q=development%20application`, `q=ward`, `q=zoning`), plus `curl ... "https://open.toronto.ca/dataset/building-permits-active-permits/"`. Full transcript in the evidence log. |

## What this source can and cannot answer

**Intended role in the star schema** (per `docs/build-plan.md` §2): the primary source for
Toronto's half of `fct_permits` (building permits — active and issued/cleared) and
`fct_applications` (development applications), plus the Toronto rows of `dim_geography`
(via ward boundaries) and a likely contributor to `dim_use_type` (permit/application use or
work-type classification) and `dim_status` (permit/application status codes).

**What it cannot answer right now:** nothing, because nothing was retrieved. This is not a case
of the data existing but lacking a specific column — the entire question of whether Toronto's
CKAN API is reachable, what datasets it currently publishes under what slugs, and what those
datasets' schemas look like is open. Until this is re-run from a network-enabled environment,
**Toronto contributes zero confirmed rows to any gold table.**

## Required next step

Re-run, in order, from an environment with real internet access:
1. `GET /api/3/action/package_search?q=building%20permits&rows=50` and the equivalent for
   `development application`, `ward`, `zoning` — read the actual dataset names/slugs back.
2. `GET /api/3/action/package_show?id={slug}` for each relevant dataset — read the resource
   list and each resource's `id` (the datastore resource UUID) and declared fields.
3. `GET /api/3/action/datastore_search?resource_id={id}&limit=0` — read `result.total` for an
   exact row count, and `result.fields` for the real field list with types.
4. Fetch `https://open.toronto.ca/open-data-license/` directly and quote the licence text.

Only after all four steps succeed should this doc's "UNVERIFIED" rows be replaced with real
values, each cited to the exact call that produced it.
