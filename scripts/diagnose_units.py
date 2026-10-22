"""Explain a move in the dwelling-unit measure.

Written after the 2026-10-22 reconcile: Toronto's net units rose 38.8% while its
permit rows rose 0.71% and the other two municipalities' mean units per row held
steady to two decimal places. A measure that moves two orders of magnitude faster
than its row count is either a handful of outliers or a parse change, and the
data tests do not catch it because they check row-count deltas, not measure
deltas.

Read-only. Run: uv run python scripts/diagnose_units.py [--municipality TOR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WAREHOUSE = REPO_ROOT / "data" / "warehouse.duckdb"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--municipality", default="TOR", help="Municipality code (default TOR)")
    ap.add_argument("--warehouse", default=str(DEFAULT_WAREHOUSE))
    ap.add_argument("--top", type=int, default=20, help="How many largest rows to list")
    args = ap.parse_args()

    path = Path(args.warehouse)
    if not path.exists():
        print(f"no warehouse at {path} — run the transform first", file=sys.stderr)
        return 2

    con = duckdb.connect(str(path), read_only=True)
    code = args.municipality
    where = (
        "FROM gold.fct_permits f JOIN gold.dim_municipality m USING (municipality_sk) "
        f"WHERE m.municipality_code = '{code}' AND f.unit_count_net_new IS NOT NULL"
    )

    total, rows_with = con.execute(f"SELECT SUM(f.unit_count_net_new), COUNT(*) {where}").fetchone()
    print(f"\n{code}: {total:,} units across {rows_with:,} rows carrying a count")
    print(f"mean {total / rows_with:.2f} units per such row\n")

    print(f"-- {args.top} largest rows")
    print(f"{'permit_number':24} {'units':>10}  status")
    cum = 0
    for permit, units, status in con.execute(
        f"SELECT f.permit_number, f.unit_count_net_new, f.status_raw {where} "
        f"ORDER BY f.unit_count_net_new DESC LIMIT {args.top}"
    ).fetchall():
        cum += units
        print(f"{str(permit)[:24]:24} {units:>10,}  {str(status)[:28]}")
    print(
        f"\nthose {args.top} rows alone carry {cum:,} units "
        f"({100 * cum / total:.1f}% of the municipality total)"
    )

    print("\n-- distribution")
    buckets = con.execute(
        f"SELECT CASE "
        "WHEN f.unit_count_net_new < 0 THEN 'negative (demolition)' "
        "WHEN f.unit_count_net_new = 0 THEN '0' "
        "WHEN f.unit_count_net_new <= 2 THEN '1-2' "
        "WHEN f.unit_count_net_new <= 10 THEN '3-10' "
        "WHEN f.unit_count_net_new <= 100 THEN '11-100' "
        "WHEN f.unit_count_net_new <= 1000 THEN '101-1000' "
        "ELSE 'over 1000' END AS bucket, "
        "COUNT(*), SUM(f.unit_count_net_new) "
        f"{where} GROUP BY 1 ORDER BY 3 DESC"
    ).fetchall()
    print(f"{'bucket':24} {'rows':>10} {'units':>14}")
    for bucket, n, units in buckets:
        print(f"{bucket:24} {n:>10,} {units:>14,}")

    print(
        "\nA few rows carrying most of the total means outliers, not growth. "
        "Check those permit numbers against the live source before any unit "
        "figure is published (ADR-0003)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
