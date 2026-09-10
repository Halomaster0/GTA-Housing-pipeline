# Source: City of Mississauga — ArcGIS Open Data

**Status: UNVERIFIED-BLOCKED.** Raw evidence: `docs/sources/evidence/2026-09-10-verification.md` §2.

| Field | Content |
|---|---|
| Portal + canonical URL | Candidates tried: `https://data.mississauga.ca`, `https://opendata.mississauga.ca`. Neither resolved through the sandbox's network — **the actual current portal hostname is itself unconfirmed**, not just its contents. |
| API type | ArcGIS REST (expected — feature layer `?f=json` for schema, `/query?where=1%3D1&returnCountOnly=true&f=json` for count), per the build plan's stated pattern. Not confirmed against a real layer this session. |
| Auth required | UNVERIFIED |
| Licence | UNVERIFIED — no licence page was reached. Ontario municipal ArcGIS Hub sites commonly publish under an Open Government Licence variant, but which one (Ontario provincial OGL, a municipal-specific OGL, or Esri's default Hub terms) was not read and must not be assumed. |
| Update cadence | UNVERIFIED |
| Row count on 2026-09-10 | **UNVERIFIED — reason: `curl: (56) CONNECT tunnel failed, response 403`** on `data.mississauga.ca`, `opendata.mississauga.ca`, and the ArcGIS Hub discovery API (`hub.arcgis.com/api/v3/datasets?q=mississauga...`). No feature layer was ever located, so no `returnCountOnly` call was possible. |
| Fields available | UNVERIFIED — no layer schema (`?f=json`) was ever retrieved. |
| Fields we need | UNVERIFIED — cannot confirm permit number, application number, address, ward, use/occupancy type, unit count, status, or dates exist in any Mississauga layer. |
| Known gaps | UNVERIFIED |
| Rate limits / pagination | UNVERIFIED — ArcGIS `resultRecordCount`/`resultOffset` pagination is the documented convention, not confirmed against Mississauga's deployment. |
| Verified live on | **Not verified.** Attempted 2026-09-10 06:10 UTC: `curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://data.mississauga.ca"`; `curl ... "https://opendata.mississauga.ca"`; `curl ... "https://hub.arcgis.com/api/v3/datasets?q=mississauga%20building%20permits"`. All returned `CONNECT tunnel failed, response 403`. |

## What this source can and cannot answer

**Intended role:** Mississauga's rows in `fct_permits` and `fct_applications`; contributes to
`dim_geography` if ward-level boundaries are published; contributes candidate values for
`dim_use_type` and `dim_status` once a real schema is read.

**What it cannot answer right now:** everything is open, including which hostname is even the
correct portal. `data.mississauga.ca` and `opendata.mississauga.ca` are both plausible based on
the build plan's naming convention and general municipal open-data conventions, but neither has
been confirmed to exist, let alone to serve the datasets needed. **Mississauga contributes zero
confirmed rows to any gold table.**

## Required next step

From a network-enabled environment: resolve the correct portal hostname (try the two candidates
above, and fall back to the ArcGIS Hub organization search API), locate the building-permits and
development-applications feature layers, call `{layer_url}?f=json` for the field list and
`{layer_url}/query?where=1%3D1&returnCountOnly=true&f=json` for the exact count, and fetch
whatever licence page the portal links before this doc's `UNVERIFIED` rows are replaced.
