"""Key-stability checker: the Gate 1 condition (iii-c) as runnable code.

After every pull, the declared business key is measured: rows, distinct key
values, duplicates. Policy `unique` fails loudly on any duplicate (proving
assumption A9 per source instead of assuming it); policy `observe` records
the counts for sources proven non-unique (Toronto applications — ADR-0005).

A missing key column is a loud failure under either policy: silently
skipping the check would be worse than no check.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ingest.base import IngestError


@dataclass(frozen=True)
class KeyCheck:
    source_id: str
    key_columns: list[str]
    policy: str
    rows: int
    distinct: int
    duplicates: int
    passed: bool
    detail: str


def check_keys(
    source_id: str,
    records: list[dict[str, Any]],
    key_columns: list[str],
    policy: str,
) -> KeyCheck:
    if not key_columns:
        return KeyCheck(source_id, [], policy, len(records), 0, 0, True, "no key declared")
    for column in key_columns:
        if any(column not in record for record in records):
            raise IngestError(f"{source_id}: key column {column!r} missing from landed records")
    seen: set[str] = set()
    duplicates = 0
    for record in records:
        token = "\x1f".join("" if record[col] is None else str(record[col]) for col in key_columns)
        if token in seen:
            duplicates += 1
        else:
            seen.add(token)
    rows = len(records)
    distinct = len(seen)
    if policy == "unique":
        passed = duplicates == 0
        detail = "" if passed else f"{duplicates} duplicate key(s) over {rows} rows"
    else:
        passed = True
        detail = f"observed {distinct} distinct key(s) over {rows} rows (policy=observe)"
    return KeyCheck(
        source_id, list(key_columns), policy, rows, distinct, duplicates, passed, detail
    )
