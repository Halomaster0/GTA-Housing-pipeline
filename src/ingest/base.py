"""Shared ingestion runtime: retried HTTP, checkpoints, manifests, parquet landing.

Every connector pulls through these helpers so retries, resume, and the
manifest contract behave identically across source families. Nothing here
knows about a specific municipality — family specifics live in
toronto_ckan.py, arcgis_hub.py, and statcan.py.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_BRONZE = REPO_ROOT / "data" / "bronze"
STATE_DIR = REPO_ROOT / "state"
CHECKPOINT_PATH = STATE_DIR / "ingest_checkpoints.json"
HASH_PATH = STATE_DIR / "schema_hashes.json"

REQUEST_TIMEOUT_SECONDS = 60.0
MAX_ATTEMPTS = 4
BACKOFF_BASE_SECONDS = 2.0


class IngestError(RuntimeError):
    """A loud, non-silent ingestion failure. Never swallowed by callers."""


def utc_today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def sha256_fields(fields: list[str]) -> str:
    """Stable hash of a source's field set. Order-insensitive, dup-sensitive."""
    canonical = "\n".join(sorted(fields))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
        fh.write("\n")


def fetch_json(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: Any | None = None,
) -> Any:
    """GET/POST JSON with exponential backoff on transport/timeout/5xx/429.

    4xx (other than 429) is a loud immediate failure: the request is wrong,
    retrying will not fix it. A response that is not JSON is a loud failure.
    """
    last_error = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            if method.upper() == "POST":
                response = client.post(url, json=json_body, timeout=REQUEST_TIMEOUT_SECONDS)
            else:
                response = client.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        else:
            if response.status_code == 429 or response.status_code >= 500:
                last_error = f"HTTP {response.status_code}: {response.text[:300]!r}"
            elif response.status_code >= 400:
                raise IngestError(f"HTTP {response.status_code} for {url}: {response.text[:300]!r}")
            else:
                try:
                    return response.json()
                except ValueError as exc:
                    raise IngestError(f"non-JSON response for {url}: {exc}") from exc
        if attempt < MAX_ATTEMPTS:
            time.sleep(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))
    raise IngestError(f"gave up after {MAX_ATTEMPTS} attempts for {url}: {last_error}")


@dataclass(frozen=True)
class Partition:
    """One immutable bronze partition: data/bronze/{source}/ingest_date={date}/."""

    source_id: str
    ingest_date: str

    @property
    def path(self) -> Path:
        return DATA_BRONZE / self.source_id / f"ingest_date={self.ingest_date}"

    def reset(self) -> None:
        """Same-date reruns replace the partition wholesale (idempotence).

        Cross-date partitions are never touched — raw history is immutable.
        """
        if self.path.exists():
            for child in sorted(self.path.iterdir()):
                if child.is_file():
                    child.unlink()

    def land_parquet(self, records: list[dict[str, Any]], stem: str) -> int:
        """Append records as one parquet part file. Returns bytes written."""
        self.path.mkdir(parents=True, exist_ok=True)
        table = pa.Table.from_pylist(records)
        out = self.path / f"{stem}.parquet"
        pq.write_table(table, out)
        return out.stat().st_size

    def part_files(self) -> list[str]:
        return sorted(p.name for p in self.path.glob("part-*.parquet"))


def get_checkpoint(source_id: str) -> dict[str, Any]:
    checkpoints = load_json(CHECKPOINT_PATH, {})
    if not isinstance(checkpoints, dict):
        raise IngestError(f"{CHECKPOINT_PATH} is corrupt: top level is not an object")
    entry = checkpoints.get(source_id, {})
    return entry if isinstance(entry, dict) else {}


def save_checkpoint(source_id: str, entry: dict[str, Any]) -> None:
    checkpoints = load_json(CHECKPOINT_PATH, {})
    if not isinstance(checkpoints, dict):
        checkpoints = {}
    checkpoints[source_id] = entry
    save_json(CHECKPOINT_PATH, checkpoints)


def write_manifest(partition: Partition, manifest: dict[str, Any]) -> Path:
    out = partition.path / "manifest.json"
    save_json(out, manifest)
    return out
