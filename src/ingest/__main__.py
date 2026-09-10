"""Extract-and-land CLI: `python -m src.ingest --all`.

One connector per source family, shared runtime (base.py), checkpointed,
drift-detecting. Bronze lands at data/bronze/{source}/ingest_date={date}/
with a manifest.json per run. Same-date reruns replace the partition
wholesale (idempotent); cross-date partitions are never touched.

Exit code is the contract: 0 only if every source pulled, held its field
hash, and passed its key policy. Drift or duplicate unique keys fail loudly.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any

import httpx

from src.ingest.arcgis_hub import ArcgisPull, pull_arcgis
from src.ingest.base import (
    IngestError,
    Partition,
    get_checkpoint,
    save_checkpoint,
    save_json,
    utc_today,
    write_manifest,
)
from src.ingest.drift import DriftDetected, check_drift
from src.ingest.keys import check_keys
from src.ingest.spec import SourceSpec, load_specs
from src.ingest.statcan import pull_statcan_meta
from src.ingest.toronto_ckan import CkanPull, pull_ckan

STATCAN_PRODUCTS = [34100292]


def _run_ckan_arcgis(client: httpx.Client, spec: SourceSpec, ingest_date: str) -> dict[str, Any]:
    started = time.monotonic()
    partition = Partition(spec.id, ingest_date)
    # Same-date reruns always replace the partition wholesale. There is no
    # mid-run resume: a previous failed run may have landed complete part
    # files before failing at drift/key checks, so resuming from a stored
    # offset would append duplicates. Fresh pulls are cheap (largest feed is
    # ~90 pages); checkpoints remain as progress observability only.
    partition.reset()
    save_checkpoint(spec.id, {"ingest_date": ingest_date, "done": False})
    part_index = 0

    params = spec.params
    pull: CkanPull | ArcgisPull
    if spec.family == "ckan":
        pull = pull_ckan(
            client, spec.id, str(params["resource_id"]), int(params["ckan_page_size"]), ingest_date
        )
        records, fields, reported_total = pull.records, pull.fields, pull.reported_total
        page_size = int(params["ckan_page_size"])
    else:
        pull = pull_arcgis(
            client,
            spec.id,
            str(params["layer_url"]),
            int(params["arcgis_page_size"]),
            ingest_date,
            geometry=bool(params.get("geometry", False)),
        )
        records, fields, reported_total = pull.records, pull.fields, pull.reported_total
        page_size = int(params["arcgis_page_size"])

    # Bronze lands the full pull, including on drift/key failure: raw is
    # evidence, and the manifest records the failure. Nothing is hidden.
    total_bytes = 0
    for part_index, start in enumerate(range(0, len(records), page_size)):
        total_bytes += partition.land_parquet(
            records[start : start + page_size], f"part-{part_index:05d}"
        )

    drift_status = "ok"
    try:
        outcome = check_drift(spec.id, fields, ingest_date)
        field_hash = outcome.field_hash
    except DriftDetected as exc:
        drift_status = f"drift: {exc}"
        from src.ingest.base import sha256_fields

        field_hash = sha256_fields(fields)

    key = check_keys(spec.id, records, spec.business_key, spec.key_policy)
    key_observe: dict[str, Any] | None = None
    if spec.key_observe:
        observed = check_keys(spec.id, records, spec.key_observe, "observe")
        key_observe = {
            "columns": observed.key_columns,
            "rows": observed.rows,
            "distinct": observed.distinct,
            "duplicates": observed.duplicates,
            "detail": observed.detail,
        }

    if drift_status != "ok":
        status = drift_status
    elif not key.passed:
        status = f"key-fail: {key.detail}"
    else:
        status = "ok"

    duration_s = round(time.monotonic() - started, 1)
    count_match = reported_total is None or reported_total == len(records)
    manifest = {
        "source": spec.id,
        "family": spec.family,
        "ingest_date": ingest_date,
        "row_count": len(records),
        "reported_total": reported_total,
        "count_match": count_match,
        "bytes": total_bytes,
        "duration_s": duration_s,
        "status": status,
        "field_hash": field_hash,
        "n_fields": len(fields),
        "key": {
            "columns": key.key_columns,
            "policy": key.policy,
            "rows": key.rows,
            "distinct": key.distinct,
            "duplicates": key.duplicates,
            "passed": key.passed,
            "detail": key.detail,
            "observe": key_observe,
        },
        "facts_feed": spec.facts_feed,
        "files": partition.part_files(),
    }
    write_manifest(partition, manifest)
    checkpoint = get_checkpoint(spec.id)
    checkpoint.update({"ingest_date": ingest_date, "done": True})
    save_checkpoint(spec.id, checkpoint)
    return manifest


def _run_statcan_meta(spec: SourceSpec, ingest_date: str) -> dict[str, Any]:
    started = time.monotonic()
    partition = Partition(spec.id, ingest_date)
    partition.reset()
    with httpx.Client(follow_redirects=True) as client:
        metadata = pull_statcan_meta(client, STATCAN_PRODUCTS)
    out = partition.path / "metadata.json"
    partition.path.mkdir(parents=True, exist_ok=True)
    save_json(out, metadata)
    duration_s = round(time.monotonic() - started, 1)
    manifest = {
        "source": spec.id,
        "family": spec.family,
        "ingest_date": ingest_date,
        "row_count": len(metadata),
        "reported_total": None,
        "count_match": True,
        "bytes": out.stat().st_size,
        "duration_s": duration_s,
        "status": "ok",
        "field_hash": None,
        "n_fields": 0,
        "key": {"columns": [], "policy": "observe", "detail": "metadata-only pull"},
        "facts_feed": False,
        "files": ["metadata.json"],
        "products": STATCAN_PRODUCTS,
    }
    write_manifest(partition, manifest)
    return manifest


def run_source(client: httpx.Client, spec: SourceSpec, ingest_date: str) -> dict[str, Any]:
    if spec.family == "statcan-meta":
        return _run_statcan_meta(spec, ingest_date)
    return _run_ckan_arcgis(client, spec, ingest_date)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract and land bronze partitions.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Pull every spec in config/ingest.yml.")
    group.add_argument("--source", help="Pull a single source id.")
    parser.add_argument(
        "--ingest-date", default=None, help="Partition date YYYY-MM-DD (default: today UTC)."
    )
    args = parser.parse_args(argv)

    ingest_date = args.ingest_date or utc_today()
    try:
        specs = load_specs()
    except IngestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.source:
        specs = [s for s in specs if s.id == args.source]
        if not specs:
            print(f"No ingest spec with id '{args.source}'", file=sys.stderr)
            return 2

    manifests: list[dict[str, Any]] = []
    failures = 0
    with httpx.Client(follow_redirects=True) as client:
        for spec in specs:
            try:
                manifest = run_source(client, spec, ingest_date)
            except IngestError as exc:
                print(f"[{spec.id}] ERROR: {exc}", file=sys.stderr)
                failures += 1
                continue
            manifests.append(manifest)
            print(
                f"[{manifest['source']}] rows={manifest['row_count']} "
                f"reported={manifest['reported_total']} "
                f"status={manifest['status']} files={len(manifest['files'])}"
            )
            if str(manifest["status"]) != "ok":
                failures += 1

    bad_counts = [m for m in manifests if not m["count_match"]]
    for manifest in bad_counts:
        print(
            f"[{manifest['source']}] NOTE: landed {manifest['row_count']} rows but source "
            f"reported {manifest['reported_total']} (source mutated mid-pull or paging gap)",
        )
    if failures:
        print(f"\n{failures} of {len(specs)} source(s) failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
