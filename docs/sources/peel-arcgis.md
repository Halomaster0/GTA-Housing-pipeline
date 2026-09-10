# Source: Region of Peel — ArcGIS Open Data

**Status: VERIFIED-LIVE (2026-09-10).** Org `services6.arcgis.com/ONZht79c8QWuX759`
confirmed (it is Peel, not Brampton — the Hub mislabel is corrected).
Live confirmation: `docs/sources/evidence/2026-09-10-local-verification.md` §4;
registry: `config/sources.yml` (`peel-*`).

| Layer | Rows (2026-09-10) | Role |
|---|---|---|
| `Municipal_Boundary/0` (`MunicipalBoundary_Peel`: Mississauga, Brampton, Caledon) | 3 | `dim_municipality` seed |
| `Wards_20222026/0` | 27 | `dim_geography` current vintage |
| `Ward_Boundary_2018_2022/0` (26 then vs 27 now — redistricting is real) | 26 | `dim_geography` prior vintage |
| `Census_2021_-_Census_Tract_-_Population_and_Dwellings/0` (282 tracts, `Pop16/Pop21`) | 282 | tract grain + per-capita denominator |
| `Building_Permits/0` | 684 | liveness/drift ONLY — not a permit feed |

Service-name correction: the boundary service is `Municipal_Boundary`
(layer 0 named `MunicipalBoundary_Peel`); `MunicipalBoundary_Peel/FeatureServer`
returns `Token Required`. Licence: **Open Data Licence for The Regional
Municipality of Peel, Version 1.0**. PII: prior-ward layer carries councillor
contact columns — dropped at bronze→silver. Caledon has no permit feed:
scope decision owed in Phase 2.

**Status: UNVERIFIED-BLOCKED.** Raw evidence: `docs/sources/evidence/2026-09-10-verification.md` §4.

| Field | Content |
|---|---|
| Portal + canonical URL | Candidate tried: `https://data.peelregion.ca`. Not reachable — **portal hostname itself unconfirmed.** |
| API type | ArcGIS REST (expected, per build plan pattern). Not confirmed. |
| Auth required | UNVERIFIED |
| Licence | UNVERIFIED — no licence page reached. |
| Update cadence | UNVERIFIED |
| Row count on 2026-09-10 | **UNVERIFIED — reason: `curl: (56) CONNECT tunnel failed, response 403`** on `data.peelregion.ca` and on the ArcGIS Hub discovery API. Cross-checked independently with `WebFetch("https://data.peelregion.ca")`, which returned `{"error_type":"EGRESS_BLOCKED", ...}`. |
| Fields available | UNVERIFIED |
| Fields we need | UNVERIFIED |
| Known gaps | **A structural gap, independent of network access:** Peel Region is the *upper-tier* government; building permits in the GTA are issued by *lower-tier* municipalities — Mississauga, Brampton, and Caledon — not by the Region. Peel Region's own open data is more likely to hold region-wide reference layers (municipal/regional boundaries, possibly regionally-reviewed planning applications) than a `fct_permits`-shaped permit dataset. This is a modelling fact from the structure of Ontario's two-tier municipal government, not something that required a live call to know, and it should be treated as a likely finding even once the portal is reachable. |
| Rate limits / pagination | UNVERIFIED |
| Verified live on | **Not verified.** Attempted 2026-09-10 06:10–06:11 UTC: `curl -sS -w '\nHTTP_STATUS:%{http_code}\n' "https://data.peelregion.ca"`; `curl ... "https://hub.arcgis.com/api/v3/datasets?q=peel%20region%20building%20permits"`. Both `CONNECT tunnel failed, response 403`. |

## What this source can and cannot answer

**Intended role:** likely candidate for the Peel Region rows of `dim_geography` (regional and
lower-tier municipal boundaries) and possibly a cross-check source for `dim_municipality`
(Peel's three constituent lower-tier municipalities: Mississauga, Brampton, Caledon). **Not**
expected to be a `fct_permits` source given the two-tier structure noted above — that
expectation itself needs live confirmation, not just an assumption, since some regions do
publish rolled-up statistics.

**What it cannot answer right now:** everything, because the portal was never reached. If, once
reachable, Peel Region genuinely publishes no permit-level data, that is not a defect in this
source-scout pass — it is expected from Ontario's municipal structure and should be documented
as such in `docs/sources/README.md`, not treated as a missing field to chase.

## Required next step

Confirm `data.peelregion.ca` (or its current replacement) resolves; if it does, look specifically
for regional boundary layers and any region-level planning/development-application datasets
rather than assuming a building-permits dataset exists at this tier.
