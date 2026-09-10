# Evidence — Phase 2 field capture, 2026-09-10

Environment: network-enabled local session (Windows, Python 3.14, stdlib
`urllib`). Every field list below was read from a live API response on
2026-09-10. Nothing here is recalled or inferred. This file closes Gate 1
condition (iii-b): "Toronto permit 32-column field lists captured before
silver SQL assumes columns" — and extends the same capture to every other
Phase 2 feed so no silver SQL assumes any column anywhere.

Row counts were already verified live in
`2026-09-10-local-verification.md` and are not re-asserted here except where
a capture call also returned a total (noted inline).

---

## 1. Toronto CKAN — both permit resources, identical 32-column schema

Call: `GET /api/3/action/datastore_search?resource_id={id}&limit=1`,
`result.fields` (id + type). Totals returned inline: active **206,259**,
cleared **435,942** — unchanged from the verification pass.

| # | Field | Type | Notes |
|---|---|---|---|
| 1 | `_id` | int | CKAN row id, not a business key |
| 2 | `PERMIT_NUM` | text | Business key, e.g. `06 102984 BLD` (suffix = trade: BLD/PLB). Sample: `25 254881 BLD` |
| 3 | `REVISION_NUM` | text | |
| 4 | `PERMIT_TYPE` | text | E.g. `Building Additions/Alterations`, `New Houses`, `Plumbing(PS)` |
| 5 | `STRUCTURE_TYPE` | text | |
| 6 | `WORK` | text | E.g. `Interior Alterations`, `New Building`, `Building Permit Related(PS)` |
| 7 | `STREET_NUM` | text | |
| 8 | `STREET_NAME` | text | |
| 9 | `STREET_TYPE` | text | |
| 10 | `STREET_DIRECTION` | text | |
| 11 | `POSTAL` | text | |
| 12 | `GEO_ID` | text | |
| 13 | `WARD_GRID` | text | Grid ref (e.g. `N1731`), not a ward number |
| 14 | `APPLICATION_DATE` | date | Bare date |
| 15 | `ISSUED_DATE` | date | Bare date |
| 16 | `COMPLETED_DATE` | date | Bare date, nullable (null observed on open permits) |
| 17 | `STATUS` | text | E.g. `Inspection` (observed); full vocabulary uncaptured |
| 18 | `DESCRIPTION` | text | Free text — untrusted input at query time (risk R7) |
| 19 | `CURRENT_USE` | text | |
| 20 | `PROPOSED_USE` | text | |
| 21 | `DWELLING_UNITS_CREATED` | **text** | Nullable; `"0"` and null both observed. Unit semantics net-vs-gross unresolved (A12 stands) |
| 22 | `DWELLING_UNITS_LOST` | **text** | Nullable; `"0"` and null both observed |
| 23 | `EST_CONST_COST` | text | Construction value as text — cast in silver with failure logging |
| 24 | `ASSEMBLY` | float8 | Floor-area breakdown component |
| 25 | `INSTITUTIONAL` | float8 | Floor-area breakdown component |
| 26 | `RESIDENTIAL` | float8 | Floor-area breakdown component |
| 27 | `BUSINESS_AND_PERSONAL_SERVICES` | float8 | Floor-area breakdown component |
| 28 | `MERCANTILE` | float8 | Floor-area breakdown component |
| 29 | `INDUSTRIAL` | float8 | Floor-area breakdown component |
| 30 | `INTERIOR_ALTERATIONS` | float8 | Floor-area breakdown component |
| 31 | `DEMOLITION` | float8 | Floor-area breakdown component |
| 32 | `BUILDER_NAME` | text | Person/org name — assess for PII handling in silver |

Active-vs-cleared overlap probe: one active-sample permit (`06 102984 BLD`)
filtered against the cleared resource returned **0 matches** — consistent
with (not proof of) disjoint resources. Full dedup is a Phase 2 conformance
task (ADR-0005 scope); no claim is made here beyond this single probe.

Sample rows (active, 2026-09-10): `06 102984 BLD` (alterations, created 0 /
lost 0), `06 102984 PLB` (same building, related trade permit, units null),
`25 254881 BLD` (new houses, created 4 / lost 0, issued 2026-03-03).

## 2. Toronto development applications — 25 columns; grain is per-address, not per-application

Call: same pattern, resource `8907d8ed-c515-4ce9-b674-9f8c6eefcf0d`
(total 26,613 inline, unchanged).

Fields: `_id` (int), `APPLICATION_TYPE`, `APPLICATION#`, `STREET_NUM`,
`STREET_NAME`, `STREET_TYPE`, `STREET_DIRECTION`, `POSTAL`,
`DATE_SUBMITTED` (**timestamp**), `STATUS`, `X`, `Y` (projected coords as
text), `DESCRIPTION`, `REFERENCE_FILE#`, `FOLDERRSN` (**text**),
`WARD_NUMBER`, `WARD_NAME`, `COMMUNITY_MEETING_DATE` (timestamp),
`COMMUNITY_MEETING_TIME`, `COMMUNITY_MEETING_LOCATION`, `APPLICATION_URL`,
`CONTACT_NAME`, `CONTACT_PHONE`, `CONTACT_EMAIL` (PII — silver-drop),
`PARENT_FOLDER_NUMBER`.

Grain finding (load-bearing for ADR-0005): `limit=100` returned **100 rows
for 47 distinct `APPLICATION#`**. Filter on `22 114201 WET 05 OZ` returned
**6 rows** differing only by street address (`5A/7/1/3/5/9 OXFORD DR`) and
X/Y — same type, status (`OMB Appeal`), submitted date, FOLDERRSN
(`5060317`). **The resource grain is one row per application-address, not
one row per application.** Counting rows as applications overstates by ~2x
on this sample. No unit-count field. Exactly one lifecycle date
(`DATE_SUBMITTED`) — no decision date. `REFERENCE_FILE#` and
`PARENT_FOLDER_NUMBER` observed null on sampled rows.

## 3. Mississauga permits — 24 fields

Call: `.../Issued_Building_Permits/FeatureServer/0?f=json`, `fields`
(name + type).

`OBJECTID` (OID), `BP_NO` (string, business key), `STATUS` (string),
`ADDRESS`, `UNIT_NO`, `DESCRIPTION` (free text), `SCOPE`, `FILE_TYPE`,
`BLDG_TYPE`, `APP_DETAIL`, `APPL_AREA` (double), `STOREYS` (double),
`EST_CON_VALUE` (integer), `RES_UNITS` (**integer** — unit count),
`DEMO` (string), `POSTAL_CODE`, `BLDG_NO`, `WARD` (small integer),
`ZAREA`, `LATITUDE`/`LONGITUDE` (double), `APPLICATION_DATE`,
`ISSUE_DATE`, `COMPLETE_DATE` (dates). No `FOLDERRSN` — linkage-relevant
(ADR-0006).

## 4. Mississauga site plan + rezoning — identical 34-field schema

Calls: `.../Site_Plan_Applications/FeatureServer/0?f=json` and
`.../Rezoning_Applications/FeatureServer/0?f=json`.

Shared fields: `OBJECTID`, `PLNG_APP_ID` (integer), `APP_FILE_NO` (string,
business key), `TYPE_DESC`, `SUBTYPE_CODE`, `YEAR`, `APPLICATION_NO`
(integer), `CATEGORY_DESC`, `GENERAL_LOCATION`, `DESCRIPTION`,
`SITE_ADDRESS`, `APPLICATION_DATE`, `APPROVAL_DATE` (**decision date —
exists here**, unlike Toronto), `APPLICANT`, `PLANNER` (person names —
flag for PII review in silver), `RES_DET`, `RES_SEMIS`, `RES_ROWS`,
`RES_APTS`, `RES_OTH_APTS` (integers — unit breakdown),
`ICI_OFFICE`, `ICI_INDUST`, `ICI_ICI_FLEX`, `ICI_RETAIL`, `ICI_CC`,
`ICI_INSTITUT`, `ICI_OTHER` (doubles — non-res GFA breakdown),
`TOTAL_RES_UNITS` (integer — unit count), `TOTAL_NON_RES_GFA` (double),
`WARD` (small integer), `CHAR_AREA`, `SIMPLE_STATUS`,
`Shape__Area`/`Shape__Length` (geometry measures).

## 5. Brampton production permits — 20 fields live

Call: `https://maps1.brampton.ca/arcgis/rest/services/BuildingPermit/Building_Permits/MapServer/0?f=json`
(layer name `Building Permits`; description: "Building Permits for
addresses within the City of Brampton. Updated using a live service.").

`OBJECTID`, `GIS_ID` (double), `ADDRESS`, `FOLDERRSN` (**double** — cf.
Toronto text), `PERMITNUMBER` (string, business key), `SUBDESC`,
`WORKDESC` (free text), `ISSUEDATE` (date, nullable — unissued permits),
`INDATE` (date), `STATUSDESC`, `PROCESSDATE`, `BUILDER`, `CONTRACTOR`
(names — PII review), `EXPIRYDATE`, `GFA` (**string** — cast in silver),
`SECOND_UNIT`, `BEDROOMS`, `STOREYS`, `DWELLINGS` (**string** — unit
count; net-vs-gross unresolved, A12 stands), `SHAPE` (geometry).
(Prior evidence counted 19 excluding the geometry field; 20 including it.
No discrepancy.)

## 6. Brampton Minor Variance (planning layer 8) — 16 fields, no units, no FOLDERRSN

Call: `.../Planning_Land_Use_Development/FeatureServer/8?f=json`.

`FILE_NUMBER` (string, business key), `REGIONAL_NUMBER`,
`LOCATION`, `DATE_RECEIVED` (date), `APPLICATION_TYPE`,
`APPLICATION_TITLE`, `DESCRIPTION`, `STATUS`, `CITY_PLANNER`,
`PROPOSAL_DESCRIPTION`, `AGENT_COMPANY`, `APPLICANT_COMPANY`,
`WARD` (string), `POLY_ID` (OID), `Shape__Area`/`Shape__Length`.
No dwelling-unit field, no `FOLDERRSN`, no decision date on this layer.
(Other planning layers 5/7/9/10 share the service; per-layer field capture
repeats at ingestion time and any divergence is a drift failure, not a
silent assumption.)

## 7. Peel census tracts — 20 fields

Call: `.../Census_2021_-_Census_Tract_-_Population_and_Dwellings/FeatureServer/0?f=json`
(layer `Census2021_CT_PopulationDwelling`).

`OBJECTID`, `CTUID` (string, tract key), `DGUID`, `CTNAME`,
`LANDAREA` (double), `PRUID`, `CDUID`, `CDNAME`, `CSDUID`, `CSDNAME`,
`Pop16`/`Pop21` (integers), `PopChg16_21` (double), `Dwell21`,
`Dwell_UR21` (integers), `AreaKM2_21`, `PopDen21`, `DwellUR_Den21`
(doubles), `Shape__Area`/`Shape__Length`. Per-capita denominators
confirmed present (`Pop21`, `Dwell21`).

## 8. StatCan — per-product metadata read live (closes Phase 2 entry item 5 for the load-bearing products)

Call: `POST https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata` with
`[{"productId": ...}]`, 2026-09-10. All four return `status: SUCCESS`.

| Product | Title | Status | Period | Series | Dimensions (members) |
|---|---|---|---|---|---|
| 34100292 | Building permits, by type of structure and type of work | CURRENT | 2018-01 → 2026-06, monthly | 375,864 (38.3M datapoints) | Geography 66 · Type of building 89 · Type of work 22 · Variables 5 · Seasonal adjustment/value type 4 |
| 34100143 | CMHC housing starts, under construction and completions (via StatCan) | CURRENT | 1948-01 → 2026-07, monthly | 220 | Geography 22 · Housing estimates 3 · Type of unit 6 |
| 98100002 | Population and dwelling counts: Canada and census subdivisions | CURRENT | 2021-01 (census snapshot) | 1 | Geographic name 5,468 · Counts 13 |
| 98100014 | Population and dwelling counts: CMAs, tracted CAs and census tracts | CURRENT | 2021-01 (census snapshot) | 1 | Geographic name 6,297 · Counts 7 |

Reconciliation note: 34100292's Geography dimension (66 members) must
contain the municipal/CMA members used as control totals — member
selection is an ingestion-time task against these dimensions, not assumed
here. 38.3M datapoints means municipal ingestion pulls selected
vectors/series only, never the full cube.

## 9. Still not confirmed (carried, not blocking entry)

- Full STATUS vocabularies per source (samples only).
- ArcGIS update cadences (single snapshot cannot show cadence).
- Brampton `DWELLINGS` / Toronto `DWELLING_UNITS_CREATED/LOST` /
  Mississauga `RES_UNITS` net-vs-gross semantics (A12 — unresolved by
  schema alone; needs documentation or a hand-labelled sample in Phase 2).
- Whether Mississauga `APPLICANT`/`PLANNER` and Brampton
  `BUILDER`/`CONTRACTOR` name fields identify individuals (PII review at
  silver time; Toronto `CONTACT_*` and Peel councillor columns are already
  ruled drops).
- Toronto cleared-vs-active full dedup (single-probe evidence in §1 only).

## 10. First `--all` run key-resolution findings, 2026-09-10 (closes Gate 1 condition iii-c)

`python -m src.ingest --all` landed 14/20 feeds clean on the first attempt
(942,241 rows). The 6 non-clean results were all caught by the pipeline's own
guards — no silent corruption — and each resolved to a proven rule below.

**Toronto permits: the row key is (PERMIT_NUM, REVISION_NUM), not
PERMIT_NUM.** Active showed 22,285 duplicate `PERMIT_NUM` over 206,259 rows;
cleared 45,177 over 435,942. Bronze inspection: duplicates are revisions of
the same permit (`25 254881 BLD` rev `00` Inspection → rev `01` Revision
Issued, new dates). Spec amended to composite unique key. Silver rule
(follows): gold permit grain keeps the latest `REVISION_NUM` per
`PERMIT_NUM`; revision history is not modelled in v1.

**Mississauga: two genuine source-side duplicates.** `HOUSDEMO 18-3651`
(permits, OBJECTID 3067 vs 3069) and `SP 24/2` (site plan, OBJECTID 594 vs
1096, same `PLNG_APP_ID` 181783) are byte-identical rows published twice
under different OBJECTIDs. Spec amended to composite keys (`BP_NO` /
`APP_FILE_NO` + `OBJECTID`, unique). Silver rule (follows): dedup keeping
min OBJECTID, logging dropped counts per run.

**ArcGIS paging, two fixes from live behaviour.** (1) Brampton production
MapServer truncates pages at maxRecordCount=1,000 with no error — a short
page is not the last page; the connector now pages `oid > last_oid` ranges
to the reported total. (2) The OID field is not always `OBJECTID`
(Brampton planning layers: `POLY_ID`); the connector reads the layer
definition for the `esriFieldTypeOID` field first. Peel `Building_Permits`
and all five Brampton planning layers failed loud (400) on the first run
and are re-pulled under the fixed connector.

**StatCan series pulls: HTTP 406.** `getDataFromCubePidCoordAndLatestNPeriods`
with coordinate `45.1.1.1.1` (product 34100292, latestN 3) returned HTTP 406
twice (with and without Accept/User-Agent headers) while `getCubeMetadata`
succeeds from the same client. Series specs stay empty; metadata lands as
bronze `metadata.json`. First successful series pull is owed before any
reconciliation depends on StatCan series.

**StatCan geography is CMA-level.** 34100292's Geography dimension (66
members) carries `Toronto, Ontario` (CMA, member 45) — no
Mississauga/Brampton/Peel municipal members. Municipal control totals come
from census products (98100002 CSD / Peel CT layer), not from 34100292.

## 11. Second-round key findings, 2026-09-10 (same session)

**Toronto permits: the row key is (PERMIT_NUM, REVISION_NUM, PERMIT_TYPE).**
Residual duplicates on the composite (259 active / 3,476 cleared) are
conditional-vs-definitive permit pairs: `17 224333 STS` rev `00` exists once
as `Drain and Site Service` and once as `Conditional Permit` (different
application/issue/completion dates). Spec amended to the triple composite.
Silver rule (follows): gold keeps one row per `PERMIT_NUM` — prefer the
non-conditional row, then max `REVISION_NUM`; conditional rows are
precursors, not separate permits.

**Brampton permits: the row key is (PERMITNUMBER, FOLDERRSN).** 957
duplicate `PERMITNUMBER` over 222,274 rows are sub-permits under one folder
number: `10-124296-000-00` spans `New Shell Building` (FOLDERRSN 325203,
DWELLINGS 1) and `Interior/Unit Finish` (FOLDERRSN 325204, DWELLINGS null).
FOLDERRSN here is Brampton-internal row serial — same field name as
Toronto's, different key space (reinforces ADR-0006: never matched
cross-municipally). Silver rule (follows): unit sums must account for
shell-vs-finish double-counting (finish rows carry null DWELLINGS;
shell rows carry the count) — recorded here, enforced in silver tests.

**Peel `Building_Permits` resolved: an aggregate stats table, not permits.**
Live `?f=json`: Year / Quarter / Geography / Single_Units / Double_Units /
Row_Units / Apartment_Units / Total_Units / value fields / FID (OID). Grain
is (Year, Quarter, Geography); spec key amended accordingly. The
"unresolved grain" note in `config/sources.yml` is superseded by this
paragraph — the MUST-NOT-feed-fct_permits rule stands unconditionally.

## 12. Third-round key findings, 2026-09-10 (same session)

**No-connector-resume rule.** A failed run can land complete part files
before failing at drift/key checks; resuming from a stored offset then
appends duplicates (observed: peel-building-permits re-pulled 0 rows onto a
landed partition and tripped a false drift). Same-date reruns now always
replace the partition wholesale; checkpoints are progress observability
only. The false drift file was deleted, not kept.

**Brampton residual dupes are re-processed rows.** 4 duplicate
(PERMITNUMBER, FOLDERRSN) pairs are byte-identical except OBJECTID and
PROCESSDATE (e.g. `20-231851-000-00` × 1280107.0, PROCESSDATE differing by
~7 weeks). Spec key is now (PERMITNUMBER, FOLDERRSN, OBJECTID) unique with
an observe tail on (PERMITNUMBER, FOLDERRSN). Silver rule (follows): dedup
keeping min OBJECTID.

**Toronto residual dupes are double-entered rows.** 9 active / 15 cleared
duplicate (PERMIT_NUM, REVISION_NUM, PERMIT_TYPE) triples are byte-identical
except `_id` and BUILDER_NAME (`24 123058 BLD` rev `00`: MICHAEL YEE vs ADAM
TAO — a builder reassignment double-entered). Spec key is now the triple +
`_id` (CKAN row identity, unique by construction) with an observe tail on
the triple. Silver rule (follows): dedup keeping min `_id`, logging the
dropped builder names for the data-quality report.
