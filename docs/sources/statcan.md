# Source: Statistics Canada — Census Profile + Web Data Service (WDS)

**Status: UNVERIFIED-BLOCKED.** Raw evidence: `docs/sources/evidence/2026-09-10-verification.md` §5.

| Field | Content |
|---|---|
| Portal + canonical URL | Census Profile: `https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/index.cfm`. WDS REST base: `https://www150.statcan.gc.ca/t1/wds/rest/`. Main site: `https://www.statcan.gc.ca`. None reachable this session. |
| API type | SDMX-adjacent JSON REST (StatCan's own Web Data Service, not literally SDMX) for tabular data; the Census Profile itself is served through a separate web application whose machine-readable API surface (if any beyond bulk CSV/geography-file downloads) was **not confirmed** this session. |
| Auth required | UNVERIFIED — StatCan's WDS is documented publicly as key-free for read access, but this was not confirmed by an actual unauthenticated call this session. |
| Licence | UNVERIFIED — no licence page reached. Prior general knowledge only (not confirmed live): StatCan data is published under the **Statistics Canada Open Licence** (`https://www.statcan.gc.ca/en/reference/licence`). **Do not treat this as confirmed** until fetched directly. |
| Update cadence | UNVERIFIED — Census Profile data is a fixed 2021 snapshot by definition (quinquennial census); building-permits/housing-starts survey tables are monthly per StatCan's general publication pattern, but the exact cadence for whichever specific table ends up in use is unconfirmed. |
| Row count on 2026-09-10 | **UNVERIFIED — reason: `curl: (56) CONNECT tunnel failed, response 403`** on `www150.statcan.gc.ca`, `www12.statcan.gc.ca`, and `www.statcan.gc.ca`. Cross-checked independently with `WebFetch("https://www150.statcan.gc.ca/t1/wds/rest/getAllCubesListLite")`, which returned `{"error_type":"EGRESS_BLOCKED", ...}`. No `getCubeMetadata` call was possible, so **no product ID for the census-population table or the building-permits/housing-starts table is recorded anywhere in this doc or in `config/sources.yml`**, per the explicit instruction not to trust a remembered product ID. |
| Fields available | UNVERIFIED |
| Fields we need | UNVERIFIED — need population by census subdivision (municipality-level) and by census tract for per-capita normalisation (`dim_geography`), plus, if adopted, a building-permits or housing-starts/completions series as a cross-source reconciliation control total (per the Data Quality Auditor's role card, §5.6). Existence of exact matching tables/columns not confirmed. |
| Known gaps | UNVERIFIED |
| Rate limits / pagination | UNVERIFIED — WDS is documented as unauthenticated with no published hard rate limit for light use, but this is unconfirmed here. |
| Verified live on | **Not verified.** Attempted 2026-09-10 06:11 UTC: `curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"`; `curl ... "https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/index.cfm"`; `curl ... "https://www.statcan.gc.ca"`. All `CONNECT tunnel failed, response 403`. |

## What this source can and cannot answer

**Intended role:** feeds `dim_geography` with population figures for per-capita normalisation
(the "units approved per capita" measure the build plan names explicitly in §5.15 and the
municipal-comparison dashboard page in §5.16). Optionally provides an independent StatCan-side
building-permits or housing-starts series for cross-source reconciliation against the municipal
permit feeds (Data Quality Auditor's "cross-source reconciliation" test, §5.6).

**What it cannot answer right now:** nothing has been confirmed, including which specific WDS
product IDs correspond to the 2021 Census Profile population tables and to a permits/starts
series. This is the source most exposed to the "do not trust a remembered product ID" rule —
StatCan renumbers and retires product IDs across census cycles, so guessing here would be
exactly the mistake the CEO's hard rule exists to prevent.

## Required next step

From a network-enabled environment:
1. `GET getAllCubesListLite` — confirm WDS is reachable and get the full cube catalogue.
2. Search that catalogue (or StatCan's own table-search UI) for the 2021 Census Profile
   population-by-CSD and population-by-CT product IDs, and for a building
   permits / housing starts & completions product ID.
3. `POST getCubeMetadata` with those product IDs — read the real dimension/field structure and
   `nbDatapointsCube` as a count proxy without downloading the full table.
4. Fetch `https://www.statcan.gc.ca/en/reference/licence` directly and quote the licence text.

Only then should real product IDs be added to `config/sources.yml` — never before a live
`getCubeMetadata` response has echoed them back.
