"""Ingest spec guards: registry and pull specs cannot drift apart silently.

- Every spec id exists in config/sources.yml (typos fail at load, but this
  pins the direction registry→spec too: every fact/geography feed that is
  verified-live must have a pull spec, or it is silently un-ingested).
- No spec may reference CMHC (NOT ADOPTED) or a _DEV/_UAT URL.
- The StatCan series-pull caveat holds: no coordinates until one succeeds
  live (config comment today; this test locks the current state so a future
  edit adds coordinates deliberately, updating this test with the evidence).
"""

from __future__ import annotations

import pytest
import yaml

from src.ingest.base import REPO_ROOT
from src.ingest.spec import load_specs

pytestmark = pytest.mark.unit


def test_every_landed_feed_has_a_spec() -> None:
    with (REPO_ROOT / "config" / "sources.yml").open("r", encoding="utf-8") as fh:
        registry = yaml.safe_load(fh)["sources"]
    # Feeds that must land bronze: verified-live record feeds. `catalogued`
    # StatCan products land metadata via their spec; liveness-only and
    # not-adopted entries are excluded by status.
    must_land = {
        entry["id"]
        for entry in registry
        if entry.get("status") == "verified-live" and entry.get("count_json_path") is not None
    }
    # `statcan-wds-liveness` is a service check, not a feed: its metadata lands
    # via the statcan-building-permits-34100292 spec.
    must_land.discard("statcan-wds-liveness")
    # peel-building-permits is verified-live-not-a-feed but lands bronze for
    # liveness/drift (facts_feed=false) — required, not optional.
    must_land.add("peel-building-permits")
    spec_ids = {spec.id for spec in load_specs()}
    assert must_land - spec_ids == set(), f"feeds without pull specs: {must_land - spec_ids}"


def test_no_cmhc_and_no_dev_urls_in_specs() -> None:
    for spec in load_specs():
        assert not spec.id.startswith("cmhc"), f"{spec.id}: CMHC is NOT ADOPTED"
        url = str(spec.params.get("layer_url", ""))
        assert "_DEV" not in url and "_UAT" not in url, f"{spec.id}: staging URL in spec"


def test_statcan_series_pull_stays_empty_until_proven() -> None:
    with (REPO_ROOT / "config" / "ingest.yml").open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    statcan = [e for e in raw["sources"] if e.get("family") == "statcan-meta"]
    assert statcan, "statcan-meta spec went missing"
    for entry in statcan:
        assert not entry.get("series"), (
            f"{entry['id']}: series coordinates added without updating this test — "
            "cite the live successful pull (evidence file) when enabling"
        )
