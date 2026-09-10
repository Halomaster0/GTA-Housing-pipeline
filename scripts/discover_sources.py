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
    """Enumerate each municipality's ArcGIS service directory directly.

    Hub free-text search is useless here: querying "Mississauga building permit"
    returned datasets from Faribault County, Nashville and Atlanta, because the
    q parameter ranks across the whole hub rather than scoping to a place. The
    org ids below were the one useful thing that search did surface, so we go
    straight to each org's REST service directory instead, which is exhaustive
    and unambiguous.
    """
    rule("ARCGIS — municipal service directories")
    orgs = [
        ("Mississauga", "https://services6.arcgis.com/hM5ymMLbxIyWTjn2"),
        ("Brampton", "https://services3.arcgis.com/rl7ACuZkiFsmDA2g"),
        ("Brampton (alt org)", "https://services6.arcgis.com/ONZht79c8QWuX759"),
    ]
    keywords = (
        "permit",
        "development",
        "application",
        "zoning",
        "planning",
        "parcel",
        "ward",
        "boundary",
    )

    for name, base in orgs:
        p(f"\n-- {name}: {base}/arcgis/rest/services")
        data = get(client, f"{base}/arcgis/rest/services", {"f": "json"})
        if not data:
            continue
        services = data.get("services", [])
        p(f"   {len(services)} services published")
        hits = [
            svc for svc in services if any(k in str(svc.get("name", "")).lower() for k in keywords)
        ]
        p(f"   {len(hits)} match permit/development/zoning keywords:")
        for svc in hits:
            svc_name = svc.get("name")
            svc_type = svc.get("type")
            p(f"   - {svc_name} ({svc_type})")
            layers_url = f"{base}/arcgis/rest/services/{str(svc_name).split('/')[-1]}/{svc_type}"
            meta = get(client, layers_url, {"f": "json"})
            if not meta:
                continue
            for layer in meta.get("layers", [])[:6]:
                lid, lname = layer.get("id"), layer.get("name")
                cnt = get(
                    client,
                    f"{layers_url}/{lid}/query",
                    {"where": "1=1", "returnCountOnly": "true", "f": "json"},
                )
                total = cnt.get("count") if cnt else "?"
                p(f"       layer {lid}: {lname!r}  ROWS={total}")
                info = get(client, f"{layers_url}/{lid}", {"f": "json"})
                if info:
                    flds = [(f.get("name"), f.get("type")) for f in info.get("fields", [])]
                    p(f"         FIELDS ({len(flds)}): {flds}")

    # Peel's org id was never surfaced. Ask the hub for its datasets by org name.
    p("\n-- Peel: hub datasets filtered by orgName")
    data = get(
        client,
        HUB_DATASETS,
        {"filter[orgName]": "Regional Municipality of Peel", "page[size]": 40},
    )
    if data:
        for it in data.get("data", []):
            a = it.get("attributes", {})
            p(
                f"   - {a.get('name')!r} type={a.get('type')!r} records={a.get('recordCount')} url={a.get('url')!r}"
            )


def discover_statcan(client: httpx.Client) -> None:
    """List StatCan cubes over GET and filter locally.

    Every POST to getCubeMetadata from a GitHub runner was answered with a
    connection reset or a read timeout, while the GET liveness endpoint returned
    200 in the same run. Rather than fight that, pull the full cube list over GET
    and filter it here. This also removes the need to recall a product id: the
    ids come from the response.
    """
    rule("STATISTICS CANADA WDS")
    p("\n-- getAllCubesListLite (GET)")
    data = get(client, "https://www150.statcan.gc.ca/t1/wds/rest/getAllCubesListLite")
    if not data:
        p("   no cube list returned; StatCan discovery unresolved")
        return
    cubes = data if isinstance(data, list) else data.get("object", [])
    p(f"   {len(cubes)} cubes listed")
    terms = ("building permit", "housing start", "dwelling", "occupanc")
    for cube in cubes:
        title = str(cube.get("cubeTitleEn", ""))
        if any(t in title.lower() for t in terms):
            p(
                f"   - productId={cube.get('productId')} {title!r} "
                f"start={cube.get('cubeStartDate')} end={cube.get('cubeEndDate')} "
                f"archived={cube.get('archived')}"
            )


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
