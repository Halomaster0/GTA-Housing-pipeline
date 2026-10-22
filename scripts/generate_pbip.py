"""Generate the GTA housing Power BI Project (PBIP) as version-controlled TMDL text.

Why this exists: a semantic model built by hand in Desktop lives in a binary,
cannot be diffed, and drifts from the documented measure library (the
2026-10-22 build review found a headline card whose formula did not match
``docs/fabric-dax.md``). This script is the single source of truth for the
model's tables, columns, relationships and measures; ``powerbi/`` is its
committed output. Desktop is for authoring *pages*, not the model.

Modes (exactly one of the first three per run):

    python scripts/generate_pbip.py                       # (re)write powerbi/
    python scripts/generate_pbip.py --out DIR             # write somewhere else
    python scripts/generate_pbip.py --check-schema [DB]   # embedded spec vs live gold
    python scripts/generate_pbip.py --verify-output       # committed powerbi/ vs generator

``--check-schema`` is the drift guard. It reads ``information_schema`` from the
DuckDB warehouse (default ``data/warehouse.duckdb``) and compares every gold
table's ordered ``(column, type)`` list with ``GOLD_SPEC`` below. Any missing
table, missing column, extra column, type change or reordering is drift.
``--verify-output`` is the second guard: it fails if the files on disk differ
from what this script would emit (a hand edit, or a spec change nobody
regenerated).

Exit codes: 0 clean, 1 drift or stale output, 2 the check could not run
(bad spec, unreadable warehouse).

Ownership: the generator owns the SEMANTIC MODEL (everything under
``gta-housing.SemanticModel/``) and rewrites it on every run. The ``.pbip`` and the
``gta-housing.Report/`` folder are BOOTSTRAP files: created once if absent and never
overwritten, so report pages built in Desktop survive regeneration. (Desktop may also
convert the report to its newer folder format on save; a non-empty Report folder is
therefore always left alone.)

Determinism: output contains no timestamps and no random identifiers. Every
GUID is a UUIDv5 of a stable string, files are written as UTF-8 with LF line
endings, so two runs on one spec are byte-identical.

Honesty note: this environment cannot run Power BI Desktop. The TMDL / PBIP
syntax below follows the published format as the author knows it and has not
been loaded by Desktop. See ``docs/powerbi-manual.md`` section 14 for the
first-open verification procedure and the fallback if a file is rejected.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "powerbi"
DEFAULT_WAREHOUSE = REPO_ROOT / "data" / "warehouse.duckdb"

PROJECT = "gta-housing"
SEMANTIC_MODEL_DIR = f"{PROJECT}.SemanticModel"
REPORT_DIR = f"{PROJECT}.Report"
GOLD_SCHEMA = "gold"

# 1567 is the long-standing Power BI Desktop level that PBIP/TMDL samples use.
# Everything this model needs (M partitions, parameters, inactive relationships,
# dataCategory/isKey date tables, powerBI_V3 data sources) exists at or below it,
# and any TMDL-capable Desktop reads it; Desktop bumps the level itself on save.
# Raising it buys nothing and risks "created with a newer version" rejections.
COMPATIBILITY_LEVEL = 1567
# definition.pbism 4.0 is the first version that means "TMDL folder, not model.bim".
PBISM_VERSION = "4.0"
# Relative to powerbi/. Power Query may not resolve relative paths against the
# .pbip location, so the manual tells the user to overwrite this with an
# absolute path once, in the GoldCsvFolder parameter.
CSV_FOLDER_DEFAULT = "..\\data\\gold-csv\\"

GUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "gta-housing-pipeline.powerbi.pbip")

SCHEMA_PBIP = (
    "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json"
)
SCHEMA_PLATFORM = (
    "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
    "platformProperties/2.0.0/schema.json"
)
SCHEMA_PBISM = (
    "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/"
    "definitionProperties/1.0.0/schema.json"
)
SCHEMA_PBIR = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definitionProperties/1.0.0/schema.json"
)

# DuckDB base type -> TMDL dataType / Power Query type used in TransformColumnTypes.
TMDL_TYPE: dict[str, str] = {
    "BIGINT": "int64",
    "INTEGER": "int64",
    "SMALLINT": "int64",
    "VARCHAR": "string",
    "DATE": "dateTime",
    "TIMESTAMPTZ": "dateTime",
    "BOOLEAN": "boolean",
    "DECIMAL": "decimal",
    "DOUBLE": "double",
}
M_TYPE: dict[str, str] = {
    "BIGINT": "Int64.Type",
    "INTEGER": "Int64.Type",
    "SMALLINT": "Int64.Type",
    "VARCHAR": "type text",
    "DATE": "type date",
    "TIMESTAMPTZ": "type datetimezone",
    "BOOLEAN": "type logical",
    "DECIMAL": "Currency.Type",
    "DOUBLE": "type number",
}
# Integer columns that are quantities (thousands separator); every other integer
# column is a key, a calendar part or a year and must not render as "2,026".
COUNT_COLUMNS = frozenset({"unit_count_net_new", "unit_count_proposed", "population_latest"})


class SpecError(Exception):
    """The embedded spec is internally inconsistent (a bug in this file)."""


@dataclass(frozen=True)
class Column:
    name: str
    duck_type: str
    description: str


@dataclass(frozen=True)
class Measure:
    name: str
    expression: tuple[str, ...]
    format_string: str
    description: str


@dataclass(frozen=True)
class Table:
    name: str
    description: str
    columns: tuple[Column, ...]
    measures: tuple[Measure, ...] = ()
    date_table_key: str | None = None  # calendar column when this is the date table


@dataclass(frozen=True)
class Relationship:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    active: bool


def _c(name: str, duck_type: str, description: str) -> Column:
    return Column(name, duck_type, description)


# --------------------------------------------------------------------------
# Gold spec. Column order and types are authoritative and verbatim from the
# warehouse (DuckDB DESCRIBE / final SELECT lists of models/gold/*.sql).
# Descriptions come from docs/data-dictionary.md and the gold SQL; where the
# two disagree the SQL wins (see iso_year and fiscal_* below).
# --------------------------------------------------------------------------

DIM_DATE = Table(
    name="dim_date",
    description=(
        "One row per calendar date, 2010-01-01 to 2028-12-31 (6,940 rows). "
        "This is the model's date table, keyed on calendar_date.\n"
        "date_sk is YYYYMMDD, not a day count: never subtract two date_sk values "
        "(20260301 - 20260228 = 73). Use calendar_date for any duration."
    ),
    date_table_key="calendar_date",
    columns=(
        _c(
            "date_sk",
            "BIGINT",
            "Surrogate key, YYYYMMDD. Join target for every fact date role. "
            "Not a day count: never subtract two date_sk values.",
        ),
        _c(
            "calendar_date",
            "DATE",
            "The calendar date. Key column of the date table: unique, no blanks, "
            "2010-01-01 to 2028-12-31.",
        ),
        _c("year", "BIGINT", "Calendar year."),
        _c("quarter", "BIGINT", "Calendar quarter, 1 to 4."),
        _c("month", "BIGINT", "Calendar month number, 1 to 12."),
        _c("month_name", "VARCHAR", "Full month name, English."),
        _c("month_short_name", "VARCHAR", "Three-letter month abbreviation."),
        _c("day_of_month", "BIGINT", "Day of month, 1 to 31."),
        _c("day_of_week_iso", "BIGINT", "ISO weekday, 1 = Monday to 7 = Sunday."),
        _c("day_name", "VARCHAR", "Full weekday name, English."),
        _c("is_weekend", "BOOLEAN", "TRUE for Saturday and Sunday."),
        _c("week_of_year_iso", "BIGINT", "ISO week number."),
        _c(
            "iso_year",
            "BIGINT",
            "Gold computes this as YEAR(calendar_date), so it always equals year and is NOT "
            "the ISO week-numbering year. (iso_year, week_of_year_iso) mis-pairs for days "
            "near 1 January and 31 December. Use year with calendar_date instead.",
        ),
        _c("day_of_year", "BIGINT", "Day of year, 1 to 366."),
        _c(
            "fiscal_year",
            "BIGINT",
            "Fiscal year. In v1 gold sets this equal to the calendar year (Director ruling "
            "8-5, assumption A20). It is NOT an April-start fiscal year.",
        ),
        _c("fiscal_quarter", "BIGINT", "Fiscal quarter. Equal to the calendar quarter in v1."),
        _c("fiscal_month", "BIGINT", "Fiscal month. Equal to the calendar month in v1."),
    ),
)

DIM_MUNICIPALITY = Table(
    name="dim_municipality",
    description=(
        "One row per municipality in scope (5 rows: Toronto, Mississauga, Brampton, "
        "Peel Region, Caledon; ADR-0004).\n"
        "Peel Region and Caledon issue no permits in these feeds, so they have zero fact "
        "rows and show blank, never zero, against fact measures."
    ),
    columns=(
        _c(
            "municipality_sk",
            "BIGINT",
            "Surrogate key. Target of fct_permits[municipality_sk] and "
            "fct_applications[municipality_sk].",
        ),
        _c("municipality_code", "VARCHAR", "Short code: TOR, MISS, BRAM, CALE or PEEL."),
        _c(
            "municipality_name",
            "VARCHAR",
            "Display name. Use this, not the code, on axes, slicers and legends.",
        ),
        _c(
            "municipality_tier",
            "VARCHAR",
            "Governance tier: single-tier (Toronto), lower-tier (Peel member municipalities), "
            "upper-tier (Peel Region).",
        ),
        _c("parent_region_code", "VARCHAR", "PEEL for the Peel member municipalities, else NULL."),
        _c(
            "is_permit_issuing_authority",
            "BOOLEAN",
            "FALSE for Peel Region and Caledon: zero fact rows by construction (ADR-0004).",
        ),
        _c(
            "population_latest",
            "BIGINT",
            "All NULL in v1: populated from StatCan census profiles once the series pull "
            "works. Per-capita measures are defined but not computable, so none is in this model.",
        ),
        _c(
            "population_reference_year",
            "SMALLINT",
            "All NULL in v1. Census year of population_latest.",
        ),
        _c("population_source", "VARCHAR", "All NULL in v1. Source series of population_latest."),
    ),
)

DIM_USE_TYPE = Table(
    name="dim_use_type",
    description=(
        "One row per conformed use type (6 rows): RESIDENTIAL, MIXED_USE, INSTITUTIONAL, "
        "INFRASTRUCTURE, OTHER (non-residential scope) and UNKNOWN (no use signal in source).\n"
        "Raw source values are preserved on the facts; the crosswalk is "
        "docs/conformance-matrix.md sections 1 and 2."
    ),
    columns=(
        _c("use_type_sk", "INTEGER", "Surrogate key, 1 to 6."),
        _c("use_type_code", "VARCHAR", "Conformed code, for example RESIDENTIAL or UNKNOWN."),
        _c("use_type_label", "VARCHAR", "Display label. Use on axes and slicers."),
        _c(
            "applies_to",
            "VARCHAR",
            "Always 'both': the vocabulary is shared by permits and applications.",
        ),
    ),
)

DIM_STATUS = Table(
    name="dim_status",
    description=(
        "One row per conformed status per track (15 rows). Permit track: APPLIED, "
        "UNDER_REVIEW, ISSUED, then terminal CLOSED / CANCELLED / EXPIRED, plus UNKNOWN. "
        "Application track: SUBMITTED, UNDER_REVIEW, then terminal APPROVED / REFUSED / "
        "WITHDRAWN / CLOSED, plus APPEALED (non-terminal) and UNKNOWN.\n"
        "Crosswalk: docs/conformance-matrix.md section 4."
    ),
    columns=(
        _c(
            "status_sk",
            "INTEGER",
            "Surrogate key. Permit track 1 to 7, application track 11 to 18.",
        ),
        _c(
            "status_code",
            "VARCHAR",
            "Conformed status code. Not unique on its own: UNDER_REVIEW, CLOSED and UNKNOWN "
            "each exist once per track. A fact only reaches rows of its own track through "
            "its relationship.",
        ),
        _c("status_label", "VARCHAR", "Display label. Use on axes, slicers and legends."),
        _c("applies_to", "VARCHAR", "Track this row belongs to: 'permit' or 'application'."),
        _c(
            "status_stage_order",
            "INTEGER",
            "Funnel position within the track (1 = first stage), 0 for UNKNOWN. Use it to "
            "order stages in visuals; it is not unique across tracks, so it is not wired as "
            "a sort-by column.",
        ),
        _c(
            "is_terminal",
            "BOOLEAN",
            "TRUE for end-of-life statuses. FALSE means still active; APPEALED is non-terminal. "
            "Drives Active Applications.",
        ),
    ),
)

DIM_GEOGRAPHY = Table(
    name="dim_geography",
    description=(
        "One row per ward-boundary version (municipality, ward code, effective start), "
        "89 rows (ADR-0007). Join on geography_sk only: ward_code repeats across vintages "
        "and Power BI rejects it as a key.\n"
        "Coverage: Toronto and Brampton permits carry NULL geography_sk (grid reference / "
        "no ward in source), so ward visuals of permits cover Mississauga only. "
        "Brampton city-versus-regional ward equivalence is UNCONFIRMED (conformance matrix "
        "section 3)."
    ),
    columns=(
        _c(
            "geography_sk",
            "BIGINT",
            "Surrogate key, unique 1 to 89. The only valid join key from the facts.",
        ),
        _c(
            "municipality",
            "VARCHAR",
            "Lower-tier municipality name as text. Not related to dim_municipality in this "
            "model: slice facts by dim_municipality instead.",
        ),
        _c("ward_code", "VARCHAR", "Ward code within its vintage. NOT unique across vintages."),
        _c("ward_name", "VARCHAR", "Ward display name within its vintage."),
        _c(
            "vintage",
            "VARCHAR",
            "Boundary version: city-wards-current (Toronto), mississauga-wards-current, "
            "peel-2018-2022, peel-2022-2026 (ADR-0007).",
        ),
        _c("effective_start", "DATE", "First date the boundary version applies."),
        _c("effective_end", "DATE", "Last date the boundary version applies; NULL if open-ended."),
        _c("is_current", "BOOLEAN", "TRUE for the boundary version currently in force."),
        _c(
            "census_tract_id",
            "VARCHAR",
            "NULL on every row in v1: tract linkage is unresolved (no spatial step yet).",
        ),
        _c(
            "census_tract_allocation_method",
            "VARCHAR",
            "Always 'unresolved' in v1.",
        ),
        _c(
            "geometry_precision",
            "VARCHAR",
            "'unknown' in v1: no geometries are stored, codes only.",
        ),
        _c("geometry_crs", "VARCHAR", "'EPSG:4326' by convention for any future geometry."),
    ),
)

# DAX below is docs/fabric-dax.md M1-M8 plus Permit Records and Date Coverage Pct.
# Leading // lines are the plain-language business definition kept next to the
# formula; the description carries the caveats and reference values.
PERMITS_ISSUED = Measure(
    name="Permits Issued",
    format_string="#,0",
    expression=(
        "// M1. Permits that carry an issue date (date_issued_sk is not blank).",
        "// Not the same as Permit Records, which counts every permit row.",
        "CALCULATE (",
        "    COUNTROWS ( fct_permits ),",
        "    NOT ( ISBLANK ( fct_permits[date_issued_sk] ) )",
        ")",
    ),
    description=(
        "Permits that carry an issue date (date_issued_sk is not blank). This is the only "
        "valid 'issued' count and the only one that matches a by-year chart.\n"
        "Not the same as Permit Records. Permit Records is every permit row; this excludes "
        "rows with no issue date, which is a mix of permits never issued and permits whose "
        "issue date falls outside dim_date's 2010-2028 range (the split is not measured).\n"
        "Reference (docs/measure-reconciliation.json): 647,589 overall; Toronto 462,039, "
        "Brampton 150,936, Mississauga 34,614. If a card labelled 'Permits Issued' shows "
        "827,919 it is Permit Records mislabelled, a 21.8% overstatement (build review D2)."
    ),
)

PERMIT_RECORDS = Measure(
    name="Permit Records",
    format_string="#,0",
    expression=(
        "// Every row in fct_permits, whether or not the permit has an issue date.",
        "COUNTROWS ( fct_permits )",
    ),
    description=(
        "Every row in fct_permits: the total permit population, one row per building permit, "
        "regardless of status or dates. NOT 'permits issued'.\n"
        "180,330 of these rows (21.8%) have no date_issued_sk, so they cannot be placed on the "
        "date axis: a by-year chart sums to Permits Issued, not to this measure.\n"
        "Reference (docs/measure-reconciliation.json): 827,919 overall; Toronto 571,986, "
        "Brampton 221,319, Mississauga 34,614."
    ),
)

NET_NEW_UNITS = Measure(
    name="Net New Units",
    format_string="#,0",
    expression=(
        "// M2. Sum of unit_count_net_new; NULL rows are skipped by SUM.",
        "// Mixed basis: do not total across municipalities (ADR-0003).",
        "SUM ( fct_permits[unit_count_net_new] )",
    ),
    description=(
        "CAVEAT, MIXED BASIS: units are mixed-basis. Toronto is created minus lost (net), "
        "Mississauga res_units and Brampton dwellings taken as reported with no loss "
        "adjustment. Whether those source fields are gross or net is undocumented "
        "(ADR-0003), so cross-municipality "
        "sums are not comparable (ADR-0003). Show it per municipality and never show a "
        "grand total.\n"
        "64.3% of permit rows (532,330 of 827,919) carry no unit count: Brampton 60.1%, "
        "Mississauga 80.9%, Toronto 64.9%. SUM skips them; they are not zeros.\n"
        "Gold stamps unit_count_basis = 'unknown' on every row pending source documentation "
        "(ADR-0003). Negative values are real Toronto demolition losses.\n"
        "Reference (docs/measure-reconciliation.json): Toronto 259,840; Brampton 78,957; "
        "Mississauga 30,968. Their sum, 369,765, is NOT a valid figure."
    ),
)

DATE_COVERAGE_PCT = Measure(
    name="Date Coverage Pct",
    format_string="0.0%",
    expression=(
        "// Share of permit rows that have BOTH an applied date and an issued date.",
        "DIVIDE (",
        "    CALCULATE (",
        "        COUNTROWS ( fct_permits ),",
        "        NOT ( ISBLANK ( fct_permits[date_applied_sk] ) ),",
        "        NOT ( ISBLANK ( fct_permits[date_issued_sk] ) )",
        "    ),",
        "    COUNTROWS ( fct_permits )",
        ")",
    ),
    description=(
        "Share of permit records that carry both date_applied_sk and date_issued_sk: the "
        "population Median Applied to Issued Days is computed over. Show it wherever that "
        "median is shown, because each municipality's median covers a different share of "
        "its permits.\n"
        "Reference (docs/measure-reconciliation.json): 645,382 of 827,919 = 78.0% overall; "
        "Toronto 80.4% (460,121 of 571,986), Mississauga 99.9% (34,581 of 34,614), "
        "Brampton 68.1% (150,680 of 221,319)."
    ),
)

MEDIAN_APPLIED_TO_ISSUED = Measure(
    name="Median Applied to Issued Days",
    format_string="#,0.0",
    expression=(
        "// M6. Median whole days from applied to issued, over permits with both dates.",
        "// LOOKUPVALUE form: needs no role-playing date tables.",
        "MEDIANX (",
        "    FILTER (",
        "        fct_permits,",
        "        NOT ( ISBLANK ( fct_permits[date_applied_sk] ) )",
        "            && NOT ( ISBLANK ( fct_permits[date_issued_sk] ) )",
        "    ),",
        "    DATEDIFF (",
        "        LOOKUPVALUE ( dim_date[calendar_date], dim_date[date_sk], "
        "fct_permits[date_applied_sk] ),",
        "        LOOKUPVALUE ( dim_date[calendar_date], dim_date[date_sk], "
        "fct_permits[date_issued_sk] ),",
        "        DAY",
        "    )",
        ")",
    ),
    description=(
        "Median whole days from application to issue, over permits that have both dates "
        "(645,382 of 827,919). Valid per municipality only: coverage differs by municipality "
        "(see Date Coverage Pct), so do not average the three medians into a GTA figure.\n"
        "Reference (docs/measure-reconciliation.json): Toronto 28 days (n=460,121), "
        "Mississauga 34 (n=34,581), Brampton 44 (n=150,680).\n"
        "Computed through dim_date[calendar_date] with LOOKUPVALUE, never by subtracting "
        "date_sk values."
    ),
)

ACTIVE_APPLICATIONS = Measure(
    name="Active Applications",
    format_string="#,0",
    expression=(
        "// M3. Applications whose status is not terminal; APPEALED counts as active.",
        "CALCULATE (",
        "    COUNTROWS ( fct_applications ),",
        "    dim_status[is_terminal] = FALSE ()",
        ")",
    ),
    description=(
        "Applications whose conformed status is not terminal (dim_status[is_terminal] = FALSE). "
        "APPEALED counts as active.\n"
        "Reference (docs/measure-reconciliation.json): 2,668 overall; Toronto 1,694, "
        "Brampton 719, Mississauga 255."
    ),
)

MEDIAN_SUBMITTED_TO_DECISION = Measure(
    name="Median Submitted to Decision Days",
    format_string="#,0.0",
    expression=(
        "// M7. Median whole days from submitted to decision, over applications with both dates.",
        "MEDIANX (",
        "    FILTER (",
        "        fct_applications,",
        "        NOT ( ISBLANK ( fct_applications[date_submitted_sk] ) )",
        "            && NOT ( ISBLANK ( fct_applications[date_decision_sk] ) )",
        "    ),",
        "    DATEDIFF (",
        "        LOOKUPVALUE ( dim_date[calendar_date], dim_date[date_sk], "
        "fct_applications[date_submitted_sk] ),",
        "        LOOKUPVALUE ( dim_date[calendar_date], dim_date[date_sk], "
        "fct_applications[date_decision_sk] ),",
        "        DAY",
        "    )",
        ")",
    ),
    description=(
        "Median whole days from submission to decision, over applications that have both "
        "dates. Mississauga only in v1: Toronto and Brampton sources carry no decision date, "
        "so this returns blank for them by design (an empty state, not zero).\n"
        "Reference (docs/measure-reconciliation.json): Mississauga 385 days (n=1,163)."
    ),
)

CONSTRUCTION_VALUE = Measure(
    name="Construction Value CAD",
    format_string="\\$#,0",
    expression=(
        "// M8. Sum of declared construction value in CAD; blank where the source has none.",
        "SUM ( fct_permits[construction_value_cad] )",
    ),
    description=(
        "Sum of construction_value_cad (CAD). Toronto and Mississauga only: the Brampton feed "
        "has no value field, so Brampton returns blank, not zero. Toronto has 373,693 permits "
        "with no value, so this is a sum over reported values, not over all permits.\n"
        "Reference (docs/measure-reconciliation.json): Toronto $100,991,303,902; "
        "Mississauga $18,269,933,097."
    ),
)

FCT_PERMITS = Table(
    name="fct_permits",
    description=(
        "One row per building permit (827,919 rows): Toronto 571,986, Brampton 221,319, "
        "Mississauga 34,614. Grain is the permit, not the project or the revision.\n"
        "Collapse: Toronto per PERMIT_NUM (definitive beats Conditional, then max revision); "
        "Mississauga per BP_NO; Brampton per PERMITNUMBER (the row carrying DWELLINGS wins).\n"
        "Date roles: date_issued_sk is the ACTIVE link to dim_date; date_applied_sk and "
        "date_closed_sk are inactive (USERELATIONSHIP)."
    ),
    measures=(
        PERMITS_ISSUED,
        PERMIT_RECORDS,
        NET_NEW_UNITS,
        DATE_COVERAGE_PCT,
        MEDIAN_APPLIED_TO_ISSUED,
        CONSTRUCTION_VALUE,
    ),
    columns=(
        _c("permit_sk", "BIGINT", "Surrogate key, one per permit row."),
        _c("municipality_sk", "BIGINT", "FK to dim_municipality. Never NULL."),
        _c("permit_number", "VARCHAR", "Business key: the municipality's own permit number."),
        _c(
            "geography_sk",
            "BIGINT",
            "FK to dim_geography. NULL on 793,305 of 827,919 rows: only Mississauga permits "
            "carry a ward. Toronto (grid reference) and Brampton (no ward) are NULL.",
        ),
        _c("use_type_sk", "INTEGER", "FK to dim_use_type. Never NULL."),
        _c(
            "use_type_raw",
            "VARCHAR",
            "Source type field before conformance: Toronto permit_type, Mississauga file_type, "
            "Brampton subdesc. Preserved for audit.",
        ),
        _c(
            "use_type_classification_method",
            "VARCHAR",
            "How use_type_sk was assigned. 'source-field-mapped' on every row: mapped from the "
            "source type field by the conformance crosswalk.",
        ),
        _c("status_sk", "INTEGER", "FK to dim_status (permit track). Never NULL."),
        _c("status_raw", "VARCHAR", "Source status text before conformance. Preserved for audit."),
        _c(
            "date_applied_sk",
            "BIGINT",
            "FK to dim_date, applied role. INACTIVE relationship: activate per measure with "
            "USERELATIONSHIP. NULL when the source has no applied date or it falls outside "
            "dim_date's 2010-2028 range.",
        ),
        _c(
            "date_issued_sk",
            "BIGINT",
            "FK to dim_date, issued role. The ACTIVE date relationship, so time axes show "
            "permits by issue date. NULL on 180,330 of 827,919 rows (21.8%): never issued, or "
            "issue date outside dim_date's 2010-2028 range (split not measured).",
        ),
        _c(
            "date_closed_sk",
            "BIGINT",
            "FK to dim_date, closed role. INACTIVE relationship. Always NULL for Brampton "
            "(no closed date in source).",
        ),
        _c(
            "unit_count_net_new",
            "BIGINT",
            "Units, MIXED BASIS: Toronto created minus lost (only when both are reported), "
            "Mississauga res_units and Brampton dwellings as reported, with no loss adjustment "
            "and their gross-or-net semantics undocumented. Not comparable across "
            "municipalities (ADR-0003). NULL on 64.3% of rows (not reported, never coerced to "
            "0). Negatives are real demolition losses. Use the Net New Units measure.",
        ),
        _c(
            "unit_count_basis",
            "VARCHAR",
            "Always 'unknown' in v1 (ADR-0003): the default until source semantics are "
            "confirmed, never assumed net-new.",
        ),
        _c(
            "construction_value_cad",
            "DECIMAL(21,2)",
            "Declared construction value in CAD. Toronto and Mississauga only; Brampton has no "
            "value field (all 221,319 rows NULL).",
        ),
        _c(
            "floor_area_sqm",
            "DOUBLE",
            "Floor area in square metres where the source reports one (Toronto: sum of the "
            "eight area fields; Mississauga appl_area; Brampton floor_area_raw), else NULL.",
        ),
        _c(
            "related_application_number",
            "VARCHAR",
            "NULL on every row in v1: no proven permit-to-application key exists in any feed "
            "(ADR-0006). Do not use it to link tables.",
        ),
        _c(
            "ingest_batch_id",
            "VARCHAR",
            "Ingest date of the batch that produced the row (lineage).",
        ),
        _c("row_loaded_at", "TIMESTAMPTZ", "Timestamp the row was written to gold (lineage)."),
    ),
)

FCT_APPLICATIONS = Table(
    name="fct_applications",
    description=(
        "One row per development application file (21,658 rows): Brampton 11,630, "
        "Toronto 8,601, Mississauga 1,427. Grain is the administrative file number "
        "(ADR-0005), explicitly not the project.\n"
        "Date roles: date_submitted_sk is the ACTIVE link to dim_date; date_decision_sk is "
        "inactive (USERELATIONSHIP) and populated for Mississauga only."
    ),
    measures=(ACTIVE_APPLICATIONS, MEDIAN_SUBMITTED_TO_DECISION),
    columns=(
        _c("application_sk", "BIGINT", "Surrogate key, one per application file."),
        _c("municipality_sk", "BIGINT", "FK to dim_municipality. Never NULL."),
        _c("application_number", "VARCHAR", "Business key: the administrative file number."),
        _c(
            "geography_sk",
            "BIGINT",
            "FK to dim_geography. NULL on 55 rows: unmatched ward codes (measured residual).",
        ),
        _c(
            "use_type_sk",
            "INTEGER",
            "FK to dim_use_type. UNKNOWN on 20,500 of 21,658 rows (94.6%): most application "
            "feeds carry no use signal.",
        ),
        _c(
            "use_type_classification_method",
            "VARCHAR",
            "Always 'unknown' on applications (permits use 'source-field-mapped').",
        ),
        _c("status_sk", "INTEGER", "FK to dim_status (application track). Never NULL."),
        _c("status_raw", "VARCHAR", "Source status text before conformance. Preserved for audit."),
        _c(
            "date_submitted_sk",
            "BIGINT",
            "FK to dim_date, submitted role. The ACTIVE date relationship.",
        ),
        _c(
            "date_decision_sk",
            "BIGINT",
            "FK to dim_date, decision role. INACTIVE relationship. Populated for Mississauga "
            "only; Toronto and Brampton sources have no decision date, so NULL.",
        ),
        _c(
            "unit_count_proposed",
            "BIGINT",
            "Proposed units where reported: Mississauga TOTAL_RES_UNITS only; Toronto and "
            "Brampton have no unit field, so NULL. Basis 'unknown' (ADR-0003). No measure uses "
            "it; never add it to unit_count_net_new.",
        ),
        _c("unit_count_basis", "VARCHAR", "Always 'unknown' in v1 (ADR-0003)."),
        _c(
            "ingest_batch_id",
            "VARCHAR",
            "Ingest date of the batch that produced the row (lineage).",
        ),
        _c("row_loaded_at", "TIMESTAMPTZ", "Timestamp the row was written to gold (lineage)."),
    ),
)

# Model table order (also the Power Query order). Lead-specified column order is
# inside each Table; do not reorder.
GOLD_SPEC: tuple[Table, ...] = (
    DIM_DATE,
    DIM_MUNICIPALITY,
    DIM_USE_TYPE,
    DIM_STATUS,
    DIM_GEOGRAPHY,
    FCT_PERMITS,
    FCT_APPLICATIONS,
)

# Many-to-one, single filter direction. Exactly ONE active dim_date link per fact;
# a second active link would make time results ambiguous and double-count.
_DIM_KEYS: tuple[tuple[str, str], ...] = (
    ("dim_municipality", "municipality_sk"),
    ("dim_use_type", "use_type_sk"),
    ("dim_status", "status_sk"),
    ("dim_geography", "geography_sk"),
)
RELATIONSHIPS: tuple[Relationship, ...] = (
    *(Relationship("fct_permits", key, dim, key, True) for dim, key in _DIM_KEYS),
    Relationship("fct_permits", "date_issued_sk", "dim_date", "date_sk", True),
    Relationship("fct_permits", "date_applied_sk", "dim_date", "date_sk", False),
    Relationship("fct_permits", "date_closed_sk", "dim_date", "date_sk", False),
    *(Relationship("fct_applications", key, dim, key, True) for dim, key in _DIM_KEYS),
    Relationship("fct_applications", "date_submitted_sk", "dim_date", "date_sk", True),
    Relationship("fct_applications", "date_decision_sk", "dim_date", "date_sk", False),
)


# --------------------------------------------------------------------------
# Spec helpers and validation
# --------------------------------------------------------------------------


def base_type(duck_type: str) -> str:
    """DECIMAL(21,2) -> DECIMAL."""
    return duck_type.split("(")[0].strip().upper()


def table_by_name(name: str) -> Table:
    for table in GOLD_SPEC:
        if table.name == name:
            return table
    raise SpecError(f"unknown table {name!r}")


def spec_schema() -> dict[str, list[tuple[str, str]]]:
    """The spec as {table: [(column, duckdb_type), ...]} in spec order."""
    return {t.name: [(c.name, c.duck_type) for c in t.columns] for t in GOLD_SPEC}


_COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)
_COLUMN_REF_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\[([^\]]+)\]")
_COUNTROWS_RE = re.compile(r"COUNTROWS\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)")


def validate_spec() -> None:
    """Fail loudly if the embedded spec contradicts itself. Runs on every invocation."""
    names = [t.name for t in GOLD_SPEC]
    if len(set(names)) != len(names):
        raise SpecError("duplicate table names")
    for table in GOLD_SPEC:
        cols = [c.name for c in table.columns]
        if len(set(cols)) != len(cols):
            raise SpecError(f"{table.name}: duplicate column names")
        for col in table.columns:
            if base_type(col.duck_type) not in TMDL_TYPE:
                raise SpecError(f"{table.name}.{col.name}: unmapped type {col.duck_type}")
    date_tables = [t for t in GOLD_SPEC if t.date_table_key]
    if [t.name for t in date_tables] != ["dim_date"]:
        raise SpecError("dim_date must be the one and only date table")
    key = next(c for c in DIM_DATE.columns if c.name == DIM_DATE.date_table_key)
    if base_type(key.duck_type) != "DATE":
        raise SpecError("date table key column must be DATE")

    column_type = {(t.name, c.name): base_type(c.duck_type) for t in GOLD_SPEC for c in t.columns}
    seen: set[tuple[str, str]] = set()
    active_date: dict[str, int] = {}
    for rel in RELATIONSHIPS:
        for end in ((rel.from_table, rel.from_column), (rel.to_table, rel.to_column)):
            if end not in column_type:
                raise SpecError(f"relationship endpoint {end[0]}.{end[1]} is not in the spec")
        if (
            column_type[(rel.from_table, rel.from_column)]
            != column_type[(rel.to_table, rel.to_column)]
        ):
            raise SpecError(f"relationship type mismatch {rel.from_column} -> {rel.to_column}")
        if (rel.from_table, rel.from_column) in seen:
            raise SpecError(f"{rel.from_table}.{rel.from_column} is related twice")
        seen.add((rel.from_table, rel.from_column))
        if rel.to_table == "dim_date" and rel.active:
            active_date[rel.from_table] = active_date.get(rel.from_table, 0) + 1
    for fact in ("fct_permits", "fct_applications"):
        if active_date.get(fact) != 1:
            raise SpecError(f"{fact} must have exactly one active dim_date relationship")

    for table in GOLD_SPEC:
        for measure in table.measures:
            code = _COMMENT_RE.sub("", "\n".join(measure.expression))
            if code.count("(") != code.count(")"):
                raise SpecError(f"{measure.name}: unbalanced parentheses")
            for ref_table, ref_col in _COLUMN_REF_RE.findall(code):
                if (ref_table, ref_col) not in column_type:
                    raise SpecError(f"{measure.name}: {ref_table}[{ref_col}] is not in the spec")
            for ref_table in _COUNTROWS_RE.findall(code):
                table_by_name(ref_table)


# --------------------------------------------------------------------------
# TMDL rendering
# --------------------------------------------------------------------------

_PLAIN_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def tmdl_name(name: str) -> str:
    """Quote an object name unless it is a plain identifier."""
    if _PLAIN_NAME_RE.match(name):
        return name
    return "'" + name.replace("'", "''") + "'"


def guid(*parts: str) -> str:
    """Stable GUID from the given parts: identical on every run, different per object."""
    return str(uuid.uuid5(GUID_NAMESPACE, "|".join(parts)))


class Tmdl:
    """Tab-indented line builder. TMDL structure is carried entirely by indentation."""

    def __init__(self) -> None:
        self._lines: list[str] = []

    def add(self, depth: int, text: str = "") -> None:
        self._lines.append("\t" * depth + text if text else "")

    def blank(self) -> None:
        if self._lines and self._lines[-1] != "":
            self._lines.append("")

    def describe(self, depth: int, description: str) -> None:
        """Emit a description as /// doc-comment lines, one per paragraph."""
        for paragraph in description.split("\n"):
            self.add(depth, f"/// {paragraph}")

    def render(self) -> str:
        lines = list(self._lines)
        while lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines) + "\n"


def dax_lines(expression: tuple[str, ...]) -> list[str]:
    """Convert the 4-space DAX nesting used in this file to tabs, as TMDL expects."""
    out = []
    for line in expression:
        stripped = line.lstrip(" ")
        spaces = len(line) - len(stripped)
        out.append("\t" * (spaces // 4) + " " * (spaces % 4) + stripped)
    return out


def column_format(column: Column) -> str | None:
    base = base_type(column.duck_type)
    if base in ("BIGINT", "INTEGER", "SMALLINT"):
        return "#,0" if column.name in COUNT_COLUMNS else "0"
    if base == "DATE":
        return "yyyy-mm-dd"
    if base == "DECIMAL":
        return "\\$#,0.00"
    if base == "DOUBLE":
        return "#,0.0"
    return None


def partition_source(table: Table) -> list[str]:
    """Power Query M for one table: read CSV, promote headers, explicit types."""
    path = f'Text.TrimEnd(GoldCsvFolder, {{"\\", "/"}}) & "\\{GOLD_SCHEMA}.{table.name}.csv"'
    lines = [
        "let",
        "\tSource = Csv.Document(",
        f"\t\tFile.Contents({path}),",
        '\t\t[Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]',
        "\t),",
        "\tPromoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
        "\tTyped = Table.TransformColumnTypes(",
        "\t\tPromoted,",
        "\t\t{",
    ]
    entries = [f'\t\t\t{{"{c.name}", {M_TYPE[base_type(c.duck_type)]}}}' for c in table.columns]
    lines.append(",\n".join(entries))
    lines += ["\t\t},", '\t\t"en-US"', "\t)", "in", "\tTyped"]
    return "\n".join(lines).split("\n")


def render_table(table: Table) -> str:
    w = Tmdl()
    w.describe(0, table.description)
    w.add(0, f"table {tmdl_name(table.name)}")
    w.add(1, f"lineageTag: {guid('table', table.name)}")
    if table.date_table_key:
        w.add(1, "dataCategory: Time")
    w.blank()

    for measure in table.measures:
        w.describe(1, measure.description)
        w.add(1, f"measure {tmdl_name(measure.name)} = ```")
        for line in dax_lines(measure.expression):
            w.add(3, line)
        w.add(3, "```")
        w.add(2, f"formatString: {measure.format_string}")
        w.add(2, f"lineageTag: {guid('measure', table.name, measure.name)}")
        w.blank()

    for column in table.columns:
        base = base_type(column.duck_type)
        w.describe(1, column.description)
        w.add(1, f"column {tmdl_name(column.name)}")
        w.add(2, f"dataType: {TMDL_TYPE[base]}")
        fmt = column_format(column)
        if fmt:
            w.add(2, f"formatString: {fmt}")
        if table.date_table_key == column.name:
            w.add(2, "isKey: true")
        w.add(2, f"lineageTag: {guid('column', table.name, column.name)}")
        w.add(2, "summarizeBy: none")
        w.add(2, f"sourceColumn: {column.name}")
        if base == "DATE":
            w.add(2, "annotation UnderlyingDateTimeDataType = Date")
        w.blank()

    w.add(1, f"partition {tmdl_name(table.name)} = m")
    w.add(2, "mode: import")
    w.add(2, "source =")
    for line in partition_source(table):
        w.add(4, line)
    return w.render()


def render_relationships() -> str:
    w = Tmdl()
    for rel in RELATIONSHIPS:
        name = guid("relationship", rel.from_table, rel.from_column, rel.to_table, rel.to_column)
        w.add(0, f"relationship {tmdl_name(name)}")
        if not rel.active:
            w.add(1, "isActive: false")
        w.add(1, "fromCardinality: many")
        w.add(1, "toCardinality: one")
        w.add(1, "crossFilteringBehavior: oneDirection")
        w.add(1, f"fromColumn: {tmdl_name(rel.from_table)}.{tmdl_name(rel.from_column)}")
        w.add(1, f"toColumn: {tmdl_name(rel.to_table)}.{tmdl_name(rel.to_column)}")
        w.blank()
    return w.render()


def render_model() -> str:
    w = Tmdl()
    w.add(0, "model Model")
    w.add(1, "culture: en-US")
    w.add(1, "defaultPowerBIDataSourceVersion: powerBI_V3")
    w.add(1, "sourceQueryCulture: en-US")
    w.add(1, "dataAccessOptions")
    w.add(2, "legacyRedirects")
    w.add(2, "returnErrorValuesAsNull")
    w.blank()
    order = json.dumps(["GoldCsvFolder", *(t.name for t in GOLD_SPEC)], separators=(",", ":"))
    w.add(0, f"annotation PBI_QueryOrder = {order}")
    w.blank()
    # 0 = Auto date/time off, so Desktop does not add hidden LocalDateTable_* tables.
    w.add(0, "annotation __PBI_TimeIntelligenceEnabled = 0")
    w.blank()
    for table in GOLD_SPEC:
        w.add(0, f"ref table {tmdl_name(table.name)}")
    return w.render()


def render_database() -> str:
    w = Tmdl()
    w.add(0, "database")
    w.add(1, f"compatibilityLevel: {COMPATIBILITY_LEVEL}")
    return w.render()


def render_expressions() -> str:
    w = Tmdl()
    w.describe(
        0,
        "Folder holding the seven gold.<table>.csv files written by `make export-csv`. "
        "Set it once here (Transform data, Manage parameters); every table partition reads "
        "it. The default is repo-relative from powerbi/, but Power Query may not resolve "
        "relative paths against the .pbip, so overwrite it with an absolute path on first open.",
    )
    meta = 'meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]'
    w.add(0, f'expression GoldCsvFolder = "{CSV_FOLDER_DEFAULT}" {meta}')
    w.add(1, f"lineageTag: {guid('expression', 'GoldCsvFolder')}")
    w.blank()
    w.add(1, "annotation PBI_ResultType = Text")
    return w.render()


# --------------------------------------------------------------------------
# JSON files
# --------------------------------------------------------------------------


def dump_json(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def platform_json(item_type: str) -> str:
    return dump_json(
        {
            "$schema": SCHEMA_PLATFORM,
            "metadata": {"type": item_type, "displayName": PROJECT},
            "config": {"version": "2.0", "logicalId": guid("platform", item_type)},
        }
    )


def report_json() -> str:
    """Minimal legacy-format report: one empty page, so the project opens.

    Pages are authored in Desktop per docs/report-plan.md; generating visual JSON
    here would be brittle and is out of scope. ``config`` and the page ``config`` /
    ``filters`` fields are JSON documents stored as strings, as the legacy format has it.
    """
    config = {
        "version": "5.0",
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "settings": {},
    }
    page = {
        "config": "{}",
        "displayName": "Page 1",
        "displayOption": 1,
        "filters": "[]",
        "height": 720.0,
        "name": "ReportSection",
        "visualContainers": [],
        "width": 1280.0,
    }
    return dump_json(
        {
            "config": json.dumps(config, separators=(",", ":")),
            "layoutOptimization": 0,
            "resourcePackages": [],
            "sections": [page],
        }
    )


def build_project() -> dict[str, str]:
    """Every emitted file as {path relative to the output root: text}."""
    validate_spec()
    model = f"{SEMANTIC_MODEL_DIR}/definition"
    files: dict[str, str] = {
        f"{PROJECT}.pbip": dump_json(
            {
                "$schema": SCHEMA_PBIP,
                "version": "1.0",
                "artifacts": [{"report": {"path": REPORT_DIR}}],
                "settings": {"enableAutoRecovery": True},
            }
        ),
        f"{SEMANTIC_MODEL_DIR}/.platform": platform_json("SemanticModel"),
        f"{SEMANTIC_MODEL_DIR}/definition.pbism": dump_json(
            {"$schema": SCHEMA_PBISM, "version": PBISM_VERSION, "settings": {}}
        ),
        f"{model}/database.tmdl": render_database(),
        f"{model}/model.tmdl": render_model(),
        f"{model}/expressions.tmdl": render_expressions(),
        f"{model}/relationships.tmdl": render_relationships(),
        f"{REPORT_DIR}/.platform": platform_json("Report"),
        f"{REPORT_DIR}/definition.pbir": dump_json(
            {
                "$schema": SCHEMA_PBIR,
                "version": "1.0",
                "datasetReference": {
                    "byPath": {"path": f"../{SEMANTIC_MODEL_DIR}"},
                    "byConnection": None,
                },
            }
        ),
        f"{REPORT_DIR}/report.json": report_json(),
    }
    for table in GOLD_SPEC:
        files[f"{model}/tables/{table.name}.tmdl"] = render_table(table)
    for path, text in files.items():
        try:
            text.encode("ascii")
        except UnicodeEncodeError as exc:
            raise SpecError(f"{path}: non-ASCII character in emitted text") from exc
    return files


PBIP_FILE = f"{PROJECT}.pbip"


def is_bootstrap(rel: str) -> bool:
    """Files created once and then owned by Desktop / the report author."""
    return rel == PBIP_FILE or rel.startswith(f"{REPORT_DIR}/")


def bootstrap_present(out_dir: Path, rel: str) -> bool:
    """True when a bootstrap file's slot is already taken and must not be touched."""
    if rel == PBIP_FILE:
        return (out_dir / rel).exists()
    report = out_dir / REPORT_DIR
    return report.is_dir() and any(report.iterdir())


def stray_files(out_dir: Path, files: dict[str, str]) -> list[str]:
    """Files under definition/ that the generator would not write (stale or hand-added)."""
    definition = out_dir / SEMANTIC_MODEL_DIR / "definition"
    if not definition.is_dir():
        return []
    known = set(files)
    found = (p.relative_to(out_dir).as_posix() for p in definition.rglob("*") if p.is_file())
    return sorted(p for p in found if p not in known)


def write_project(out_dir: Path) -> int:
    files = build_project()
    # Decide which bootstrap slots are taken BEFORE writing anything: writing the first
    # report file would otherwise make the folder non-empty and skip the rest.
    taken = {rel for rel in files if is_bootstrap(rel) and bootstrap_present(out_dir, rel)}
    written, kept = 0, []
    for rel, text in files.items():
        if rel in taken:
            kept.append(rel)
            continue
        target = out_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))  # bytes: LF on every OS
        written += 1
    stray = stray_files(out_dir, files)
    for rel in stray:
        print(
            f"warning: {rel} is not produced by the generator (stale or hand-added)",
            file=sys.stderr,
        )
    print(f"wrote {written} files under {out_dir}")
    if kept:
        print(f"kept {len(kept)} existing report/project file(s) untouched (Desktop-owned)")
    return 0


# --------------------------------------------------------------------------
# Guards
# --------------------------------------------------------------------------

_TYPE_ALIASES = {"TIMESTAMP WITH TIME ZONE": "TIMESTAMPTZ"}


def normalise_type(data_type: str) -> str:
    cleaned = re.sub(r"\s+", " ", data_type.strip().upper())
    return _TYPE_ALIASES.get(cleaned, cleaned)


def diff_schema(
    expected: dict[str, list[tuple[str, str]]],
    live: dict[str, list[tuple[str, str]]],
) -> list[str]:
    """Describe every difference between the spec and a live schema. Empty means no drift."""
    problems: list[str] = []
    for table, exp_cols in expected.items():
        label = f"{GOLD_SCHEMA}.{table}"
        if table not in live:
            problems.append(f"{label}: table missing from the warehouse")
            continue
        live_cols = live[table]
        exp_types = {n: normalise_type(t) for n, t in exp_cols}
        live_types = {n: normalise_type(t) for n, t in live_cols}
        for name in exp_types:
            if name not in live_types:
                problems.append(f"{label}.{name}: in spec, missing from the warehouse")
        for name in live_types:
            if name not in exp_types:
                problems.append(
                    f"{label}.{name}: in the warehouse ({live_types[name]}), not in spec"
                )
        for name, exp_type in exp_types.items():
            if name in live_types and live_types[name] != exp_type:
                problems.append(
                    f"{label}.{name}: type drift, spec {exp_type}, warehouse {live_types[name]}"
                )
        if exp_types.keys() == live_types.keys() and list(exp_types) != list(live_types):
            problems.append(f"{label}: same columns but different order")
    return problems


def read_live_schema(warehouse: Path) -> dict[str, list[tuple[str, str]]]:
    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        rows = con.execute(
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = ? ORDER BY table_name, ordinal_position",
            [GOLD_SCHEMA],
        ).fetchall()
    finally:
        con.close()
    live: dict[str, list[tuple[str, str]]] = {}
    for table_name, column_name, data_type in rows:
        live.setdefault(table_name, []).append((column_name, data_type))
    return live


def check_schema(warehouse: Path) -> int:
    if not warehouse.exists():
        print(f"check-schema: warehouse not found: {warehouse}", file=sys.stderr)
        print("Run `make transform` first, or pass the path to a gold warehouse.", file=sys.stderr)
        return 2
    try:
        live = read_live_schema(warehouse)
    except duckdb.Error as exc:
        print(f"check-schema: cannot read {warehouse}: {exc}", file=sys.stderr)
        return 2
    expected = spec_schema()
    problems = diff_schema(expected, live)
    for extra in sorted(set(live) - set(expected)):
        print(
            f"note: {GOLD_SCHEMA}.{extra} exists in the warehouse but is not modelled",
            file=sys.stderr,
        )
    if problems:
        print(f"SCHEMA DRIFT: {len(problems)} difference(s) between spec and {warehouse}")
        for problem in problems:
            print(f"  - {problem}")
        print("Update GOLD_SPEC in scripts/generate_pbip.py, regenerate, and re-verify.")
        return 1
    n_cols = sum(len(cols) for cols in expected.values())
    print(f"OK: {len(expected)} tables, {n_cols} columns match {warehouse}")
    return 0


def verify_output(out_dir: Path) -> int:
    files = build_project()
    problems: list[str] = []
    for rel, text in files.items():
        target = out_dir / rel
        if is_bootstrap(rel):
            # Report/.pbip are Desktop-owned after creation: require a slot, not content.
            if not bootstrap_present(out_dir, rel):
                problems.append(f"{rel}: missing (run the generator once to create it)")
            continue
        if not target.is_file():
            problems.append(f"{rel}: missing")
            continue
        on_disk = target.read_bytes().decode("utf-8").replace("\r\n", "\n")
        if on_disk != text:
            problems.append(f"{rel}: differs from generator output")
    problems += [f"{rel}: not produced by the generator" for rel in stray_files(out_dir, files)]
    if problems:
        print(f"STALE OUTPUT: {len(problems)} problem(s) under {out_dir}")
        for problem in problems:
            print(f"  - {problem}")
        print("Regenerate with `python scripts/generate_pbip.py` (Desktop edits are overwritten).")
        return 1
    owned = sum(1 for rel in files if not is_bootstrap(rel))
    print(f"OK: {owned} generator-owned files under {out_dir} match the generator")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="Output root (default powerbi/)."
    )
    parser.add_argument(
        "--check-schema",
        nargs="?",
        const=str(DEFAULT_WAREHOUSE),
        default=None,
        metavar="WAREHOUSE",
        help="Compare the embedded spec with a live gold warehouse; exit 1 on drift. "
        "Writes nothing.",
    )
    parser.add_argument(
        "--verify-output",
        action="store_true",
        help="Fail if the files under --out differ from what the generator would write.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        validate_spec()
        if args.check_schema is not None or args.verify_output:
            codes = []
            if args.check_schema is not None:
                codes.append(check_schema(Path(args.check_schema)))
            if args.verify_output:
                codes.append(verify_output(args.out))
            return max(codes)
        return write_project(args.out)
    except SpecError as exc:
        print(f"generate_pbip: spec error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
