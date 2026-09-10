# Evidence — local verification pass, 2026-09-10

Environment: network-enabled local session (Windows, Python 3.14, httpx 0.28.1).
Unlike the build sandbox (see `2026-09-10-verification.md`) and like the GitHub
runner (see `2026-09-10-runner-discovery.md`), this session has normal internet
access. Every number below was read from a live HTTP response on 2026-09-10.
Nothing here is recalled or inferred.

`scripts/verify_sources.py` against the transcribed `config/sources.yml`:
**25/25 checks pass, exit 0** (24 OK + CMHC reachability-only, which is
`not-adopted` by decision).

---

## 1. Toronto CKAN — both permit feeds resolved, licence unblocked

| Package slug | Resource id | Rows | Columns | Refresh | Last refreshed |
|---|---|---|---|---|---|
| `building-permits-active-permits` | `6d0229af-bc54-46de-9c2b-26759b01dd05` | **206,259** | 32 | Daily | 2026-09-10 10:24:07 |
| `building-permits-cleared-permits` | `a96c0ba4-3026-402b-b09d-5b1268b8f810` | **435,942** | 32 | Daily | 2026-09-10 11:16:05 |
| `development-applications` | `8907d8ed-c515-4ce9-b674-9f8c6eefcf0d` | **26,613** | 25 | Daily | 2026-09-10 07:26:09 |
| `city-wards` | `7672dac5-b383-4d7c-90ec-291dc69d37bf` | **25** | 20 | Semi-annually | 2026-02-20 19:02:48 |

Calls: `GET /api/3/action/package_show?id={slug}` then
`GET /api/3/action/datastore_search?resource_id={id}&limit=0`, `result.total`.

**Licence (was blocking, now resolved).** The CKAN API returns
`license_title: "License not specified"` — but every dataset page on the portal
names the licence explicitly:
`https://open.toronto.ca/dataset/development-applications/`,
`.../building-permits-active-permits/`,
`.../building-permits-cleared-permits/`, `.../city-wards/` all render
`Licence: Open Government Licence - Toronto` linking to
`https://open.toronto.ca/open-data-licence/` (note: `licence` with a C; the
`-license` spelling 404s). Licence text fetched live: worldwide, royalty-free,
perpetual, commercial use allowed; attribution
`Contains information licensed under the Open Government Licence - Toronto`;
excludes Personal Information. The portal page governs; the API field is
incomplete metadata, not an ambiguous licence. Registry records both.

Open question carried to Phase 2: active + cleared overlap in semantics is
unresolved — deduplication across the two resources is a conformance task.

## 2. Brampton `_DEV` question — RESOLVED: ingest production, never `_DEV`

| Feed | URL | Rows | Currency signal |
|---|---|---|---|
| **Production `Building_Permits/MapServer/0`** | `maps1.brampton.ca/arcgis/rest/services/BuildingPermit/Building_Permits/MapServer/0` | **222,263** | `INDATE` up to **2026-09-10** (current) |
| `_DEV` copy `Building_Permits_DEV/FeatureServer/0` | `services3.arcgis.com/rl7ACuZkiFsmDA2g/.../Building_Permits_DEV/FeatureServer/0` | 141,886 | max `ISSUEDATE` **2018-10-17** (frozen ~8 years) |

`_DEV` is the smaller, staler copy in every comparable pair (Minor Variance
6,989 prod vs 5,117 `_DEV`; OPA/ZBA 1,451 vs 1,036; Pre-Consultation 2,100 vs
681; Consent to Sever 1,031 vs 859). The authoritative AGOL item
`Building Permits` (owner `BramptonMaps`, access `City of Brampton`, licence
**CC BY**, id `f1c647c68b0f429a8575f200a803bce8`) points at the production
MapServer; nothing authoritative points at `_DEV`. Brampton's Hub sites are
named `Bramptons GeoHub DEV` / `Bramptons GeoHub UAT` — the suffix is their
staging-environment convention leaking into public names.

**Rule (registry + test):** ingest production `MapServer/0`; no `_DEV`/`_UAT`
URL is registered without written justification (`tests/unit/test_sources_registry.py`).

Production fields (layer 0, 19 fields): `OBJECTID, GIS_ID, ADDRESS, FOLDERRSN,
PERMITNUMBER, SUBDESC, WORKDESC, ISSUEDATE, INDATE, STATUSDESC, PROCESSDATE,
BUILDER, CONTRACTOR, EXPIRYDATE, GFA, SECOND_UNIT, BEDROOMS, STOREYS,
DWELLINGS`. `DWELLINGS` is the unit-count field (semantics net-vs-gross still
to confirm in Phase 2 — assumption A12 stands). `ISSUEDATE` is nullable.
Layer 1 `Building Permits Activity` (2,494,357 rows, per-activity log) is NOT
the permit grain and is not registered as a fact feed.

Brampton planning layers re-confirmed live: Minor Variance 6,989; OPA/ZBA/
Subdivision 1,451 (Pre-Consultation 2,100; Consent to Sever 1,031; Draft Plan
of Condo 182 per runner evidence, transcribed as runner-observed).

Brampton licence: **CC BY** (AGOL items, owner `BramptonMaps`).

## 3. Mississauga — counts re-confirmed, licence read in full

| Layer | Rows (live re-check 2026-09-10) |
|---|---|
| `Issued_Building_Permits/0` | **34,615** |
| `Site_Plan_Applications/0` | **1,138** |
| `Rezoning_Applications/0` | **290** |
| `MississaugaWards/0` | **11** |

**Licence:** City of Mississauga Terms of Use (PDF, 4 pages, fetched live from
`mississauga.maps.arcgis.com/sharing/rest/content/items/961c790805c14d8da258ec91bf4117e3/data`):
worldwide, royalty-free, non-exclusive, revocable licence to use, modify and
distribute for any lawful purpose, with Terms pass-through on redistribution.
Permits public portfolio use.

## 4. Peel — service names corrected, licence read in full

The service is `Municipal_Boundary/FeatureServer` (layer 0 named
`MunicipalBoundary_Peel`) — **not** `MunicipalBoundary_Peel/FeatureServer`
(which returns `Token Required`). Corrected in the registry.

| Service / layer | Rows (live 2026-09-10) |
|---|---|
| `Municipal_Boundary/0` (`MunicipalBoundary_Peel`: Mississauga, Brampton, Caledon; `REG_NAME/MUN_NAME/FULL_NAME`) | **3** |
| `Region_of_Peel_Boundary/0` | 1 |
| `Wards_20222026/0` (fields `WardName/WardNumber/Municipali/Year` + councillor columns) | **27** |
| `Ward_Boundary_2018_2022/0` | **26** |
| `Building_Permits/0` | **684** (not a regional feed — liveness/drift only) |
| `Census_2021_-_Census_Tract_-_Population_and_Dwellings/0` (`CTUID/CTNAME/CSDNAME/Pop16/Pop21/LANDAREA`) | **282** |

**Licence:** `Open Data Licence for The Regional Municipality of Peel,
Version 1.0` (Hub page item `a03e28df41e5423abea4beb34d975961`, read live):
worldwide, royalty-free, perpetual, non-exclusive; commercial use allowed;
attribution `Contains public sector Information made available under The
Regional Municipality of Peel's Open Data Licence - Version 1.0.`

**PII note:** `Ward_Boundary_2018_2022` carries councillor
`FirstName/Phone/email` columns — dropped at bronze→silver like Toronto
`CONTACT_*` (data test in Phase 2).

## 5. StatCan — licence read, catalogue re-confirmed

`getAllCubesListLite` live: **8,270 cubes**. Licence page
`https://www.statcan.gc.ca/en/reference/licence` live: **Statistics Canada
Open Licence** (His Majesty the King in Right of Canada; use indicates
acceptance). Product IDs 34100292 / 34100143 / 34100148 / 98100002 / 98100014 /
98100041 transcribed as **catalogued** (from the live list) — per-product
`getCubeMetadata` still to be read before any series is ingested.

## 6. What is still NOT confirmed

- Field lists for Mississauga/Peel/Brampton-planning layers (counts only this
  pass; `?f=json` field capture is a Phase 2 ingestion task).
- Per-source update cadences for ArcGIS layers (single snapshot cannot show cadence).
- Toronto cleared-vs-active overlap semantics.
- Brampton `DWELLINGS` net-vs-gross semantics (A12).
- Caledon permit feed: none discovered — scope decision owed in Phase 2.
- StatCan per-product metadata.
