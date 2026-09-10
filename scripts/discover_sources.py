"""Resolve real dataset identifiers, row counts and field lists for each source.

Why this exists as a separate tool from ``verify_sources.py``:

``verify_sources.py`` answers "is the registered check still returning what it
returned last time" and runs weekly forever. This script answers the earlier and
messier question -- "which dataset, on which portal, under which identifier, with
which columns" -- which has to be settled once per source before a registry entry
means anything, and re-settled whenever a portal reorganises.

It is deliberately verbose and prints raw response shapes. Open-data portals do
not document their response envelopes reliably, and the project's rule is that a
field name is never written down until it has been seen in a live response. So
this prints what actually came back rather than what a schema promised.

The build sandbox blocks every municipal and StatCan host, so this is intended to
run on a GitHub runner via .github/workflows/source-discovery.yml, with its output
read from the job log.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import httpx

TORONTO_CKAN = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action"
HUB_DATASETS = "https://hub.arcgis.com/api/v3/datasets"
TIMEOUT = httpx.Timeout(30.0, connect=15.0)
HEADERS = {
    "User-Agent": "GTA-Housing-pipeline source discovery (+https://github.com/Halomaster0/GTA-Housing-pipeline)"
}


def p(msg: str) -> None:
    """Print and flush. CI job logs interleave badly without an explicit flush."""
    print(msg, flush=True)


def rule(title: str) -> None:
    p(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def get(client: httpx.Client, url: str, params: dict[str, Any] | None = None) -> Any:
    try:
        r = client.get(url, params=params)
    except httpx.HTTPError as exc:
        p(f"  TRANSPORT ERROR {url}: {exc}")
        return None
    if r.status_code != 200:
        p(f"  HTTP {r.status_code} {r.request.url}")
        return None
    try:
        return r.json()
    except ValueError:
        p(f"  NON-JSON RESPONSE from {r.request.url}: {r.text[:200]!r}")
        return None


def discover_toronto(client: httpx.Client) -> None:
    rule("TORONTO CKAN")
    for query in ("building permit", "development application", "ward"):
        p(f"\n-- package_search q={query!r}")
        data = get(client, f"{TORONTO_CKAN}/package_search", {"q": query, "rows": 10})
        if not data:
            continue
        results = data.get("result", {}).get("results", [])
        total = data.get("result", {}).get("count")
        p(f"   {total} packages matched; showing {len(results)}")
        for pkg in results:
            n_res = len(pkg.get("resources", []))
            p(f"   - {pkg.get('name')!r}  title={pkg.get('title')!r}  resources={n_res}")

    # Resolve the datastore resources of the most likely permit/application packages.
    for slug in (
        "building-permits-active-permits",
        "building-permits-cleared-permits",
        "development-applications",
        "city-wards",
    ):
        p(f"\n-- package_show id={slug!r}")
        data = get(client, f"{TORONTO_CKAN}/package_show", {"id": slug})
        if not data or not data.get("success"):
            continue
        pkg = data["result"]
        p(f"   title={pkg.get('title')!r}")
        p(f"   licence={pkg.get('license_title')!r} url={pkg.get('license_url')!r}")
        p(f"   refresh={pkg.get('refresh_rate')!r} last_refreshed={pkg.get('last_refreshed')!r}")
        for res in pkg.get("resources", []):
            p(
                f"   resource id={res.get('id')} name={res.get('name')!r} "
                f"format={res.get('format')!r} datastore_active={res.get('datastore_active')}"
            )
            if res.get("datastore_active"):
                ds = get(
                    client,
                    f"{TORONTO_CKAN}/datastore_search",
                    {"resource_id": res["id"], "limit": 1},
                )
                if ds and ds.get("success"):
                    result = ds["result"]
                    p(f"     TOTAL ROWS = {result.get('total')}")
                    fields = [(f.get("id"), f.get("type")) for f in result.get("fields", [])]
                    p(f"     FIELDS ({len(fields)}): {fields}")


def discover_arcgis(client: httpx.Client) -> None:
    rule("ARCGIS HUB — municipal layer discovery")
    queries = [
        ("mississauga", "Mississauga building permit"),
        ("mississauga", "Mississauga development application"),
        ("brampton", "Brampton building permit"),
        ("brampton", "Brampton development application"),
        ("peel", "Peel Region planning"),
    ]
    printed_shape = False
    for _tag, q in queries:
        p(f"\n-- hub datasets q={q!r}")
        data = get(client, HUB_DATASETS, {"q": q, "page[size]": 8})
        if not data:
            continue
        items = data.get("data", [])
        meta_total = data.get("meta", {}).get("stats", {}).get("totalCount")
        p(f"   returned {len(items)} items (hub-wide meta total={meta_total})")
        if items and not printed_shape:
            p(f"   ATTRIBUTE KEYS: {sorted(items[0].get('attributes', {}).keys())}")
            printed_shape = True
        for it in items:
            a = it.get("attributes", {})
            p(
                f"   - {a.get('name')!r} org={a.get('orgName')!r} type={a.get('type')!r} "
                f"records={a.get('recordCount')} url={a.get('url')!r}"
            )


def discover_statcan(client: httpx.Client) -> None:
    rule("STATISTICS CANADA WDS")
    # Confirm product IDs by asking the API, never from memory.
    for pid in ("34100066", "34100143", "98100001"):
        p(f"\n-- getCubeMetadata productId={pid}")
        try:
            r = client.post(
                "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata",
                json=[{"productId": int(pid)}],
            )
        except httpx.HTTPError as exc:
            p(f"   TRANSPORT ERROR: {exc}")
            continue
        p(f"   HTTP {r.status_code}")
        if r.status_code != 200:
            continue
        try:
            payload = r.json()
        except ValueError:
            p(f"   NON-JSON: {r.text[:200]!r}")
            continue
        for entry in payload if isinstance(payload, list) else [payload]:
            if entry.get("status") != "SUCCESS":
                p(f"   status={entry.get('status')} object={str(entry.get('object'))[:200]}")
                continue
            obj = entry.get("object", {})
            p(f"   cubeTitleEn={obj.get('cubeTitleEn')!r}")
            p(f"   start={obj.get('cubeStartDate')} end={obj.get('cubeEndDate')}")
            p(f"   archived={obj.get('archiveStatusEn')!r}")
            dims = [d.get("dimensionNameEn") for d in obj.get("dimension", [])]
            p(f"   dimensions: {dims}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--only",
        choices=["toronto", "arcgis", "statcan"],
        help="run a single discovery pass instead of all three",
    )
    args = ap.parse_args()

    with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
        if args.only in (None, "toronto"):
            discover_toronto(client)
        if args.only in (None, "arcgis"):
            discover_arcgis(client)
        if args.only in (None, "statcan"):
            discover_statcan(client)

    p(
        "\nDiscovery pass complete. Nothing here is fact until it is transcribed "
        "into config/sources.yml and docs/sources/*.md."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
