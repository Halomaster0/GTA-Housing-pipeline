"""Statistics Canada connector: per-product metadata first, series when proven.

getCubeMetadata is proven live from this environment (2026-09-10, four
products, status SUCCESS). Series pulls via
getDataFromCubePidCoordAndLatestNPeriods returned HTTP 406 on 2026-09-10 —
so series specs stay empty until one coordinate succeeds live (see
config/ingest.yml). A failed series pull raises IngestError with the response
excerpt: loud, recorded in the manifest, never silent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from src.ingest.base import IngestError, fetch_json

WDS_BASE = "https://www150.statcan.gc.ca/t1/wds/rest"


@dataclass(frozen=True)
class StatcanPull:
    metadata: list[dict[str, Any]]
    series: list[dict[str, Any]]


def pull_statcan_meta(client: httpx.Client, product_ids: list[int]) -> list[dict[str, Any]]:
    payload = fetch_json(
        client,
        "POST",
        WDS_BASE + "/getCubeMetadata",
        json_body=[{"productId": pid} for pid in product_ids],
    )
    if not isinstance(payload, list):
        raise IngestError("getCubeMetadata did not return a list")
    for entry in payload:
        if not isinstance(entry, dict) or entry.get("status") != "SUCCESS":
            raise IngestError(f"getCubeMetadata non-SUCCESS entry: {str(entry)[:300]!r}")
    return payload


def pull_statcan_series(
    client: httpx.Client, product_id: int, coordinate: str, latest_n: int
) -> list[dict[str, Any]]:
    try:
        payload = fetch_json(
            client,
            "POST",
            WDS_BASE + "/getDataFromCubePidCoordAndLatestNPeriods",
            json_body=[{"productId": product_id, "coordinate": coordinate, "latestN": latest_n}],
        )
    except IngestError as exc:
        raise IngestError(f"StatCan series pull failed (product {product_id}): {exc}") from exc
    if not isinstance(payload, list):
        raise IngestError(f"StatCan series pull for {product_id} did not return a list")
    return payload
