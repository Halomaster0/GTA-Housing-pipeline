"""Transform CLI: `python -m src.transform --all [--report]."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from src.transform.runner import (
    DEFAULT_BRONZE_ROOT,
    DEFAULT_WAREHOUSE,
    build_all,
    write_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build bronze -> silver -> gold in DuckDB.")
    parser.add_argument("--all", action="store_true", help="Build all layers.")
    parser.add_argument(
        "--report", action="store_true", help="Regenerate docs/data-quality-report.md."
    )
    parser.add_argument("--warehouse", default=str(DEFAULT_WAREHOUSE))
    parser.add_argument("--bronze-root", default=str(DEFAULT_BRONZE_ROOT))
    parser.add_argument("--ingest-date", default=None, help="Default: today UTC.")
    args = parser.parse_args(argv)

    ingest_date = args.ingest_date or datetime.now(UTC).strftime("%Y-%m-%d")
    warehouse = Path(args.warehouse)
    bronze_root = Path(args.bronze_root)
    if args.all:
        if warehouse.exists():
            warehouse.unlink()
        build_all(warehouse, bronze_root, ingest_date)
        print(f"warehouse built: {warehouse}")
    if args.report:
        if not warehouse.exists():
            raise SystemExit(f"no warehouse at {warehouse} — run with --all first")
        out = write_report(warehouse, bronze_root, ingest_date)
        print(f"report written: {out}")
    if not args.all and not args.report:
        raise SystemExit("nothing to do — pass --all and/or --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
