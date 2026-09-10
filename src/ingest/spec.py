"""Typed pull specs from config/ingest.yml, validated against the registry.

Every spec id must exist in config/sources.yml (typos fail loudly), and no
spec may point at a _DEV/_UAT URL without written justification — the same
rule the registry itself enforces (tests/unit/test_sources_registry.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from src.ingest.base import REPO_ROOT, IngestError

INGEST_CONFIG_PATH = REPO_ROOT / "config" / "ingest.yml"
REGISTRY_PATH = REPO_ROOT / "config" / "sources.yml"

VALID_FAMILIES = frozenset({"ckan", "arcgis", "statcan-meta"})
VALID_KEY_POLICIES = frozenset({"unique", "observe"})


@dataclass(frozen=True)
class SourceSpec:
    id: str
    family: str
    business_key: list[str]
    key_policy: str
    facts_feed: bool
    params: dict[str, Any]
    key_observe: list[str]


def _registry_ids() -> set[str]:
    with REGISTRY_PATH.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    if not raw or "sources" not in raw:
        raise IngestError(f"{REGISTRY_PATH} has no top-level 'sources' key")
    return {str(entry["id"]) for entry in raw["sources"]}


def load_specs() -> list[SourceSpec]:
    with INGEST_CONFIG_PATH.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    if not raw or "sources" not in raw:
        raise IngestError(f"{INGEST_CONFIG_PATH} has no top-level 'sources' key")

    known_ids = _registry_ids()
    defaults = raw.get("defaults", {}) or {}
    specs: list[SourceSpec] = []
    for entry in raw["sources"]:
        source_id = str(entry["id"])
        if source_id not in known_ids:
            raise IngestError(f"ingest spec {source_id!r} has no entry in {REGISTRY_PATH}")
        family = str(entry["family"])
        if family not in VALID_FAMILIES:
            raise IngestError(f"ingest spec {source_id!r}: unknown family {family!r}")
        key_policy = str(entry.get("key_policy", "unique"))
        if key_policy not in VALID_KEY_POLICIES:
            raise IngestError(f"ingest spec {source_id!r}: unknown key_policy {key_policy!r}")
        params = {k: v for k, v in entry.items() if k not in {"id", "family"}}
        params.setdefault("ckan_page_size", defaults.get("ckan_page_size", 5000))
        params.setdefault("arcgis_page_size", defaults.get("arcgis_page_size", 2000))
        key_observe = [str(c) for c in entry.get("key_observe", [])]
        layer_url = str(params.get("layer_url", ""))
        if any(suffix in layer_url for suffix in ("_DEV", "_UAT")):
            raise IngestError(
                f"ingest spec {source_id!r}: _DEV/_UAT URL without written justification"
            )
        specs.append(
            SourceSpec(
                id=source_id,
                family=family,
                business_key=[str(c) for c in entry.get("business_key", [])],
                key_policy=key_policy,
                facts_feed=bool(entry.get("facts_feed", True)),
                params=params,
                key_observe=key_observe,
            )
        )
    ids = [s.id for s in specs]
    if len(ids) != len(set(ids)):
        raise IngestError("duplicate source ids in config/ingest.yml")
    return specs
