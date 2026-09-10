#!/usr/bin/env python3
"""Live liveness / row-count checker for the sources registered in config/sources.yml.

For each registered source this issues one live HTTP request (with one retry on transport
failure/timeout, backing off between attempts), extracts a row/record count from the JSON
response using the source's declared `count_json_path`, and compares it against the
source's `expected_min_rows`. No source URL, resource id, or count path is hardcoded here --
everything comes from config/sources.yml, so adding a new source is a YAML edit, never a
code change.

Usage:
    uv run --with httpx --with pyyaml python scripts/verify_sources.py
    uv run --with httpx --with pyyaml python scripts/verify_sources.py --json
    uv run --with httpx --with pyyaml python scripts/verify_sources.py \
        --source toronto-building-permits

This is meant to run weekly in CI (see docs/build-plan.md §5.9, §9 risk R1): the exit code
is the contract. Exit 0 only if every checked source is reachable, returned HTTP < 400, and
met its expected_min_rows. Any DEAD, UNREACHABLE, BELOW_MINIMUM, or PARSE_ERROR verdict
exits non-zero.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "sources.yml"
RESULT_PATH = REPO_ROOT / "docs" / "sources" / "verification-latest.json"

REQUEST_TIMEOUT_SECONDS = 20.0
RETRY_ATTEMPTS = 2  # one try + one retry
RETRY_BACKOFF_SECONDS = 3.0

# Sentinel count_json_path meaning "the whole JSON response body is the array to count".
ARRAY_LENGTH_SENTINEL = "$__array_length__"

VERDICT_OK = "OK"
VERDICT_BELOW_MINIMUM = "BELOW_MINIMUM"
VERDICT_UNREACHABLE = "UNREACHABLE"
VERDICT_DEAD = "DEAD"  # reachable, but HTTP >= 400
VERDICT_NO_COUNT_CHECK = "REACHABLE_NO_COUNT_CHECK"  # HTTP OK, count_json_path is null
VERDICT_PARSE_ERROR = "PARSE_ERROR"  # HTTP OK, but count could not be extracted

FAILING_VERDICTS = frozenset(
    {VERDICT_BELOW_MINIMUM, VERDICT_UNREACHABLE, VERDICT_DEAD, VERDICT_PARSE_ERROR}
)


@dataclass(frozen=True)
class SourceConfig:
    """One row of config/sources.yml, typed."""

    id: str
    name: str
    municipality: str
    api_type: str
    check_url: str
    count_json_path: str | None
    expected_min_rows: int
    licence: str
    licence_url: str | None
    cadence: str
    verified_on: str | None
    status: str
    method: str = "GET"
    json_body: dict[str, Any] | None = None
    notes: str = ""


@dataclass(frozen=True)
class CheckResult:
    source: SourceConfig
    http_status: int | None
    row_count: int | None
    verdict: str
    detail: str


class SourceConfigError(ValueError):
    """Raised when config/sources.yml is malformed."""


def load_sources(config_path: Path) -> list[SourceConfig]:
    """Read and type the source registry. Fails loudly on a malformed entry."""
    with config_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not raw or "sources" not in raw:
        raise SourceConfigError(f"{config_path} has no top-level 'sources' key")

    sources: list[SourceConfig] = []
    for i, entry in enumerate(raw["sources"]):
        try:
            sources.append(
                SourceConfig(
                    id=entry["id"],
                    name=entry["name"],
                    municipality=entry.get("municipality", ""),
                    api_type=entry.get("api_type", ""),
                    check_url=entry["check_url"],
                    count_json_path=entry.get("count_json_path"),
                    expected_min_rows=int(entry.get("expected_min_rows") or 0),
                    licence=entry.get("licence", ""),
                    licence_url=entry.get("licence_url"),
                    cadence=entry.get("cadence", ""),
                    verified_on=entry.get("verified_on"),
                    status=entry.get("status", "unverified"),
                    method=entry.get("method", "GET"),
                    json_body=entry.get("json_body"),
                    notes=entry.get("notes", ""),
                )
            )
        except KeyError as exc:
            raise SourceConfigError(
                f"{config_path}: sources[{i}] is missing required key {exc}"
            ) from exc
    return sources


def resolve_count(data: Any, path: str) -> int:
    """Walk a dot-path (e.g. 'result.count') through parsed JSON and return an int count.

    A resolved list is reported by its length; a resolved number is cast to int. The
    ARRAY_LENGTH_SENTINEL path means "the whole payload is the array to count".

    Raises TypeError/KeyError/IndexError/ValueError when the path does not resolve --
    callers must catch those explicitly (never swallow silently) and report PARSE_ERROR.
    """
    if path == ARRAY_LENGTH_SENTINEL:
        if not isinstance(data, list):
            raise TypeError(
                f"expected a top-level JSON array for {ARRAY_LENGTH_SENTINEL}, "
                f"got {type(data).__name__}"
            )
        return len(data)

    node: Any = data
    for key in path.split("."):
        if isinstance(node, list):
            node = node[int(key)]
        elif isinstance(node, dict):
            node = node[key]
        else:
            raise TypeError(f"cannot descend into {type(node).__name__} with key '{key}'")

    if isinstance(node, bool):
        raise TypeError("resolved value is a bool, not a count")
    if isinstance(node, (int, float)):
        return int(node)
    if isinstance(node, list):
        return len(node)
    raise TypeError(f"resolved value has unsupported type {type(node).__name__}")


def _request_with_retry(
    client: httpx.Client, source: SourceConfig
) -> tuple[httpx.Response | None, str]:
    """Issue the check request with one retry on timeout/transport failure."""
    last_error = ""
    for attempt in range(RETRY_ATTEMPTS):
        try:
            if source.method.upper() == "POST":
                response = client.post(
                    source.check_url, json=source.json_body, timeout=REQUEST_TIMEOUT_SECONDS
                )
            else:
                response = client.get(source.check_url, timeout=REQUEST_TIMEOUT_SECONDS)
            return response, ""
        except httpx.TimeoutException as exc:
            last_error = f"timeout after {REQUEST_TIMEOUT_SECONDS}s: {exc}"
        except httpx.TransportError as exc:
            last_error = f"transport error: {exc}"
        if attempt < RETRY_ATTEMPTS - 1:
            time.sleep(RETRY_BACKOFF_SECONDS)
    return None, last_error


def check_source(client: httpx.Client, source: SourceConfig) -> CheckResult:
    response, error_detail = _request_with_retry(client, source)

    if response is None:
        return CheckResult(
            source=source,
            http_status=None,
            row_count=None,
            verdict=VERDICT_UNREACHABLE,
            detail=error_detail,
        )

    if response.status_code >= 400:
        return CheckResult(
            source=source,
            http_status=response.status_code,
            row_count=None,
            verdict=VERDICT_DEAD,
            detail=f"HTTP {response.status_code}: {response.text[:200]!r}",
        )

    if source.count_json_path is None:
        return CheckResult(
            source=source,
            http_status=response.status_code,
            row_count=None,
            verdict=VERDICT_NO_COUNT_CHECK,
            detail="no count_json_path configured; reachability-only check",
        )

    try:
        data = response.json()
        count = resolve_count(data, source.count_json_path)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError, IndexError) as exc:
        body_excerpt = response.text[:300]
        return CheckResult(
            source=source,
            http_status=response.status_code,
            row_count=None,
            verdict=VERDICT_PARSE_ERROR,
            detail=(
                f"could not extract count via '{source.count_json_path}': {exc}. "
                f"Body excerpt: {body_excerpt!r}"
            ),
        )

    if count < source.expected_min_rows:
        return CheckResult(
            source=source,
            http_status=response.status_code,
            row_count=count,
            verdict=VERDICT_BELOW_MINIMUM,
            detail=f"{count} < expected_min_rows {source.expected_min_rows}",
        )

    return CheckResult(
        source=source,
        http_status=response.status_code,
        row_count=count,
        verdict=VERDICT_OK,
        detail="",
    )


def print_table(results: list[CheckResult]) -> None:
    headers = ["source", "http_status", "row_count", "expected_min", "verdict"]
    rows = [
        [
            r.source.id,
            str(r.http_status) if r.http_status is not None else "-",
            str(r.row_count) if r.row_count is not None else "-",
            str(r.source.expected_min_rows),
            r.verdict,
        ]
        for r in results
    ]
    widths = [
        max(len(header), *(len(row[i]) for row in rows)) if rows else len(header)
        for i, header in enumerate(headers)
    ]

    def fmt_row(cols: list[str]) -> str:
        return "  ".join(col.ljust(w) for col, w in zip(cols, widths, strict=True))

    print(fmt_row(headers))
    print(fmt_row(["-" * w for w in widths]))
    for row in rows:
        print(fmt_row(row))
    for r in results:
        if r.detail:
            print(f"  [{r.source.id}] {r.detail}")


def write_results_json(results: list[CheckResult], output_path: Path) -> None:
    payload = {
        "checked_at": datetime.now(UTC).isoformat(),
        "sources": [
            {
                "id": r.source.id,
                "name": r.source.name,
                "municipality": r.source.municipality,
                "http_status": r.http_status,
                "row_count": r.row_count,
                "expected_min_rows": r.source.expected_min_rows,
                "verdict": r.verdict,
                "detail": r.detail,
                "registry_status": r.source.status,
            }
            for r in results
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify liveness and row counts of registered data sources."
    )
    parser.add_argument("--source", help="Only check this source id.")
    parser.add_argument(
        "--json", action="store_true", help="Print machine-readable JSON instead of the table."
    )
    args = parser.parse_args(argv)

    try:
        sources = load_sources(CONFIG_PATH)
    except SourceConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.source:
        sources = [s for s in sources if s.id == args.source]
        if not sources:
            print(f"No source with id '{args.source}' in {CONFIG_PATH}", file=sys.stderr)
            return 2

    results: list[CheckResult] = []
    with httpx.Client(follow_redirects=True) as client:
        for source in sources:
            results.append(check_source(client, source))

    write_results_json(results, RESULT_PATH)

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "id": r.source.id,
                        "http_status": r.http_status,
                        "row_count": r.row_count,
                        "expected_min_rows": r.source.expected_min_rows,
                        "verdict": r.verdict,
                        "detail": r.detail,
                    }
                    for r in results
                ],
                indent=2,
            )
        )
    else:
        print_table(results)

    failing = [r for r in results if r.verdict in FAILING_VERDICTS]
    if failing:
        print(f"\n{len(failing)} of {len(results)} source(s) failed verification.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
