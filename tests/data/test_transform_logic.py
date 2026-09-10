"""Transform logic tests on synthetic bronze — runs in CI without live APIs.

Fixture rows use the exact bronze column names and exercise every proven
rule: cross-resource survivor, revision/conditional collapse, address
collapse, PII absence, unit-cast strictness, epoch dates, double
publications, shell-vs-finish preference, and the SCD2 history seed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.transform.runner import build_all
from tests.data.invariants import assert_all_invariants

DATE = "2099-01-01"


def land(bronze_root: Path, source: str, records: list[dict[str, Any]]) -> None:
    part = bronze_root / source / f"ingest_date={DATE}"
    part.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(records), part / "part-00000.parquet")


def toronto_permit_row(**over: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "_id": 1,
        "PERMIT_NUM": "P1",
        "REVISION_NUM": "00",
        "PERMIT_TYPE": "New Houses",
        "STRUCTURE_TYPE": "SFD",
        "WORK": "New Building",
        "STREET_NUM": "1",
        "STREET_NAME": "MAIN",
        "STREET_TYPE": "ST",
        "STREET_DIRECTION": None,
        "POSTAL": "M1M",
        "GEO_ID": "1",
        "WARD_GRID": "N1",
        "APPLICATION_DATE": "2024-01-01",
        "ISSUED_DATE": "2024-02-01",
        "COMPLETED_DATE": None,
        "STATUS": "Inspection",
        "DESCRIPTION": "d",
        "CURRENT_USE": "Sfd",
        "PROPOSED_USE": "Sfd",
        "DWELLING_UNITS_CREATED": "2",
        "DWELLING_UNITS_LOST": "0",
        "EST_CONST_COST": "100000",
        "ASSEMBLY": 0.0,
        "INSTITUTIONAL": 0.0,
        "RESIDENTIAL": 100.0,
        "BUSINESS_AND_PERSONAL_SERVICES": 0.0,
        "MERCANTILE": 0.0,
        "INDUSTRIAL": 0.0,
        "INTERIOR_ALTERATIONS": 0.0,
        "DEMOLITION": 0.0,
        "BUILDER_NAME": "B1",
    }
    row.update(over)
    return row


def toronto_app_row(**over: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "_id": 1,
        "APPLICATION_TYPE": "OZ",
        "APPLICATION#": "A1",
        "STREET_NUM": "5",
        "STREET_NAME": "OXFORD",
        "STREET_TYPE": "DR",
        "STREET_DIRECTION": None,
        "POSTAL": "M6M",
        "DATE_SUBMITTED": "2022-02-14T00:00:00",
        "STATUS": "Circulated",
        "X": "1",
        "Y": "2",
        "DESCRIPTION": "d",
        "REFERENCE_FILE#": None,
        "FOLDERRSN": "9",
        "WARD_NUMBER": "05",
        "WARD_NAME": "W5",
        "COMMUNITY_MEETING_DATE": None,
        "COMMUNITY_MEETING_TIME": None,
        "COMMUNITY_MEETING_LOCATION": None,
        "APPLICATION_URL": None,
        "CONTACT_NAME": "Private Person",
        "CONTACT_PHONE": "555-0100",
        "CONTACT_EMAIL": "x@y.z",
        "PARENT_FOLDER_NUMBER": None,
    }
    row.update(over)
    return row


def build_fixture_warehouse(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    bronze = tmp_path / "bronze"
    land(
        bronze,
        "toronto-building-permits-active",
        [
            toronto_permit_row(_id=1, PERMIT_NUM="P1"),
            toronto_permit_row(_id=2, PERMIT_NUM="P1", BUILDER_NAME="Other Builder"),
            toronto_permit_row(_id=3, PERMIT_NUM="P2", PERMIT_TYPE="Conditional Permit"),
            toronto_permit_row(_id=4, PERMIT_NUM="P3", DWELLING_UNITS_CREATED="abc"),
            toronto_permit_row(_id=5, PERMIT_NUM="P4", DWELLING_UNITS_LOST=None),
        ],
    )
    land(
        bronze,
        "toronto-building-permits-cleared",
        [
            toronto_permit_row(_id=50, PERMIT_NUM="P1", STATUS="Closed"),
            toronto_permit_row(_id=51, PERMIT_NUM="P2", STATUS="Closed"),
        ],
    )
    land(
        bronze,
        "toronto-development-applications",
        [
            toronto_app_row(_id=1, STREET_NUM="5A"),
            toronto_app_row(_id=2, STREET_NUM="7"),
        ],
    )
    land(
        bronze,
        "toronto-wards",
        [
            {
                "AREA_SHORT_CODE": "05",
                "AREA_NAME": "W5",
                "DATE_EFFECTIVE": "2018-08-07T00:00:00",
                "DATE_EXPIRY": "3000-01-01T00:00:00",
                "geometry": None,
            },
        ],
    )
    epoch = 1705276800000
    land(
        bronze,
        "mississauga-building-permits",
        [
            {
                "OBJECTID": 1,
                "BP_NO": "M1",
                "STATUS": "ISSUED PERMIT",
                "ADDRESS": "a",
                "UNIT_NO": None,
                "DESCRIPTION": "d",
                "SCOPE": "NEW BUILDING",
                "FILE_TYPE": "RESIDENTIAL",
                "BLDG_TYPE": "DETACHED DWELLING",
                "APP_DETAIL": None,
                "APPL_AREA": 50.0,
                "STOREYS": 2.0,
                "EST_CON_VALUE": 9,
                "RES_UNITS": 1,
                "DEMO": "N",
                "POSTAL_CODE": "L5H",
                "BLDG_NO": None,
                "WARD": 1,
                "ZAREA": "08",
                "LATITUDE": 43.5,
                "LONGITUDE": -79.5,
                "APPLICATION_DATE": epoch,
                "ISSUE_DATE": epoch,
                "COMPLETE_DATE": None,
            },
            {
                "OBJECTID": 2,
                "BP_NO": "M1",
                "STATUS": "ISSUED PERMIT",
                "ADDRESS": "a",
                "UNIT_NO": None,
                "DESCRIPTION": "d",
                "SCOPE": "NEW BUILDING",
                "FILE_TYPE": "RESIDENTIAL",
                "BLDG_TYPE": "DETACHED DWELLING",
                "APP_DETAIL": None,
                "APPL_AREA": 50.0,
                "STOREYS": 2.0,
                "EST_CON_VALUE": 9,
                "RES_UNITS": 1,
                "DEMO": "N",
                "POSTAL_CODE": "L5H",
                "BLDG_NO": None,
                "WARD": 1,
                "ZAREA": "08",
                "LATITUDE": 43.5,
                "LONGITUDE": -79.5,
                "APPLICATION_DATE": epoch,
                "ISSUE_DATE": epoch,
                "COMPLETE_DATE": None,
            },
        ],
    )
    siteplan_base = {
        "OBJECTID": 1,
        "PLNG_APP_ID": 7,
        "TYPE_DESC": "SITE PLAN",
        "SUBTYPE_CODE": "SP",
        "YEAR": 24,
        "APPLICATION_NO": 2,
        "CATEGORY_DESC": ("Site Plan Applications including SPAX - Apartment"),
        "GENERAL_LOCATION": "g",
        "DESCRIPTION": "d",
        "SITE_ADDRESS": "s",
        "APPLICATION_DATE": epoch,
        "APPROVAL_DATE": epoch,
        "APPLICANT": "ACME",
        "PLANNER": "P",
        "RES_DET": 1,
        "RES_SEMIS": 0,
        "RES_ROWS": 0,
        "RES_APTS": 0,
        "RES_OTH_APTS": 0,
        "ICI_OFFICE": None,
        "ICI_INDUST": None,
        "ICI_ICI_FLEX": None,
        "ICI_RETAIL": None,
        "ICI_CC": None,
        "ICI_INSTITUT": None,
        "ICI_OTHER": None,
        "TOTAL_RES_UNITS": 10,
        "TOTAL_NON_RES_GFA": None,
        "WARD": 1,
        "CHAR_AREA": "c",
        "SIMPLE_STATUS": "Approved",
        "Shape__Area": 1.0,
        "Shape__Length": 1.0,
    }
    rezoning_row = dict(siteplan_base)
    rezoning_row.update({"OBJECTID": 9, "APP_FILE_NO": "SP9", "TYPE_DESC": "REZONING AND/OR OPA"})
    siteplan_row = dict(siteplan_base)
    siteplan_row.update({"APP_FILE_NO": "SP9"})
    land(bronze, "mississauga-site-plan-applications", [siteplan_row])
    land(bronze, "mississauga-rezoning-applications", [rezoning_row])
    land(bronze, "mississauga-wards", [{"WARD": 1}])
    land(
        bronze,
        "brampton-building-permits",
        [
            {
                "OBJECTID": 1,
                "GIS_ID": 1.0,
                "ADDRESS": "a",
                "FOLDERRSN": 11.0,
                "PERMITNUMBER": "B1",
                "SUBDESC": "Single Family Detached",
                "WORKDESC": "New Shell Building",
                "ISSUEDATE": epoch,
                "INDATE": epoch,
                "STATUSDESC": "Closed",
                "PROCESSDATE": None,
                "BUILDER": "BB",
                "CONTRACTOR": "CC",
                "EXPIRYDATE": None,
                "GFA": "200.5",
                "SECOND_UNIT": None,
                "BEDROOMS": "3",
                "STOREYS": "2",
                "DWELLINGS": "1",
            },
            {
                "OBJECTID": 2,
                "GIS_ID": 1.0,
                "ADDRESS": "a",
                "FOLDERRSN": 12.0,
                "PERMITNUMBER": "B1",
                "SUBDESC": "Single Family Detached",
                "WORKDESC": "Interior/Unit Finish",
                "ISSUEDATE": epoch,
                "INDATE": epoch,
                "STATUSDESC": "Closed",
                "PROCESSDATE": None,
                "BUILDER": "BB",
                "CONTRACTOR": "CC",
                "EXPIRYDATE": None,
                "GFA": "150.0",
                "SECOND_UNIT": None,
                "BEDROOMS": "3",
                "STOREYS": "2",
                "DWELLINGS": None,
            },
        ],
    )
    plan_base = {
        "FILE_NUMBER": "F1",
        "REGIONAL_NUMBER": None,
        "LOCATION": "loc",
        "DATE_RECEIVED": epoch,
        "APPLICATION_TYPE": "Minor Variance",
        "APPLICATION_TITLE": "t",
        "DESCRIPTION": "d",
        "STATUS": "Approved",
        "CITY_PLANNER": "CP",
        "PROPOSAL_DESCRIPTION": "p",
        "AGENT_COMPANY": None,
        "APPLICANT_COMPANY": "AC",
        "WARD": "WARD 6",
        "Shape__Area": 5.0,
    }
    mv1 = dict(plan_base)
    mv1.update({"POLY_ID": 100})
    mv2 = dict(plan_base)
    mv2.update({"POLY_ID": 101})
    land(bronze, "brampton-minor-variance", [mv1, mv2])
    empty_plan = {
        "FILE_NUMBER": "X",
        "REGIONAL_NUMBER": None,
        "LOCATION": None,
        "DATE_RECEIVED": epoch,
        "APPLICATION_TYPE": "None",
        "APPLICATION_TITLE": None,
        "DESCRIPTION": None,
        "STATUS": "Submitted",
        "CITY_PLANNER": None,
        "PROPOSAL_DESCRIPTION": None,
        "AGENT_COMPANY": None,
        "APPLICANT_COMPANY": None,
        "WARD": None,
        "POLY_ID": 1,
        "Shape__Area": None,
    }
    land(bronze, "brampton-opa-zba-subdivision", [dict(empty_plan)])
    land(bronze, "brampton-pre-consultation", [dict(empty_plan)])
    land(bronze, "brampton-consent-sever", [dict(empty_plan)])
    land(bronze, "brampton-draft-plan-condo", [dict(empty_plan)])
    land(
        bronze,
        "peel-wards-current",
        [{"Municipali": "Brampton", "WardNumber": 6, "WardName": "W6"}],
    )
    land(bronze, "peel-wards-prior", [{"MUNIC": "Brampton", "WARDNUM": "6"}])
    land(
        bronze,
        "peel-census2021-ct",
        [
            {
                "CTUID": "T1",
                "CTNAME": "1",
                "CSDNAME": "Brampton",
                "LANDAREA": 1.0,
                "Pop16": 1,
                "Pop21": 2,
                "PopChg16_21": 1.0,
                "Dwell21": 1,
                "Dwell_UR21": 1,
                "AreaKM2_21": 1.0,
                "PopDen21": 1.0,
                "DwellUR_Den21": 1.0,
            }
        ],
    )

    warehouse = tmp_path / "warehouse.duckdb"
    build_all(warehouse, bronze, DATE)
    return duckdb.connect(str(warehouse))


@pytest.fixture()
def con(tmp_path: Path) -> Any:
    connection = build_fixture_warehouse(tmp_path)
    yield connection
    connection.close()


def query(con: Any, sql: str) -> Any:
    return con.execute(sql).fetchall()


def test_toronto_permit_collapse_rules(con: Any) -> None:
    rows = {
        r[0]: r for r in query(con, "SELECT permit_number, status_raw FROM silver.toronto_permits")
    }
    assert set(rows) == {"P1", "P2", "P3", "P4"}
    assert rows["P1"][1] == "Closed"  # cleared resource survives
    nets = {
        r[0]: r[1]
        for r in query(
            con,
            "SELECT permit_number, unit_count_net_new FROM gold.fct_permits f "
            "JOIN gold.dim_municipality m USING (municipality_sk) "
            "WHERE m.municipality_code = 'TOR'",
        )
    }
    assert nets["P1"] == 2  # created - lost, both reported
    assert nets["P3"] is None  # garbage units text -> NULL, build survives
    assert nets["P4"] is None  # strict net: lost NULL -> NULL, not created
    gold = {
        r[0]: r
        for r in query(
            con,
            "SELECT permit_number FROM gold.fct_permits f "
            "JOIN gold.dim_municipality m USING (municipality_sk) "
            "WHERE m.municipality_code = 'TOR'",
        )
    }
    assert set(gold) == {"P1", "P2", "P3", "P4"}  # one row per permit, incl. P2


def test_toronto_application_address_collapse_and_pii(con: Any) -> None:
    rows = query(con, "SELECT application_number, address_count FROM silver.toronto_applications")
    assert rows == [("A1", 2)]
    cols = [
        r[2]
        for r in query(
            con,
            "SELECT table_schema, table_name, column_name FROM information_schema.columns "
            "WHERE table_schema = 'silver'",
        )
    ]
    assert "CONTACT_NAME" not in cols and "CONTACT_EMAIL" not in cols


def test_crosswalk_spot_checks(con: Any) -> None:
    use = {
        r[0]: r[1]
        for r in query(
            con,
            "SELECT f.permit_number, u.use_type_code FROM gold.fct_permits f "
            "JOIN gold.dim_use_type u ON f.use_type_sk = u.use_type_sk "
            "JOIN gold.dim_municipality m USING (municipality_sk) "
            "WHERE m.municipality_code = 'TOR'",
        )
    }
    assert use["P1"] == "RESIDENTIAL"
    app_use = {
        r[0]: r[1]
        for r in query(
            con,
            "SELECT f.application_number, u.use_type_code FROM gold.fct_applications f "
            "JOIN gold.dim_use_type u ON f.use_type_sk = u.use_type_sk",
        )
    }
    assert app_use["A1"] == "UNKNOWN"  # process code, no use signal
    assert app_use["F1"] == "UNKNOWN"  # minor variance, no use signal
    assert app_use["SP9"] == "RESIDENTIAL"  # apartment category


def test_shell_finish_preference_and_brampton_collapse(con: Any) -> None:
    rows = query(
        con,
        "SELECT permit_number, unit_count_net_new FROM gold.fct_permits f "
        "JOIN gold.dim_municipality m USING (municipality_sk) "
        "WHERE m.municipality_code = 'BRAM'",
    )
    assert rows == [("B1", 1)]  # shell row (units=1) wins over finish row (null)
    apps = query(
        con,
        "SELECT COUNT(*) FROM gold.fct_applications f "
        "JOIN gold.dim_municipality m USING (municipality_sk) "
        "WHERE m.municipality_code = 'BRAM'",
    )
    assert apps == [(2,)]  # F1 collapsed to one row + X


def test_cross_feed_union_and_history_seed(con: Any) -> None:
    rows = query(con, "SELECT application_number, feeds_seen FROM silver.mississauga_applications")
    assert len(rows) == 1 and rows[0][0] == "SP9"
    assert set(rows[0][1].split("+")) == {"site-plan", "rezoning"}
    hist = query(
        con,
        "SELECT COUNT(*), SUM(CASE WHEN is_current THEN 1 ELSE 0 END) "
        "FROM silver.application_status_history",
    )
    assert hist[0][0] == hist[0][1] and hist[0][0] >= 4  # first run: all current
    methods = query(con, "SELECT DISTINCT detection_method FROM silver.application_status_history")
    assert methods == [("bronze-snapshot-diff",)]


def test_invariants_hold_on_fixture(con: Any) -> None:
    assert_all_invariants(con)
