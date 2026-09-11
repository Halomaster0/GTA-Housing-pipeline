"""Export gold star-schema tables for the serving layer.

Default format is parquet — the Fabric publish-path input (ADR-0008).
``--format csv`` exists for one practical reason: Power BI Desktop's Parquet
connector takes a URL, not a local file, so local serving via Desktop uses
Get Data → Text/CSV instead (ADR-0010 path). Same rows, same grain —
``reconcile_measures.py`` verifies counts against the warehouse either way.

Usage:
    python scripts/export_gold_parquet.py [--warehouse PATH] [--out-dir DIR]
        [--format parquet|csv]

Exit non-zero if the warehouse is missing or any table export fails.
Row counts are printed per table.
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
        default=None,
        help="Directory for exported files (under gitignored data/). "
        "Defaults to data/gold-parquet (or data/gold-csv with --format csv).",
    )
    parser.add_argument(
        "--format",
        choices=("parquet", "csv"),
        default="parquet",
        help="Export format. Use csv for Power BI Desktop local import.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    warehouse = Path(args.warehouse)
    if not warehouse.exists():
        print(f"export_gold_parquet: warehouse not found: {warehouse}", file=sys.stderr)
        print("Run `make transform` (or `python -m src.transform --all`) first.", file=sys.stderr)
        return 1

    out_dir = (
        Path(args.out_dir)
        if args.out_dir
        else REPO_ROOT / "data" / ("gold-parquet" if args.format == "parquet" else "gold-csv")
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        for table in GOLD_TABLES:
            suffix = "parquet" if args.format == "parquet" else "csv"
            target = out_dir / f"gold.{table}.{suffix}"
            # ORDER BY first column keeps file bytes deterministic for a given
            # warehouse content; row counts (not hashes) are the contract.
            if args.format == "parquet":
                copy_sql = (
                    f"COPY (SELECT * FROM gold.{table} ORDER BY 1) "
                    f"TO '{target.as_posix()}' (FORMAT PARQUET)"
                )
            else:
                copy_sql = (
                    f"COPY (SELECT * FROM gold.{table} ORDER BY 1) "
                    f"TO '{target.as_posix()}' (FORMAT CSV, HEADER)"
                )
            con.execute(copy_sql)
            rows = con.execute(f"SELECT COUNT(*) FROM gold.{table}").fetchone()[0]
            print(f"gold.{table}: {rows} rows -> {target.name}")
    finally:
        con.close()
    print(f"export complete: {len(GOLD_TABLES)} tables in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
