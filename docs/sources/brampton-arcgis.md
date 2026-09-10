# Source: City of Brampton — ArcGIS Open Data (Geohub + production MapServer)

**Status: VERIFIED-LIVE (2026-09-10), `_DEV` question RESOLVED.**
Live confirmation: `docs/sources/evidence/2026-09-10-local-verification.md` §2;
registry: `config/sources.yml` (`brampton-*`).

**Decision: ingest production `maps1.brampton.ca/.../Building_Permits/MapServer/0`
(222,263 rows, current — `INDATE` 2026-09-10). NEVER `Building_Permits_DEV`
(141,886 rows, frozen at `ISSUEDATE` 2018-10-17).** The AGOL `Building Permits`
item (owner `BramptonMaps`, licence CC BY) points at production; nothing
authoritative points at `_DEV`. Guard test: `tests/unit/test_sources_registry.py`.

| Layer | Rows (2026-09-10) |
|---|---|
| Production permits `MapServer/0` (fields incl. `PERMITNUMBER`, `DWELLINGS`, `ISSUEDATE` nullable) | 222,263 |
| Minor Variance (`Planning_Land_Use_Development/8`) | 6,989 |
| OPA/ZBA/Subdivision (`.../9`) | 1,451 |
| Pre-Consultation (`.../10`) | 2,100 |
| Consent to Sever (`.../5`) | 1,031 |
| Draft Plan of Condo (`.../7`) | 182 |

Licence: **CC BY** (AGOL items, owner `BramptonMaps`, City of Brampton).
Outstanding: `DWELLINGS` net-vs-gross semantics (A12, Phase 2).

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
