"""ArcGIS Hub connector: OID-range paged layer queries for FeatureServer/MapServer.

Two behaviours the naive offset approach gets wrong on real servers, both
observed live on 2026-09-10:

- Some layers truncate pages at the server's maxRecordCount (Brampton
  production MapServer: 1,000 rows back for a 2,000-row request) with no
  error — a short page is not the last page.
- The OID field is not always named OBJECTID (Brampton planning layers use
  POLY_ID). Ordering by a non-existent field is a 400.

So every pull starts by reading the layer definition (?f=json): the
esriFieldTypeOID field gives the paging key, maxRecordCount caps the page
size. Pages are `oid > last_oid` ranges ordered by the oid field — immune
to truncation and to rows shifting under offset windows on a live source.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from src.ingest.base import IngestError, fetch_json, get_checkpoint, save_checkpoint


@dataclass(frozen=True)
class LayerDef:
    oid_field: str
    max_record_count: int


@dataclass(frozen=True)
class ArcgisPull:
    records: list[dict[str, Any]]
    fields: list[str]
    reported_total: int | None


def read_layer_def(client: httpx.Client, source_id: str, layer_url: str) -> LayerDef:
    definition = fetch_json(client, "GET", layer_url, params={"f": "json"})
    if not isinstance(definition, dict) or "fields" not in definition:
        raise IngestError(f"{source_id}: layer definition has no fields list")
    oid_field = ""
    for field in definition["fields"]:
        if isinstance(field, dict) and field.get("type") == "esriFieldTypeOID":
            oid_field = str(field.get("name", ""))
            break
    if not oid_field:
        raise IngestError(f"{source_id}: no esriFieldTypeOID field in layer definition")
    try:
        max_count = int(definition.get("maxRecordCount", 1000))
    except (TypeError, ValueError):
        max_count = 1000
    return LayerDef(oid_field, max(1, max_count))


def _layer_count(client: httpx.Client, layer_url: str) -> int | None:
    payload = fetch_json(
        client,
        "GET",
        layer_url + "/query",
        params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
    )
    try:
        return int(payload["count"])
    except (KeyError, TypeError, ValueError):
        return None


def pull_arcgis(
    client: httpx.Client,
    source_id: str,
    layer_url: str,
    page_size: int,
    ingest_date: str,
    *,
    geometry: bool,
) -> ArcgisPull:
    layer = read_layer_def(client, source_id, layer_url)
    reported_total = _layer_count(client, layer_url)
    page_size = min(page_size, layer.max_record_count)

    checkpoint = get_checkpoint(source_id)
    last_oid: int | None = None
    if checkpoint.get("ingest_date") == ingest_date and not checkpoint.get("done", False):
        raw_oid = checkpoint.get("last_oid")
        if isinstance(raw_oid, int):
            last_oid = raw_oid

    records: list[dict[str, Any]] = []
    fields: list[str] = []
    while True:
        where = "1=1" if last_oid is None else f"{layer.oid_field} > {last_oid}"
        payload = fetch_json(
            client,
            "GET",
            layer_url + "/query",
            params={
                "where": where,
                "outFields": "*",
                "returnGeometry": "true" if geometry else "false",
                "orderByFields": layer.oid_field,
                "resultRecordCount": page_size,
                "f": "json",
            },
        )
        if isinstance(payload, dict) and payload.get("error"):
            raise IngestError(f"{source_id}: ArcGIS error after oid {last_oid}: {payload['error']}")
        try:
            features = payload["features"]
        except (KeyError, TypeError) as exc:
            raise IngestError(f"{source_id}: unexpected ArcGIS shape after oid {last_oid}") from exc
        if not isinstance(features, list):
            raise IngestError(f"{source_id}: ArcGIS features is not a list after oid {last_oid}")
        if not features:
            break
        for feature in features:
            attrs = dict(feature.get("attributes", {}))
            if geometry and "geometry" in feature:
                attrs["_geometry"] = feature["geometry"]
            records.append(attrs)
            raw = attrs.get(layer.oid_field)
            if isinstance(raw, int) and (last_oid is None or raw > last_oid):
                last_oid = raw
        if not fields:
            fields = sorted(records[0].keys())
        save_checkpoint(
            source_id,
            {
                "ingest_date": ingest_date,
                "last_oid": last_oid,
                "fetched": len(records),
                "done": False,
            },
        )
        if reported_total is not None and len(records) >= reported_total:
            break
    return ArcgisPull(records, fields, reported_total)
