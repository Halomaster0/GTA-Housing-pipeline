"""Warehouse invariants against the live build (data/warehouse.duckdb).

Skipped when no warehouse exists (e.g. CI without bronze). The same
invariants run unconditionally on synthetic fixtures in
test_transform_logic.py, so CI still covers the logic.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from src.transform.runner import DEFAULT_WAREHOUSE
from tests.data.invariants import assert_all_invariants

pytestmark = pytest.mark.data


def test_live_warehouse_invariants() -> None:
    warehouse = Path(DEFAULT_WAREHOUSE)
    if not warehouse.exists():
        pytest.skip("no local warehouse — run make transform first")
    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        assert_all_invariants(con)
        muni = con.execute(
            "SELECT municipality_code FROM gold.dim_municipality ORDER BY 1"
        ).fetchall()
        assert [r[0] for r in muni] == ["BRAM", "CALE", "MISS", "PEEL", "TOR"]
        facts = con.execute(
            "SELECT COUNT(*) FROM gold.fct_permits f "
            "JOIN gold.dim_municipality m USING (municipality_sk) "
            "WHERE m.municipality_code IN ('PEEL', 'CALE')"
        ).fetchone()[0]
        assert facts == 0, "Peel/Caledon must have zero fact rows (ADR-0004)"
        linked = con.execute(
            "SELECT COUNT(*) FROM gold.fct_permits WHERE related_application_number IS NOT NULL"
        ).fetchone()[0]
        assert linked == 0, "no proven link key yet (ADR-0006)"
    finally:
        con.close()
