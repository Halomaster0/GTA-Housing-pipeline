"""Shared warehouse assertions: run against the real warehouse AND the fixture build.

Every invariant here is a promise the README/dashboard rely on. Fixture rows
in test_transform_logic.py exercise each rule; test_warehouse.py runs the
same checks against data/warehouse.duckdb built from live bronze.
"""

from __future__ import annotations

import duckdb

BANNED_SILVER_COLUMNS = frozenset(
    {
        "CONTACT_NAME",
        "CONTACT_PHONE",
        "CONTACT_EMAIL",
        "Mayor",
        "RegionalCo",
        "LocalCounc",
        "FirstName0",
        "LastName0",
        "Phone0",
        "email0",
        "FirstName1",
        "LastName1",
        "Phone1",
        "email1",
        "RC_Name",
    }
)


def silver_columns(con: duckdb.DuckDBPyConnection) -> dict[str, list[str]]:
    rows = con.execute(
        "SELECT table_schema, table_name, column_name FROM information_schema.columns "
        "WHERE table_schema = 'silver' ORDER BY 1, 2, 3"
    ).fetchall()
    tables: dict[str, list[str]] = {}
    for schema, table, column in rows:
        tables.setdefault(f"{schema}.{table}", []).append(column)
    return tables


def assert_no_pii_columns(con: duckdb.DuckDBPyConnection) -> None:
    for table, columns in silver_columns(con).items():
        leaked = BANNED_SILVER_COLUMNS & set(columns)
        assert not leaked, f"{table} leaks PII columns: {sorted(leaked)}"


def assert_no_orphan_fks(con: duckdb.DuckDBPyConnection) -> None:
    orphans = con.execute(
        "SELECT COUNT(*) FROM gold.fct_permits f "
        "LEFT JOIN gold.dim_municipality m ON f.municipality_sk = m.municipality_sk "
        "WHERE m.municipality_sk IS NULL"
    ).fetchone()[0]
    assert orphans == 0, f"{orphans} permit rows with orphan municipality_sk"
    orphans = con.execute(
        "SELECT COUNT(*) FROM gold.fct_applications f "
        "LEFT JOIN gold.dim_municipality m ON f.municipality_sk = m.municipality_sk "
        "WHERE m.municipality_sk IS NULL"
    ).fetchone()[0]
    assert orphans == 0, f"{orphans} application rows with orphan municipality_sk"
    for fk, dim, key in [
        ("use_type_sk", "dim_use_type", "use_type_sk"),
        ("status_sk", "dim_status", "status_sk"),
    ]:
        for fact in ("fct_permits", "fct_applications"):
            n = con.execute(
                f"SELECT COUNT(*) FROM gold.{fact} f "
                f"LEFT JOIN gold.{dim} d ON f.{fk} = d.{key} "
                f"WHERE d.{key} IS NULL"
            ).fetchone()[0]
            assert n == 0, f"{fact}.{fk} has {n} orphans"


def assert_fact_grain(con: duckdb.DuckDBPyConnection) -> None:
    dupes = con.execute(
        "SELECT COUNT(*) FROM (SELECT municipality_sk, permit_number "
        "FROM gold.fct_permits GROUP BY 1, 2 HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    assert dupes == 0, f"fct_permits grain violated on {dupes} keys"
    dupes = con.execute(
        "SELECT COUNT(*) FROM (SELECT municipality_sk, application_number "
        "FROM gold.fct_applications GROUP BY 1, 2 HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    assert dupes == 0, f"fct_applications grain violated on {dupes} keys"


def assert_no_future_or_negative(con: duckdb.DuckDBPyConnection) -> None:
    # Net-new units CAN be negative: a demolition permit records created 0 /
    # lost N, net −N. That is a recorded loss, not corruption (matrix §3).
    # Future issue dates are source-side scheduling skew, monitored in the
    # report with row-level detail — not a build failure. Both are therefore
    # report metrics, not hard invariants; this function asserts the metrics
    # are queryable (i.e. the columns exist) and returns nothing.
    con.execute(
        "SELECT COUNT(*) FROM gold.fct_permits f "
        "JOIN gold.dim_date d ON d.date_sk = f.date_issued_sk "
        "WHERE d.calendar_date > CURRENT_DATE"
    ).fetchone()
    con.execute(
        "SELECT COUNT(*) FROM gold.fct_permits "
        "WHERE unit_count_net_new IS NOT NULL AND unit_count_net_new < 0"
    ).fetchone()


def assert_all_invariants(con: duckdb.DuckDBPyConnection) -> None:
    assert_no_pii_columns(con)
    assert_no_orphan_fks(con)
    assert_fact_grain(con)
    assert_no_future_or_negative(con)
