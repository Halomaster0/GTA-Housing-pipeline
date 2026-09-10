"""Schema-drift detector: a changed field set fails loudly, never silently.

The first run for a source seeds state/schema_hashes.json (nothing to compare
against — recording, not passing). Every later run compares the live field
list hash against the seed; a mismatch writes a human-readable diff to
docs/drift/{date}-{source_id}.md and raises DriftDetected. The caller lands
the raw partition anyway (evidence preserved) but exits non-zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.ingest.base import HASH_PATH, REPO_ROOT, IngestError, load_json, save_json, sha256_fields

DRIFT_DIR = REPO_ROOT / "docs" / "drift"


@dataclass(frozen=True)
class DriftOutcome:
    source_id: str
    field_hash: str
    fields: list[str]
    changed: bool


class DriftDetected(IngestError):
    """Raised after the diff file is written. Callers must not swallow this."""


def check_drift(source_id: str, fields: list[str], ingest_date: str) -> DriftOutcome:
    field_hash = sha256_fields(fields)
    hashes = load_json(HASH_PATH, {})
    if not isinstance(hashes, dict):
        raise IngestError(f"{HASH_PATH} is corrupt: top level is not an object")
    prior = hashes.get(source_id)
    if prior is None:
        hashes[source_id] = {
            "sha256": field_hash,
            "fields": sorted(fields),
            "seeded_on": ingest_date,
        }
        save_json(HASH_PATH, hashes)
        return DriftOutcome(source_id, field_hash, sorted(fields), changed=False)

    prior_hash = str(prior.get("sha256", ""))
    prior_fields = [str(f) for f in prior.get("fields", [])]
    if prior_hash == field_hash:
        return DriftOutcome(source_id, field_hash, sorted(fields), changed=False)

    added = sorted(set(fields) - set(prior_fields))
    removed = sorted(set(prior_fields) - set(fields))
    stamped = datetime.now(UTC).isoformat()
    diff_path = DRIFT_DIR / f"{ingest_date}-{source_id}.md"
    DRIFT_DIR.mkdir(parents=True, exist_ok=True)
    diff_path.write_text(
        "# Schema drift — "
        + source_id
        + "\n\nDetected: "
        + stamped
        + "\nPrior hash: `"
        + prior_hash
        + "`\nCurrent hash: `"
        + field_hash
        + "`\n\n## Added\n\n"
        + "\n".join(f"- `{f}`" for f in added)
        + "\n\n## Removed\n\n"
        + "\n".join(f"- `{f}`" for f in removed)
        + "\n",
        encoding="utf-8",
    )
    raise DriftDetected(
        f"{source_id}: field set changed (added={added}, removed={removed}); diff at {diff_path}"
    )


def drift_diff_path(ingest_date: str, source_id: str) -> Path:
    return DRIFT_DIR / f"{ingest_date}-{source_id}.md"
