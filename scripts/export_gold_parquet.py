"""Export gold star-schema tables to parquet for the serving layer.

This is the Fabric publish-path input (ADR-0008): ``gold/*.parquet`` is what
a future ``fabric-architect`` session uploads to OneLake. The export is a
pure function of the local warehouse — no cloud, no cost, no credentials.

Usage:
    python scripts/export_gold_parquet.py [--warehouse PATH] [--out-dir DIR]

Exit non-zero if the warehouse is missing or any table export fails.
Row counts are printed per table; ``reconcile_measures.py`` re-verifies
them against the warehouse independently.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

GOLD_TABLES = [
    "dim_date",
    "dim_municipality",
    "dim_geography",
    "dim_use_type",
    "dim_status",
    "fct_permits",
    "fct_applications",
]

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warehouse",
        default=str(REPO_ROOT / "data" / "warehouse.duckdb"),
        help="Path to the DuckDB warehouse built by `make transform`.",
    )
    parser.add_argument(
        "--out-dir",
        default=str(REPO_ROOT / "data" / "gold-parquet"),
        help="Directory for exported parquet files (under gitignored data/).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    warehouse = Path(args.warehouse)
    if not warehouse.exists():
        print(f"export_gold_parquet: warehouse not found: {warehouse}", file=sys.stderr)
        print("Run `make transform` (or `python -m src.transform --all`) first.", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        for table in GOLD_TABLES:
            target = out_dir / f"gold.{table}.parquet"
            # ORDER BY first column keeps file bytes deterministic for a given
            # warehouse content; row counts (not hashes) are the contract.
            con.execute(
                f"COPY (SELECT * FROM gold.{table} ORDER BY 1) "
                f"TO '{target.as_posix()}' (FORMAT PARQUET)"
            )
            rows = con.execute(f"SELECT COUNT(*) FROM gold.{table}").fetchone()[0]
            print(f"gold.{table}: {rows} rows -> {target.name}")
    finally:
        con.close()
    print(f"export complete: {len(GOLD_TABLES)} tables in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
