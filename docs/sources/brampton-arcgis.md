# Source: City of Brampton — ArcGIS Open Data (Geohub)

**Status: UNVERIFIED-BLOCKED.** Raw evidence: `docs/sources/evidence/2026-09-10-verification.md` §3.

| Field | Content |
|---|---|
| Portal + canonical URL | Candidates tried: `https://geohub.brampton.ca`, `https://maps.brampton.ca/arcgis/rest/services`. Neither was reachable — **portal hostname itself unconfirmed**. |
| API type | ArcGIS REST (expected, per build plan pattern). Not confirmed against a real layer this session. |
| Auth required | UNVERIFIED |
| Licence | UNVERIFIED — no licence page reached. |
| Update cadence | UNVERIFIED |
| Row count on 2026-09-10 | **UNVERIFIED — reason: `curl: (56) CONNECT tunnel failed, response 403`** on both candidate hosts. No feature layer was located. |
| Fields available | UNVERIFIED |
| Fields we need | UNVERIFIED — cannot confirm permit number, application number, address, ward, use type, unit count, status, or dates exist. |
| Known gaps | The build plan's own example gap ("Brampton lacks unit counts pre-2019", §5.3 template) is **cited there only as an illustrative example of the kind of gap to document — it is not a fact this session confirmed.** Treat it as an open question, not a finding, until read directly from a live schema/data sample. |
| Rate limits / pagination | UNVERIFIED |
| Verified live on | **Not verified.** Attempted 2026-09-10 06:10 UTC: `curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://geohub.brampton.ca"`; `curl ... "https://maps.brampton.ca/arcgis/rest/services"`. Both returned `CONNECT tunnel failed, response 403`. |

## What this source can and cannot answer

**Intended role:** Brampton's rows in `fct_permits` and `fct_applications`; contributes to
`dim_geography` (ward boundaries), `dim_use_type`, `dim_status` once a real schema exists.

**What it cannot answer right now:** everything, including whether `geohub.brampton.ca` is
still the live portal name. **Brampton contributes zero confirmed rows to any gold table.**

## Required next step

Same discovery sequence as Mississauga: confirm the portal hostname, enumerate feature layers,
call `?f=json` for schema and `returnCountOnly=true` for row counts, fetch the licence page —
from a network-enabled environment, since this one cannot reach `geohub.brampton.ca` at all.
