"""Athena vs DuckDB parity, run as the least-privilege reader role.

Opt-in. Skipped unless these are set (see README "AWS analytics layer"):
    AWS_PROFILE, ATHENA_WORKGROUP, ATHENA_READER_ROLE_ARN, ATHENA_CURATED_BUCKET
and the aws extra is installed. Default `make test` and CI never reach AWS.

What it proves, against the September warehouse (DuckDB is the source of truth):
  1. Row counts for all 7 gold tables match exactly.
  2. Three published anchors from docs/measure-reconciliation.json match exactly:
     fct_permits total, fct_applications total, and permits issued (the sum of the
     per-municipality-year series).
  3. A grouped aggregate (issued permits by municipality and year, 43 rows) matches
     DuckDB and the reconciliation file exactly.
  4. A SUM of construction value by municipality matches DuckDB within a stated
     relative tolerance (double arithmetic, so the sum order can differ slightly).
  5. Negative tests: the reader role is denied writing to the curated bucket and
     denied creating and deleting Glue tables.

Every Athena query records its query ID, state, bytes scanned and engine time.
A sanitised report (no account ID, bucket names or profile names) is written to
docs/aws-parity-report.md when the module runs.
"""

from __future__ import annotations

import contextlib
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pytest

boto3 = pytest.importorskip("boto3")  # whole module skipped when the aws extra is absent

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RECONCILIATION = REPO_ROOT / "docs" / "measure-reconciliation.json"
REPORT = REPO_ROOT / "docs" / "aws-parity-report.md"

PROFILE = os.environ.get("AWS_PROFILE")
REGION = os.environ.get("AWS_REGION", "us-east-2")
WORKGROUP = os.environ.get("ATHENA_WORKGROUP")
READER_ROLE_ARN = os.environ.get("ATHENA_READER_ROLE_ARN")
CURATED_BUCKET = os.environ.get("ATHENA_CURATED_BUCKET")
DATABASE = os.environ.get("ATHENA_DATABASE", "gta_housing_gold")
DUCKDB_PATH = Path(os.environ.get("DUCKDB_PATH", REPO_ROOT / "data" / "warehouse-sept.duckdb"))

# Relative tolerance for double-precision sums. Same values, different summation order.
SUM_REL_TOLERANCE = 1e-9

GOLD_TABLES = [
    "dim_date",
    "dim_municipality",
    "dim_geography",
    "dim_use_type",
    "dim_status",
    "fct_permits",
    "fct_applications",
]

_configured = all([PROFILE, WORKGROUP, READER_ROLE_ARN, CURATED_BUCKET]) and DUCKDB_PATH.exists()

pytestmark = [
    pytest.mark.aws,
    pytest.mark.skipif(
        not _configured,
        reason="AWS parity test not configured: set AWS_PROFILE, ATHENA_WORKGROUP, "
        "ATHENA_READER_ROLE_ARN, ATHENA_CURATED_BUCKET and provide the DuckDB file",
    ),
]


@dataclass
class Record:
    label: str
    query_id: str
    state: str
    bytes_scanned: int
    engine_ms: int


RECORDS: list[Record] = []
NEGATIVE_RESULTS: list[tuple[str, str]] = []  # (what was attempted, observed error code)


@pytest.fixture(scope="module")
def reader() -> Any:
    """Session for the reader role: assume it, keep the temporary credentials in memory only."""
    base = boto3.Session(profile_name=PROFILE, region_name=REGION)
    creds = base.client("sts").assume_role(
        RoleArn=READER_ROLE_ARN,
        RoleSessionName="gta-housing-parity",
        DurationSeconds=900,
    )["Credentials"]
    return boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
        region_name=REGION,
    )


@pytest.fixture(scope="module")
def duck() -> Any:
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    yield con
    con.close()


@pytest.fixture(scope="module", autouse=True)
def write_report() -> Any:
    yield
    if RECORDS or NEGATIVE_RESULTS:
        _write_report()


def run_athena(session: Any, sql: str, label: str) -> list[list[str | None]]:
    """Run one query through the workgroup and return rows as strings (header dropped)."""
    athena = session.client("athena")
    qid = athena.start_query_execution(QueryString=sql, WorkGroup=WORKGROUP)["QueryExecutionId"]

    deadline = time.monotonic() + 300
    while True:
        execution = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        state = execution["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        if time.monotonic() > deadline:
            raise TimeoutError(f"{label}: still {state} after 300s (query {qid})")
        time.sleep(0.5)

    stats = execution.get("Statistics", {})
    RECORDS.append(
        Record(
            label=label,
            query_id=qid,
            state=state,
            bytes_scanned=int(stats.get("DataScannedInBytes", 0)),
            engine_ms=int(stats.get("EngineExecutionTimeInMillis", 0)),
        )
    )
    if state != "SUCCEEDED":
        reason = execution["Status"].get("StateChangeReason", "no reason given")
        raise AssertionError(f"{label}: query {state}: {reason}")

    rows: list[list[str | None]] = []
    kwargs: dict[str, Any] = {"QueryExecutionId": qid}
    while True:
        page = athena.get_query_results(**kwargs)
        for row in page["ResultSet"]["Rows"]:
            rows.append([cell.get("VarCharValue") for cell in row["Data"]])
        if "NextToken" not in page:
            break
        kwargs["NextToken"] = page["NextToken"]
    return rows[1:]  # first row is the header


def _reconciliation() -> dict[str, Any]:
    return json.loads(RECONCILIATION.read_text(encoding="utf-8"))


def _write_report() -> None:
    lines = [
        "# AWS parity report",
        "",
        f"Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} by "
        "`tests/integration/test_athena_parity.py`.",
        "",
        "Athena runs as a least-privilege reader role against the September gold tables. "
        "DuckDB (`data/warehouse-sept.duckdb`) is the source of truth.",
        "",
        "## Athena queries",
        "",
        "| Check | Query ID | State | Bytes scanned | Engine ms |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for r in RECORDS:
        lines.append(
            f"| {r.label} | `{r.query_id}` | {r.state} | {r.bytes_scanned:,} | {r.engine_ms:,} |"
        )
    total_bytes = sum(r.bytes_scanned for r in RECORDS)
    lines += [
        "",
        f"Total bytes scanned across {len(RECORDS)} queries: **{total_bytes:,}** "
        f"({total_bytes / 1_000_000:.3f} MB).",
        "",
        "## Negative tests (reader role)",
        "",
        "| Attempted action | Observed error |",
        "| --- | --- |",
    ]
    for attempted, observed in NEGATIVE_RESULTS:
        lines.append(f"| {attempted} | {observed} |")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")


@pytest.mark.parametrize("table", GOLD_TABLES)
def test_row_counts_match_duckdb(reader: Any, duck: Any, table: str) -> None:
    athena_count = int(
        run_athena(reader, f'SELECT COUNT(*) FROM "{DATABASE}"."{table}"', f"count {table}")[0][0]
    )
    duck_count = duck.execute(f"SELECT COUNT(*) FROM gold.{table}").fetchone()[0]
    assert athena_count == duck_count, f"{table}: Athena {athena_count} vs DuckDB {duck_count}"


def test_published_anchors_match(reader: Any, duck: Any) -> None:
    """Three measures published in docs/measure-reconciliation.json."""
    published = _reconciliation()
    expected_permits = published["fact_totals"]["fct_permits"]
    expected_apps = published["fact_totals"]["fct_applications"]
    expected_issued = sum(
        r["permits_issued"] for r in published["permits_issued_by_municipality_year"]
    )

    permits = int(
        run_athena(
            reader, f'SELECT COUNT(*) FROM "{DATABASE}"."fct_permits"', "anchor permit records"
        )[0][0]
    )
    apps = int(
        run_athena(
            reader, f'SELECT COUNT(*) FROM "{DATABASE}"."fct_applications"', "anchor applications"
        )[0][0]
    )
    issued = int(
        run_athena(
            reader,
            f'SELECT COUNT(*) FROM "{DATABASE}"."fct_permits" WHERE date_issued_sk IS NOT NULL',
            "anchor permits issued",
        )[0][0]
    )

    assert permits == expected_permits, (
        f"permit records: Athena {permits}, published {expected_permits}"
    )
    assert apps == expected_apps, f"applications: Athena {apps}, published {expected_apps}"
    assert issued == expected_issued, (
        f"permits issued: Athena {issued}, published {expected_issued}"
    )

    duck_issued = duck.execute(
        "SELECT COUNT(*) FROM gold.fct_permits WHERE date_issued_sk IS NOT NULL"
    ).fetchone()[0]
    assert issued == duck_issued


def test_issued_by_municipality_year_matches(reader: Any, duck: Any) -> None:
    """Grouped aggregate: 43 municipality-year rows, exact match on every row."""
    sql = (
        'SELECT m.municipality_code, d."year", COUNT(*) '
        f'FROM "{DATABASE}"."fct_permits" f '
        f'JOIN "{DATABASE}"."dim_municipality" m ON f.municipality_sk = m.municipality_sk '
        f'JOIN "{DATABASE}"."dim_date" d ON f.date_issued_sk = d.date_sk '
        "WHERE f.date_issued_sk IS NOT NULL "
        "GROUP BY 1, 2"
    )
    athena = {
        (r[0], int(r[1])): int(r[2])
        for r in run_athena(reader, sql, "issued by municipality and year")
    }

    duck_rows = duck.execute(
        "SELECT m.municipality_code, d.year, COUNT(*) FROM gold.fct_permits f "
        "JOIN gold.dim_municipality m ON f.municipality_sk = m.municipality_sk "
        "JOIN gold.dim_date d ON f.date_issued_sk = d.date_sk "
        "WHERE f.date_issued_sk IS NOT NULL GROUP BY 1, 2"
    ).fetchall()
    duck_map = {(code, int(year)): int(n) for code, year, n in duck_rows}

    published = {
        (r["municipality"], int(r["year"])): int(r["permits_issued"])
        for r in _reconciliation()["permits_issued_by_municipality_year"]
    }

    assert len(published) == 43
    assert athena == duck_map, "Athena and DuckDB disagree on the grouped counts"
    assert athena == published, "Athena disagrees with the published by-year series"


def test_construction_value_sum_within_tolerance(reader: Any, duck: Any) -> None:
    """Double-precision sums: same values, possibly different order, so a stated tolerance."""
    sql = (
        f"SELECT m.municipality_code, SUM(f.construction_value_cad) "
        f'FROM "{DATABASE}"."fct_permits" f '
        f'JOIN "{DATABASE}"."dim_municipality" m ON f.municipality_sk = m.municipality_sk '
        "GROUP BY 1"
    )
    athena = {
        r[0]: float(r[1] or 0.0)
        for r in run_athena(reader, sql, "construction value sum by municipality")
    }
    duck_rows = duck.execute(
        "SELECT m.municipality_code, SUM(f.construction_value_cad) FROM gold.fct_permits f "
        "JOIN gold.dim_municipality m ON f.municipality_sk = m.municipality_sk GROUP BY 1"
    ).fetchall()
    duck_map = {code: float(total or 0.0) for code, total in duck_rows}

    assert athena.keys() == duck_map.keys()
    for code, expected in duck_map.items():
        assert athena[code] == pytest.approx(expected, rel=SUM_REL_TOLERANCE), code


def _expect_denied(label: str, call: Any, allowed_codes: set[str]) -> None:
    from botocore.exceptions import ClientError

    try:
        call()
    except ClientError as err:
        code = err.response.get("Error", {}).get("Code", "unknown")
        NEGATIVE_RESULTS.append((label, code))
        assert code in allowed_codes, f"{label}: expected denial, got {code}"
        return
    NEGATIVE_RESULTS.append((label, "ALLOWED (test fails)"))
    pytest.fail(f"{label}: the reader role was allowed. It must not be.")


def test_reader_cannot_write_curated_bucket(reader: Any) -> None:
    s3 = reader.client("s3")
    _expect_denied(
        "s3:PutObject to the curated bucket",
        lambda: s3.put_object(
            Bucket=CURATED_BUCKET, Key="probe/parity-negative-test.txt", Body=b"x"
        ),
        {"AccessDenied", "403", "AccessDeniedException"},
    )


def test_reader_cannot_create_glue_table(reader: Any) -> None:
    glue = reader.client("glue")
    probe = "parity_probe_negative"
    table_input = {
        "Name": probe,
        "TableType": "EXTERNAL_TABLE",
        "StorageDescriptor": {
            "Columns": [{"Name": "x", "Type": "int"}],
            "Location": f"s3://{CURATED_BUCKET}/probe/",
        },
    }
    _expect_denied(
        "glue:CreateTable",
        lambda: glue.create_table(DatabaseName=DATABASE, TableInput=table_input),
        {"AccessDeniedException", "AccessDenied"},
    )
    # If the create had been allowed, remove the probe. The test has already failed.
    with contextlib.suppress(Exception):
        glue.delete_table(DatabaseName=DATABASE, Name=probe)


def test_reader_cannot_delete_glue_table(reader: Any) -> None:
    """Uses a table name that does not exist, so a permitted call could not harm real data.

    A denial is the expected result. EntityNotFoundException would mean the permission
    check passed, which is a failure.
    """
    glue = reader.client("glue")
    _expect_denied(
        "glue:DeleteTable (nonexistent probe name)",
        lambda: glue.delete_table(DatabaseName=DATABASE, Name="parity_probe_does_not_exist"),
        {"AccessDeniedException", "AccessDenied"},
    )
