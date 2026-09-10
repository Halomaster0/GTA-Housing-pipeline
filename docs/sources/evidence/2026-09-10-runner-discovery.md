# Evidence — runner-side source discovery, 2026-09-10

The development sandbox cannot reach any data source (see
`2026-09-10-verification.md`). These results come from a GitHub Actions runner via
`.github/workflows/source-discovery.yml`, which has normal internet access.

Everything below was read from a live HTTP response. Nothing here is recalled or inferred.

---

## Confirmed: Toronto CKAN

Portal API base: `https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action`

### `development-applications`

| Field | Value |
|---|---|
| Datastore resource id | `8907d8ed-c515-4ce9-b674-9f8c6eefcf0d` |
| **Total rows** | **26,613** |
| Columns | 25 |
| Refresh cadence | Daily |
| Last refreshed | 2026-09-10 07:26:09 |
| **Licence** | **`License not specified`** — see escalation below |

Columns, with types exactly as CKAN reports them:

```
_id int · APPLICATION_TYPE text · APPLICATION# text · STREET_NUM text
STREET_NAME text · STREET_TYPE text · STREET_DIRECTION text · POSTAL text
DATE_SUBMITTED timestamp · STATUS text · X text · Y text · DESCRIPTION text
REFERENCE_FILE# text · FOLDERRSN text · WARD_NUMBER text · WARD_NAME text
COMMUNITY_MEETING_DATE timestamp · COMMUNITY_MEETING_TIME text
COMMUNITY_MEETING_LOCATION text · APPLICATION_URL text
CONTACT_NAME text · CONTACT_PHONE text · CONTACT_EMAIL text
PARENT_FOLDER_NUMBER text
```

### `city-wards`

| Field | Value |
|---|---|
| Datastore resource id | `7672dac5-b383-4d7c-90ec-291dc69d37bf` |
| **Total rows** | **25** |
| Columns | 20 |
| Refresh cadence | Semi-annually |
| Last refreshed | 2026-02-20 19:02:48 |
| Licence | not returned by the API |

Carries `DATE_EFFECTIVE` and `DATE_EXPIRY` timestamps, plus `AREA_SHORT_CODE`,
`AREA_LONG_CODE`, `AREA_NAME` and a `geometry` column. The package also publishes
historical 44-ward and 47-ward boundary files alongside the current 25-ward model.

---

## Three findings that change the design

### 1. The Toronto development applications licence is unspecified — blocking

CKAN returns `license_title: "License not specified"` and no licence URL. The project
rule is that a source's licence must explicitly permit public reuse, and that an
unconfirmed licence blocks portfolio use exactly like a restrictive one
(`docs/build-plan.md` §5.3, §5.21).

This is not a formality. The dataset is the primary feed for `fct_applications`.

**Owner:** `source-scout` and `security-and-licence-reviewer`. **Escalated to the CEO.**
Resolution path: check the dataset's page on `open.toronto.ca` for a licence statement
outside the API payload, and check the City of Toronto Open Data licence that governs
the portal as a whole. Do not ingest into a public artifact until the licence is named.

### 2. The dataset carries personal information

`CONTACT_NAME`, `CONTACT_PHONE` and `CONTACT_EMAIL` identify individual applicants and
agents. §5.21 is unambiguous: a field that could identify an individual is dropped at
bronze to silver.

**Rule for `transform-engineer`, to be enforced by a test, not a convention:** these three
columns are dropped in the bronze-to-silver step and never appear in silver, gold, the
vector index, the semantic model, or any LLM prompt. A data test in `tests/data/` must
fail if any of them reaches silver.

This also matters for the AI layer: free-text `DESCRIPTION` is untrusted input flowing
into prompts (risk R7), and the contact columns must never be retrievable.

### 3. The applications dataset cannot answer the velocity questions on its own

There is exactly one date column describing the application's own lifecycle:
`DATE_SUBMITTED`. There is a `STATUS` but no decision date, no approval date, and no
issued date. There is also **no dwelling-unit count**.

Consequences, which the schema design and the golden question set must both absorb:

- "How has application-to-permit time changed since 2019" is not answerable from this
  dataset alone. It needs a join to building permits on a shared address or folder key,
  and that join has not been proven to exist.
- Any per-capita or per-unit measure needs unit counts from somewhere else, or must be
  restricted to permit counts rather than unit counts.
- Without a decision date, status is a point-in-time snapshot. Slowly-changing-dimension
  Type 2 on application status is only possible if the pipeline snapshots the daily
  refresh itself and builds the history going forward. It cannot be reconstructed
  retroactively.

The last point is worth stating plainly: **if the project wants application status
history, it must start capturing daily snapshots now.** Every day of delay is a day of
history that cannot be recovered later.

---

## Discovery methods that failed, and what replaced them

**ArcGIS Hub free-text search does not scope to a place.** Querying
`Mississauga building permit` returned datasets from Faribault County, Nashville and
Atlanta. The only useful output was the municipal org ids:

- City of Mississauga: `services6.arcgis.com/hM5ymMLbxIyWTjn2`
- City of Brampton: `services3.arcgis.com/rl7ACuZkiFsmDA2g` and `services6.arcgis.com/ONZht79c8QWuX759`
- Regional Municipality of Peel: `regionofpeel.maps.arcgis.com` (org id not yet resolved)

Discovery now walks each org's REST service directory instead.

**StatCan rejects POST from the runner.** Every `getCubeMetadata` POST returned a
connection reset or a read timeout, while a GET endpoint answered 200 in the same run.
Discovery now uses `getAllCubesListLite` over GET and filters locally, which also removes
any need to recall a product id.

---

## Second discovery pass — ArcGIS by org directory, StatCan over GET

Both replacement methods worked.

### Peel Region publishes what the project needs, and it is not where the plan expected

Org: `services6.arcgis.com/ONZht79c8QWuX759`. The earlier hub search mislabelled this org
as City of Brampton; its dataset list is unambiguously Regional Municipality of Peel.

Confirmed from live responses:

| Layer | Rows | Note |
|---|---|---|
| `MunicipalBoundary_Peel` layer 0 | **3** | Mississauga, Brampton, Caledon. Fields: `REG_NAME`, `MUN_NAME`, `FULL_NAME`, plus shape area and length. |
| `Building_Permits` (FeatureServer) | not yet counted | The service exists. Its layer list was not resolved in this pass. |
| `Lot Fabric Improved` | 1,841 | parcel geometry |
| `Neighbourhood Information Tool 2021` | 286 | |
| `Growth Forecasts 2016-2041` | 135 regional, 4 municipal | |
| `Ward Boundary 2018-2022` | 32 | |

Two consequences:

1. **`MunicipalBoundary_Peel` is the natural seed for `dim_municipality`** — a three-row
   authoritative list of the lower-tier municipalities with a region name attached.
2. **The Peel question from the schema draft is half-answered.** Peel is an upper-tier
   municipality and does not itself issue permits, but it *publishes* a `Building_Permits`
   service, presumably aggregating its lower-tier municipalities. Resolve whether that
   service is the aggregate — if it is, it may be a better feed than scraping Mississauga
   and Brampton separately, and it changes the grain of `fct_permits`. Count its rows and
   read its fields before deciding.

### StatCan: confirmed product ids, and CMHC is solved

`getAllCubesListLite` returned **8,270 cubes** over GET. The ids below are copied from that
response, not recalled. `archived=2` means active; `archived=1` means inactive.

| Product id | Title | Coverage | State |
|---|---|---|---|
| **34100292** | Building permits, by type of structure and type of work | 2018-01 to 2026-06 | active |
| **34100143** | CMHC housing starts, under construction and completions, centres 10,000+, provinces and selected CMAs | 1948-01 to 2026-07 | active |
| **34100148** | CMHC housing starts by dwelling and market type, CMAs and large CAs | 1988-06 to 2026-07 | active |
| **98100002** | Population and dwelling counts: Canada and census subdivisions (municipalities) | 2021 census | active |
| **98100014** | Population and dwelling counts: CMAs, tracted CAs and census tracts | 2021 census | active |
| **98100041** | Structural type of dwelling and household size, census subdivisions | 2021 census | active |

Note that `34100066` and `34100285`, both "Building permits, by type of structure and type
of work", are **inactive**. `34100292` is the live successor. This is exactly the trap the
rule against recalling product ids exists to prevent: an id that was correct two years ago
now returns a frozen series.

**The CMHC question is resolved without adopting CMHC as a source.** Statistics Canada
republishes CMHC housing starts, completions and under-construction counts as tables
34100143 and 34100148, under the StatCan licence and through a documented API. That removes
the concern in `cmhc.md` that the Housing Market Information Portal offers only an
interactive report builder, which would have made ingestion a scrape and violated the
project's own non-goal. Recommend: leave CMHC NOT ADOPTED as a direct source and take the
same data from StatCan.

`98100002` is the per-capita denominator for `dim_municipality`; `98100014` is the census
tract grain for `dim_geography`.

### Still unresolved after two passes

- Toronto building permit datasets — the `package_show` output for the permit packages
  scrolled out of the retained log. Re-run with `--only toronto`.
- Mississauga's and Brampton's own permit and application layers, and their row counts.
- Peel's `Building_Permits` layer list, row count and fields.
- Every licence except the two Toronto datasets already recorded.

---

## Third discovery pass — the real permit and application feeds

199 facts collected from live responses. The load-bearing ones:

### City of Mississauga — `services6.arcgis.com/hM5ymMLbxIyWTjn2`

| Layer | Rows | Role |
|---|---|---|
| `Issued_Building_Permits/0` "Building Permits" | **34,615** | primary `fct_permits` candidate |
| `Growth_Management_–_Issued_Building_Permits/0` "IssuedBldgPerms" | **9,030** | a curated subset, not the same thing |
| `Site_Plan_Applications/0` | **1,138** | `fct_applications` |
| `Rezoning_Applications/0` | **290** | `fct_applications` |
| `Growth_Management_–_Active_Development_Applications/0` | **214** | active only |
| `OPA_and_Rezonings/0` | **48** | |
| `MississaugaWards/0` | **11** | `dim_geography` |
| `Parcel/0` | 166,923 | parcels — see the duplication warning below |

### City of Brampton — `services3.arcgis.com/rl7ACuZkiFsmDA2g`

| Layer | Rows | Role |
|---|---|---|
| `Building_Permits_DEV/0` "Building Permits" | **141,886** | see the `_DEV` warning below |
| `Planning_Land_Use_Development/8` "Minor Variance" | **6,989** | `fct_applications` |
| `Planning_Land_Use_Development/10` "Pre Consultation" | **2,100** | |
| `Planning_Land_Use_Development/9` "OPA ZBA Subdivision" | **1,451** | |
| `Planning_Land_Use_Development/5` "Consent to Sever" | **1,031** | |
| `Planning_Land_Use_Development/7` "Draft Plan of Condo" | **182** | |
| `Archived_Planning_Application_Layers/7` "Development Applications" | **0** | archived and empty |

### Regional Municipality of Peel — `services6.arcgis.com/ONZht79c8QWuX759`

| Layer | Rows | Role |
|---|---|---|
| `Building_Permits/0` | **684** | not a regional permit feed — see below |
| `Wards_20222026/0` | **27** | current ward vintage |
| `Ward_Boundary_2018_2022/0` | **26** | prior ward vintage |
| `Census2016_Wards20182022_Dwellings/1` | **26** | dwelling counts by ward |
| `MunicipalBoundary_Peel/0` | **3** | Mississauga, Brampton, Caledon |

---

## Findings four through seven

### 4. Brampton publishes `_DEV` and `_UAT` copies of its layers publicly, with different row counts

This is the most dangerous thing found so far, because it fails silently.

| Layer | production | `_DEV` | `_UAT` |
|---|---|---|---|
| Minor Variance | 6,989 | 5,117 | 6,046 |
| OPA ZBA Subdivision | 1,451 | 1,036 | 1,360 |
| Pre Consultation | 2,100 | 681 | 1,770 |
| Consent to Sever | 1,031 | 859 | 954 |

Three publicly reachable copies of the same layer, none labelled as authoritative in the
service name alone, differing by up to a factor of three. An ingestion job pointed at the
wrong one returns plausible numbers that are wrong, and nothing in the pipeline would catch
it, because every row is individually valid.

**Worse: the only Brampton permits service the keyword sweep found is `Building_Permits_DEV`,
at 141,886 rows.** Either the production permits layer is named something the sweep missed,
or Brampton's public permits feed is genuinely the `_DEV` service. That must be resolved
before a single Brampton row is ingested.

**Rule, for `config/sources.yml` and for `ingestion-engineer`:** no layer whose name ends in
`_DEV` or `_UAT` is registered as a source without a written justification in the registry
entry. `data-quality-auditor` should add a test that fails if any registered `check_url`
matches those suffixes without that justification.

### 5. Peel's `Building_Permits` is not a regional permit feed

684 rows for a region of roughly 1.5 million people is not a building permit register.
Mississauga alone reports 34,615. Whatever this layer is — regional capital works, a
sample, a niche permit class — it is not the aggregate feed the plan hoped for.

This confirms the schema draft's caution and settles the open question: **Peel is a
geography and demographics source, not a permit source.** `fct_permits` is fed by Toronto,
Mississauga and Brampton. `dim_municipality` is seeded from `MunicipalBoundary_Peel`, and
Peel's ward-level census dwelling counts feed per-capita measures.

Note the consequence for scope: Caledon appears in Peel's municipal boundary layer but has
no discovered permit feed. Either Caledon is documented as out of scope, or its absence is
surfaced in the model, but it must not be silently dropped from a "GTA" claim.

### 6. Ward boundary vintages are real and overlapping, exactly as the schema draft assumed

Peel alone publishes `Ward_Boundary_2018_2022` at 26 rows, `Wards_20222026` at 27, and
`Peel_Ward_Boundary` at 27. Toronto publishes 25-ward, 44-ward and 47-ward models in the
same package.

`dim_geography` at one row per ward-boundary *version*, with effective date ranges, is the
correct call. A `dim_geography` keyed on ward number alone would silently corrupt every
multi-year ward comparison in the project.

### 7. Several sources publish overlapping near-duplicate layers

Mississauga has three parcel layers (166,923 / 165,834 / 165,647) and three zoning layers
(60,510 / 11,277 / 10,775). The differences are small enough to look like noise and large
enough to change an answer. Each pair needs one chosen, documented, and the others recorded
as rejected with the reason — otherwise the choice gets made accidentally by whoever writes
the SQL.
