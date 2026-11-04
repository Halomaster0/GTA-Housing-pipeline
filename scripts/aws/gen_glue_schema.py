"""Generate infra/aws/tables.auto.tfvars.json from the exported gold Parquet schemas.

The Glue tables in infra/aws/glue.tf take their column lists from this file, so the
Terraform cannot drift from the models: re-export, re-generate, and the plan shows
any column change.

Arrow -> Glue (Hive) type mapping
    bool                  -> boolean
    int8                  -> tinyint
    int16                 -> smallint
    int32                 -> int
    int64                 -> bigint
    float16 / float32     -> float
    float64               -> double
    decimal128(p, s)      -> decimal(p,s)
    string / large_string -> string
    binary / large_binary -> binary
    date32 / date64       -> date
    timestamp             -> timestamp

Any other Arrow type stops the run with an error. Unsigned integers are not mapped on
purpose: a silent widening would hide a model change.

Usage:
    uv run python scripts/aws/gen_glue_schema.py [--parquet-dir DIR]
    uv run python scripts/aws/gen_glue_schema.py --check   # drift check (no writes)

Exit 0 on success. --check exits 1 if the committed file differs from the schemas.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PARQUET_DIR = REPO_ROOT / "data" / "gold-parquet"
OUTPUT = REPO_ROOT / "infra" / "aws" / "tables.auto.tfvars.json"

# Must match GOLD_TABLES in scripts/export_gold_parquet.py.
GOLD_TABLES = [
    "dim_date",
    "dim_municipality",
    "dim_geography",
    "dim_use_type",
    "dim_status",
    "fct_permits",
    "fct_applications",
]


def glue_type(arrow_type: pa.DataType) -> str:
    """Map one Arrow type to its Glue type. Raises on anything unmapped."""
    if pa.types.is_boolean(arrow_type):
        return "boolean"
    if pa.types.is_int8(arrow_type):
        return "tinyint"
    if pa.types.is_int16(arrow_type):
        return "smallint"
    if pa.types.is_int32(arrow_type):
        return "int"
    if pa.types.is_int64(arrow_type):
        return "bigint"
    if pa.types.is_float16(arrow_type) or pa.types.is_float32(arrow_type):
        return "float"
    if pa.types.is_float64(arrow_type):
        return "double"
    if pa.types.is_decimal(arrow_type):
        return f"decimal({arrow_type.precision},{arrow_type.scale})"
    if pa.types.is_string(arrow_type) or pa.types.is_large_string(arrow_type):
        return "string"
    if pa.types.is_binary(arrow_type) or pa.types.is_large_binary(arrow_type):
        return "binary"
    if pa.types.is_date(arrow_type):
        return "date"
    if pa.types.is_timestamp(arrow_type):
        return "timestamp"
    raise ValueError(f"unmapped Arrow type: {arrow_type}")


def build_tables(parquet_dir: Path) -> dict[str, Any]:
    """Read each gold table's Parquet schema and return the tfvars structure."""
    tables: dict[str, Any] = {}
    for name in GOLD_TABLES:
        path = parquet_dir / f"gold.{name}.parquet"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} is missing. Run `uv run python scripts/export_gold_parquet.py "
                "--warehouse data/warehouse-sept.duckdb --out-dir data/gold-parquet` first."
            )
        schema = pq.read_schema(path)
        tables[name] = {
            "columns": [
                {"name": field.name, "type": glue_type(field.type)} for field in schema
            ]
        }
    return {"tables": tables}


def render(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--parquet-dir", default=str(DEFAULT_PARQUET_DIR))
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the committed tables.auto.tfvars.json differs from the schemas.",
    )
    args = parser.parse_args()

    payload = build_tables(Path(args.parquet_dir))
    text = render(payload)

    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != text:
            print(f"{OUTPUT.relative_to(REPO_ROOT)} is out of date. Run the generator.", file=sys.stderr)
            return 1
        print("tables.auto.tfvars.json matches the Parquet schemas.")
        return 0

    OUTPUT.write_text(text, encoding="utf-8")
    for name, table in payload["tables"].items():
        print(f"{name}: {len(table['columns'])} columns")
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
