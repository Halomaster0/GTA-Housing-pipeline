"""Upload the exported gold Parquet to the curated S3 bucket.

    data/gold-parquet/gold.<table>.parquet  ->  s3://<curated>/gold/<table>/gold.<table>.parquet

Safe to re-run. A file already in S3 with the same SHA-256 (stored as object metadata)
is skipped. Before uploading, the Parquet row counts for the two fact tables must match
docs/measure-reconciliation.json; a mismatch stops the run, so the cloud copy can never
drift from the published September figures.

Credentials come from the named AWS profile (SSO or assumed role). Nothing is read from
a key file. Needs the aws extra:

    uv run --extra aws python scripts/aws/upload_gold.py

Bucket: --bucket, else ATHENA_CURATED_BUCKET, else `terraform output -raw curated_bucket`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pyarrow.parquet as pq
import structlog

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PARQUET_DIR = REPO_ROOT / "data" / "gold-parquet"
RECONCILIATION = REPO_ROOT / "docs" / "measure-reconciliation.json"
TERRAFORM_DIR = REPO_ROOT / "infra" / "aws"

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

log = structlog.get_logger()


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_against_reconciliation(parquet_dir: Path) -> None:
    """Stop unless the fact tables' row counts match the published reconciliation."""
    expected = json.loads(RECONCILIATION.read_text(encoding="utf-8"))["fact_totals"]
    for table in ("fct_permits", "fct_applications"):
        path = parquet_dir / f"gold.{table}.parquet"
        rows = pq.ParquetFile(path).metadata.num_rows
        if rows != expected[table]:
            raise SystemExit(
                f"{table}: Parquet has {rows} rows, reconciliation expects {expected[table]}. "
                "Export from the September warehouse (--warehouse data/warehouse-sept.duckdb) "
                "and try again. Nothing was uploaded."
            )
        log.info("row count matches reconciliation", table=table, rows=rows)


def resolve_bucket(explicit: str | None) -> str:
    if explicit:
        return explicit
    if os.environ.get("ATHENA_CURATED_BUCKET"):
        return os.environ["ATHENA_CURATED_BUCKET"]
    result = subprocess.run(
        ["terraform", f"-chdir={TERRAFORM_DIR}", "output", "-raw", "curated_bucket"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise SystemExit(
            "No bucket given. Pass --bucket, set ATHENA_CURATED_BUCKET, or run "
            "`terraform apply` in infra/aws first."
        )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--bucket", default=None)
    parser.add_argument("--parquet-dir", default=str(DEFAULT_PARQUET_DIR))
    parser.add_argument("--profile", default=os.environ.get("AWS_PROFILE"))
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-2"))
    args = parser.parse_args()

    # Imported after parsing so `--help` works without the aws extra installed.
    import boto3
    from botocore.exceptions import ClientError

    if not args.profile:
        raise SystemExit("Set AWS_PROFILE (or pass --profile) to the named SSO profile.")

    parquet_dir = Path(args.parquet_dir)
    missing = [t for t in GOLD_TABLES if not (parquet_dir / f"gold.{t}.parquet").exists()]
    if missing:
        raise SystemExit(f"Missing Parquet for: {', '.join(missing)}. Run make export-gold first.")

    check_against_reconciliation(parquet_dir)

    bucket = resolve_bucket(args.bucket)
    s3 = boto3.Session(profile_name=args.profile, region_name=args.region).client("s3")

    uploaded = skipped = 0
    for table in GOLD_TABLES:
        local = parquet_dir / f"gold.{table}.parquet"
        key = f"gold/{table}/gold.{table}.parquet"
        digest = sha256_of(local)

        try:
            head = s3.head_object(Bucket=bucket, Key=key)
            if head.get("Metadata", {}).get("sha256") == digest:
                skipped += 1
                log.info("unchanged, skipped", table=table)
                continue
        except ClientError:
            pass  # 404: not uploaded yet

        s3.upload_file(
            str(local),
            bucket,
            key,
            ExtraArgs={
                "Metadata": {"sha256": digest},
                "ServerSideEncryption": "AES256",
            },
        )
        uploaded += 1
        log.info("uploaded", table=table, bytes=local.stat().st_size)

    print(f"done: {uploaded} uploaded, {skipped} unchanged, {len(GOLD_TABLES)} tables total")
    for table in GOLD_TABLES:
        listing = s3.list_objects_v2(Bucket=bucket, Prefix=f"gold/{table}/")
        objects = listing.get("Contents", [])
        size = sum(o["Size"] for o in objects)
        print(f"  gold/{table}/: {len(objects)} object(s), {size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
