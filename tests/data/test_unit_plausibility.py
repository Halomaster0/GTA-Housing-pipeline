"""Unit counts above a plausibility ceiling must be known, not merely present.

Added after 2026-10-22, when one Toronto permit carrying 100,000 dwelling units
moved a published figure 38.8% while row counts moved 0.71%. The existing tests
check row-count deltas, so nothing failed. This checks the measure itself.

Skipped when no warehouse exists (CI without bronze), matching test_warehouse.py.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
import yaml

from src.transform.runner import DEFAULT_WAREHOUSE

pytestmark = pytest.mark.data

EXCEPTIONS = Path(__file__).resolve().parents[2] / "docs" / "data-exceptions.yml"


def _exceptions() -> tuple[int, set[str]]:
    data = yaml.safe_load(EXCEPTIONS.read_text(encoding="utf-8"))
    ceiling = int(data["unit_count_ceiling"])
    known = {str(p["permit_number"]) for p in data.get("permits") or []}
    return ceiling, known


def test_exceptions_file_is_well_formed() -> None:
    ceiling, known = _exceptions()
    assert ceiling > 0, "unit_count_ceiling must be positive"
    assert known, "no exceptions listed — delete the entry rather than leaving it empty"


def test_implausible_unit_counts_are_all_documented() -> None:
    warehouse = Path(DEFAULT_WAREHOUSE)
    if not warehouse.exists():
        pytest.skip("no local warehouse — run the transform first")

    ceiling, known = _exceptions()
    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        rows = con.execute(
            "SELECT f.permit_number, f.unit_count_net_new, m.municipality_code "
            "FROM gold.fct_permits f "
            "JOIN gold.dim_municipality m USING (municipality_sk) "
            "WHERE f.unit_count_net_new > ? "
            "ORDER BY f.unit_count_net_new DESC",
            [ceiling],
        ).fetchall()
    finally:
        con.close()

    undocumented = [(p, u, m) for p, u, m in rows if str(p) not in known]
    assert not undocumented, (
        "unit counts above the "
        f"{ceiling:,} ceiling with no entry in docs/data-exceptions.yml: "
        + "; ".join(f"{m} {p} = {u:,} units" for p, u, m in undocumented)
        + ". Check each against the live source, then record it with a reason "
        "and a decision. Do not raise the ceiling to make this pass."
    )
