"""Toronto CKAN connector: paged datastore_search pulls, one per resource.

Stable paging via sort=_id asc with limit/offset. The total returned on the
first page is recorded; if the final landed count disagrees (the catalogue
refreshes daily, possibly mid-pull), the run warns in the manifest instead
of failing — a mutating source is a fact to record, not an error to hide.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from src.ingest.base import fetch_json, get_checkpoint, save_checkpoint

CKAN_BASE = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action"


@dataclass(frozen=True)
class CkanPull:
    records: list[dict[str, Any]]
    fields: list[str]
    reported_total: int | None


def pull_ckan(
    client: httpx.Client,
    source_id: str,
    resource_id: str,
    page_size: int,
    ingest_date: str,
) -> CkanPull:
    checkpoint = get_checkpoint(source_id)
    start_offset = 0
    if checkpoint.get("ingest_date") == ingest_date and not checkpoint.get("done", False):
        start_offset = int(checkpoint.get("completed_offset", 0))
    records: list[dict[str, Any]] = []
    fields: list[str] = []
    reported_total: int | None = None
    offset = start_offset

    while True:
        payload = fetch_json(
            client,
            "GET",
            f"{CKAN_BASE}/datastore_search",
            params={
                "resource_id": resource_id,
                "limit": page_size,
                "offset": offset,
                "sort": "_id asc",
            },
        )
        try:
            result = payload["result"]
            batch = result["records"]
            reported_total = int(result["total"])
            if not fields:
                fields = [str(f["id"]) for f in result["fields"]]
        except (KeyError, TypeError, ValueError) as exc:
            from src.ingest.base import IngestError

            raise IngestError(f"{source_id}: unexpected datastore_search shape: {exc}") from exc
        if not isinstance(batch, list):
            from src.ingest.base import IngestError

            raise IngestError(f"{source_id}: datastore_search records is not a list")
        records.extend(batch)
        offset += len(batch)
        save_checkpoint(
            source_id,
            {"ingest_date": ingest_date, "completed_offset": offset, "done": False},
        )
        if len(batch) < page_size:
            break
    return CkanPull(records, fields, reported_total)
