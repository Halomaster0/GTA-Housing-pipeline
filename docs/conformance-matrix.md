# Conformance matrix — cross-municipality definitions, decided explicitly

**Date:** 2026-09-10 · **Owner:** `transform-engineer` · **Reviewed by:** Director of Data Engineering (owed at Gate 2)
**Inputs:** live vocabularies enumerated from bronze 2026-09-10 (see queries
below — every raw value listed was observed, none recalled).

Semantic decisions (grain, linkage, Peel/Caledon, unit basis, ward versioning)
live in ADRs 0003–0007 and are not repeated here. This matrix records the
**mechanical** layer: every raw vocabulary value and its conformed target,
including the values deliberately left UNKNOWN and why. A new raw value
appearing in a source is a drift event (ingest fails loud); its mapping is
added here, never guessed in SQL.

---

## 1. Use-type crosswalk → `dim_use_type`

Target vocabulary: `RESIDENTIAL / MIXED_USE / INSTITUTIONAL / INFRASTRUCTURE / OTHER / UNKNOWN`.
`OTHER` = classified, genuinely non-residential scope (demolition, signage,
temporary). `UNKNOWN` = the source gives no use signal (process codes).

### Toronto permits (`PERMIT_TYPE`, primary; `WORK` refines nothing in v1)

| Raw `PERMIT_TYPE` | Target | Why |
|---|---|---|
| New Houses, Residential Building Permit, Small Residential Projects, Rental Renovation Licence | RESIDENTIAL | Explicitly residential permit classes |
| Multiple Use Permit | MIXED_USE | The one explicitly mixed class |
| Portable Classrooms | INSTITUTIONAL | School buildings |
| Change of Use Permit, New Building, Non-Residential Building Permit, Building Additions/Alterations, Demolition Folder (DM), Drain and Site Service, Fire/Security Upgrade, Mechanical(MS), Plumbing(PS), Partial Permit, Conditional Permit, Designated Structures, Site Inspection(Scarborough), Temporary Structures, AS Alternative Solution, Building Historical data - Converted, DCs DeferredFees | OTHER | Non-residential scope or process artifact, not a use |
| *(WORK: 112 values)* | — | Not mapped in v1: WORK describes the job (e.g. `Window Replacement`, `HVAC`), not the use. `PROPOSED_USE`/`CURRENT_USE` unmapped v1 (values never enumerated — owed). |

### Mississauga permits (`BLDG_TYPE` primary, `FILE_TYPE` fallback)

Residential BLDG_TYPEs → RESIDENTIAL: `APARTMENT (> 6 UNITS)`,
`CONDOMINIUM ROW DWELLING`, `DETACHED DWELLING`, `DUPLEX, 3, 4, 5 0R 6PLEX`,
`RESIDENTIAL - OTHER`, `ROW DWELLING`, `SEMI-DETACHED DWELLING`,
`STREET ROW DWELLING`. Everything else (commercial, industrial, schools,
churches, governmental, garages, `UNKNOWN FROM DATA CONVERSION`, null) →
OTHER, except when `FILE_TYPE = 'RESIDENTIAL'` rescues an unlisted type →
RESIDENTIAL. Rationale (documented limitation): the v1 vocabulary has no
commercial/industrial codes, so non-residential collapses to OTHER rather
than a false precision.

### Brampton permits (`SUBDESC` — Ontario Building Code classes)

- `C:*` (all apartment/boarding/hotel/dormitory classes), `9.5`, `9.6`,
  `9.8*` residential, `Duplex`, `Triplex`, `QuatroPlex`, `Townhouse*`,
  `Semi Detached*`, `Single Family Detached`, `Single Dwelling*`,
  `Two/Three Unit Dwelling*`, `Garden Suite`, `Live/Work` → RESIDENTIAL
  (`Live/Work` → MIXED_USE — dual purpose by definition)
- `Mixed Use` → MIXED_USE
- `A2:*` (churches, schools, community, libraries, childcare) → INSTITUTIONAL
- `Site Service Com/Ind/Inst`, `Site Service Residential`, `Communication Tower`, `Crane Runway` → INFRASTRUCTURE
- `F:*` industrial, `D:*` office/commercial, `E:*` retail/restaurants,
  `A1`/`A4` entertainment, `B:*` detention/care, `Demolition*`,
  signs/tents/temporary/portables, `Commercial`, `Farm Building`,
  everything else + null → OTHER

### Mississauga applications (`CATEGORY_DESC`)

Apartment / Infill Housing / Multi-Unit Residential Complex / Townhouse /
Condominium / PAM Infill → RESIDENTIAL; `Mixed-Use` → MIXED_USE;
Community / Cultural / Institutional → INSTITUTIONAL; Commercial /
Industrial / Office → OTHER; null → UNKNOWN.

### Toronto applications (`APPLICATION_TYPE`: CD/OZ/PL/SA/SB) → UNKNOWN

Process codes, not uses (rezoning vs site plan says nothing about
residential vs office). Use signal comes from Phase 4 zero-shot
classification of DESCRIPTION (cached, ADR-0003 pattern) — not guessed here.

### Brampton applications → UNKNOWN except Draft Plan of Condo → RESIDENTIAL

Minor Variance / Consent / Pre Consultation / OPA-ZBA-Subdivision are
process classes spanning all uses → UNKNOWN. Draft Plan of Condo is a
residential built form → RESIDENTIAL.

## 2. Status crosswalk → `dim_status` (split by `applies_to`)

### Permits: APPLIED / UNDER_REVIEW / ISSUED / CLOSED / CANCELLED / EXPIRED / UNKNOWN

| Source | Raw → target |
|---|---|
| Toronto (20) | Application Received→APPLIED; Application Acceptable, Application On Hold, Examiner's Notice Sent, Response Received, Under Review→UNDER_REVIEW; Approved, Issuance Pending, Ready for Issuance, Permit Issued, Inspection, Open→ISSUED (Inspection/Open = live permit); Closed, Closed - Dormant, Closed Permit/Incomplete Work→CLOSED; Cancelled, Abandoned, Refused→CANCELLED; Revision Issued→ISSUED; Superseded→CANCELLED (replaced revision; never reaches gold — max revision kept) |
| Mississauga (3) | ISSUED PERMIT→ISSUED; COMPLETED -ALL INSP SIGNED OFF→CLOSED; REVOKED→CANCELLED |
| Brampton (13) | Applied→APPLIED; Zoning Certified→UNDER_REVIEW (pre-issuance milestone); Ready to Issue→ISSUED; Issued, Occupancy Granted→ISSUED; Registered→CLOSED (end-state registration; ISSUED-vs-CLOSED unconfirmed — flagged, terminality is what velocity needs); Closed→CLOSED; Cancelled, Refused, Revoked, Withdrawn, Deemed Abandoned, Pending Removal→CANCELLED |

### Applications: SUBMITTED / UNDER_REVIEW / APPROVED / REFUSED / APPEALED / WITHDRAWN / CLOSED / UNKNOWN

| Source | Raw → target |
|---|---|
| Toronto (17) | Application Received→SUBMITTED; Circulated, Under Review, Amend Drft Plan App→UNDER_REVIEW; Approved, Council Approved, Draft Plan Approved, Final Approval Completed, NOAC Issued, OMB Approved, OMB Partially Approved→APPROVED; Refused, OMB Refused→REFUSED; Appeal Received, OMB Appeal→APPEALED; Closed→CLOSED |
| Mississauga (2) | Active→UNDER_REVIEW; Approved→APPROVED |
| Brampton MV/consent/pre/condo (25/18/17/10) | Submitted, Received, Incomplete, Invalid, Initial Submission Rejected, Verification of Documents→SUBMITTED; In Review*, Staff Review*, Meeting/Hearing Scheduled, Staff Report Sent, Comments Released, Stage 2 Review, Finalize, Review→UNDER_REVIEW; Approved*, Final and Binding, Draft Approved, Registered*, Plan of Condo Registered, Registration, MZO Approved, M-Plan/Condition Clearance, COA - Approved*→APPROVED; Denied, Refused, OMB Refused, COA - Null & Void→REFUSED; In Appeal, Under Appeal→APPEALED; Withdrawn, Lapsed, Expired, Inactive, Closed*, COA - Closed, PRE - Closed, Denied Closed, Transferred→CLOSED (Transferred left this system — noted, not celebrated); Deemed Complete, Application Complete→UNDER_REVIEW (completeness ≠ approval); `OMB � Approved` (mojibake, byte-preserved in bronze/silver)→APPROVED |

Terminal states (permit: ISSUED-terminal? No — permits: CLOSED/CANCELLED/EXPIRED terminal; ISSUED live. Applications: APPROVED/REFUSED/WITHDRAWN/CLOSED terminal; APPEALED live).

## 3. Units, currency, area, dates, geography (mechanical)

- Units: Toronto `created − lost` candidate net, computed ONLY when both are
  reported (strict NULL otherwise — a blank loss is unknown, not zero);
  negative nets are legitimate demolition losses (DEM permits netting −N),
  monitored not failed. Mississauga `RES_UNITS` / `TOTAL_RES_UNITS`;
  Brampton `DWELLINGS`; all `basis = 'unknown'` (ADR-0003).
  Brampton finish-rows carry null DWELLINGS (shell row holds the count, §11) —
  gold keeps one row per folder preferring the non-null-DWELLINGS row, so
  folder unit sums do not double-count.
- Currency: Toronto `EST_CONST_COST` text→decimal; Mississauga
  `EST_CON_VALUE` int; Brampton none. Assumed CAD (A23).
- Area: Toronto occupancy-component sum → `floor_area_sqm` (assumption:
  components partition GFA — flagged); Mississauga `APPL_AREA` unit unknown,
  stored raw + flagged (A22 open); Brampton `GFA` text→decimal, unit unknown,
  flagged.
- Dates: Toronto bare DATEs map directly (no TZ shift, schema §7);
  Mississauga/Brampton epoch-millis are true timestamps → UTC → DATE.
  Brampton ISSUEDATE nullable → NULL (unissued).
- Geography: Toronto apps by WARD_NUMBER → `city-wards-current` vintage;
  Mississauga by WARD int → `mississauga-wards-current` vintage; Brampton
  apps parse `WARD 6` → `6` → `peel-2022-2026` vintage **with an explicit
  caveat: Brampton city-ward vs Peel-regional-ward equivalence is
  UNCONFIRMED** (same codes, possibly different boundaries — owed
  verification before any ward-level Brampton measure publishes without the
  caveat). Facts never join across vintages: Mississauga ward `1` exists in
  three dim rows (municipal + two Peel vintages) and the join pins one, so
  no fact can fan out. Toronto permits (WARD_GRID) and Brampton permits (no
  ward) → NULL geography (measured in report).
  Tract linkage `unresolved` v1 (ADR-0007 fallback).

## 4. Dropped / kept PII (binding)

Dropped in silver, tested: Toronto `CONTACT_NAME/PHONE/EMAIL`; Peel current
`Mayor/RegionalCo/LocalCounc`; Peel prior `Mayor/FirstName*/LastName*/Phone*/email*/RC_Name`.
Kept in silver, out of gold, reason logged: Toronto `BUILDER_NAME`,
Mississauga `APPLICANT/PLANNER`, Brampton `BUILDER/CONTRACTOR`,
`CITY_PLANNER`, `AGENT/APPLICANT_COMPANY` (mixed person/org, analytical
value for builder-activity questions, never published to a public layer
without a second review).

## 5. Vocabulary queries (re-run to re-verify)

```sql
SELECT DISTINCT <col> FROM read_parquet('data/bronze/<source>/ingest_date=<date>/part-*.parquet') ORDER BY 1;
```

Columns enumerated 2026-09-10: Toronto permits PERMIT_TYPE/WORK/STATUS;
Toronto apps APPLICATION_TYPE/STATUS; Mississauga permits
STATUS/BLDG_TYPE/FILE_TYPE/SCOPE; Mississauga siteplan+rezoning
TYPE_DESC/SIMPLE_STATUS/CATEGORY_DESC (rezoning CATEGORY_DESC assumed same
domain — re-enumerate before trusting a rezoning-specific measure);
Brampton permits STATUSDESC/SUBDESC/WORKDESC; Brampton planning
STATUS/APPLICATION_TYPE per layer. Toronto PROPOSED_USE/CURRENT_USE never
enumerated — owed before any use-mapping cites them.
