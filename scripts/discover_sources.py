"""Resolve real dataset identifiers, row counts and field lists for each source.

Why this is separate from ``verify_sources.py``:

``verify_sources.py`` answers "is the registered check still returning what it
returned last time", and runs weekly forever. This answers the earlier and
messier question -- which dataset, on which portal, under which identifier, with
which columns -- which must be settled once per source before a registry entry
means anything, and re-settled whenever a portal reorganises.

It prints raw response shapes on purpose. Open-data portals do not document their
envelopes reliably, and the project's rule is that a field name is never written
down until it has been seen in a live response.

The build sandbox blocks every municipal and StatCan host, so this runs on a
GitHub runner via .github/workflows/source-discovery.yml and its output is read
from the job log. Findings are also collected and reprinted as a summary at the
end, because a long log gets truncated from the top and the summary is the part
worth keeping.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import httpx

TORONTO_CKAN = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action"
HUB_DATASETS = "https://hub.arcgis.com/api/v3/datasets"
STATCAN_CUBES = "https://www150.statcan.gc.ca/t1/wds/rest/getAllCubesListLite"
TIMEOUT = httpx.Timeout(30.0, connect=15.0)
HEADERS = {
    "User-Agent": (
        "GTA-Housing-pipeline source discovery "
        "(+https://github.com/Halomaster0/GTA-Housing-pipeline)"
    )
}

# Org ids as confirmed by live responses on 2026-09-10. The hub's own search
# mislabelled the third of these as City of Brampton; its dataset list is
# unambiguously Regional Municipality of Peel.
ARCGIS_ORGS = [
    ("City of Mississauga", "https://services6.arcgis.com/hM5ymMLbxIyWTjn2"),
    ("City of Brampton", "https://services3.arcgis.com/rl7ACuZkiFsmDA2g"),
    ("Regional Municipality of Peel", "https://services6.arcgis.com/ONZht79c8QWuX759"),
]

KEYWORDS = ("permit", "development", "application", "zoning", "planning", "parcel", "ward")

FINDINGS: list[str] = []


def p(msg: str) -> None:
    """Print and flush. CI job logs interleave badly without an explicit flush."""
    print(msg, flush=True)


def record(line: str) -> None:
    """Collect a confirmed fact for the end-of-run summary."""
    FINDINGS.append(line)


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
        p(f"  NON-JSON from {r.request.url}: {r.text[:200]!r}")
        return None


def discover_toronto(client: httpx.Client) -> None:
    rule("TORONTO CKAN")
    for query in ("building permit", "development application"):
        p(f"\n-- package_search q={query!r}")
        data = get(client, f"{TORONTO_CKAN}/package_search", {"q": query, "rows": 15})
        if not data:
            continue
        results = data.get("result", {}).get("results", [])
        p(f"   {data.get('result', {}).get('count')} matched; showing {len(results)}")
        for pkg in results:
            p(f"   - {pkg.get('name')!r} title={pkg.get('title')!r}")

    slugs = (
        "building-permits-active-permits",
        "building-permits-cleared-permits",
        "development-applications",
        "city-wards",
    )
    for slug in slugs:
        p(f"\n-- package_show id={slug!r}")
        data = get(client, f"{TORONTO_CKAN}/package_show", {"id": slug})
        if not data or not data.get("success"):
            record(f"TORONTO {slug}: package_show FAILED - slug may be wrong")
            continue
        pkg = data["result"]
        licence = pkg.get("license_title")
        p(f"   title={pkg.get('title')!r} licence={licence!r}")
        p(f"   refresh={pkg.get('refresh_rate')!r} last_refreshed={pkg.get('last_refreshed')!r}")
        for res in pkg.get("resources", []):
            if not res.get("datastore_active"):
                continue
            ds = get(
                client,
                f"{TORONTO_CKAN}/datastore_search",
                {"resource_id": res["id"], "limit": 1},
            )
            if not (ds and ds.get("success")):
                continue
            result = ds["result"]
            fields = [(f.get("id"), f.get("type")) for f in result.get("fields", [])]
            p(f"   resource {res['id']} name={res.get('name')!r}")
            p(f"     ROWS={result.get('total')}  FIELDS({len(fields)}): {fields}")
            record(
                f"TORONTO {slug}: rows={result.get('total')} "
                f"resource_id={res['id']} licence={licence!r}"
            )


def probe_layer(client: httpx.Client, layers_url: str, lid: Any, lname: Any) -> int | None:
    cnt = get(
        client,
        f"{layers_url}/{lid}/query",
        {"where": "1=1", "returnCountOnly": "true", "f": "json"},
    )
    total = cnt.get("count") if cnt else None
    p(f"       layer {lid}: {lname!r}  ROWS={total}")
    info = get(client, f"{layers_url}/{lid}", {"f": "json"})
    if info:
        flds = [(f.get("name"), f.get("type")) for f in info.get("fields", [])]
        p(f"         FIELDS ({len(flds)}): {flds}")
    return total


def discover_arcgis(client: httpx.Client) -> None:
    """Walk each municipality's ArcGIS service directory.

    Hub free-text search is useless here: 'Mississauga building permit' returned
    datasets from Faribault County, Nashville and Atlanta, because q ranks across
    the whole hub rather than scoping to a place. Going straight to each org's REST
    directory is exhaustive and unambiguous.
    """
    rule("ARCGIS — municipal service directories")
    for org_name, base in ARCGIS_ORGS:
        p(f"\n-- {org_name}: {base}/arcgis/rest/services")
        data = get(client, f"{base}/arcgis/rest/services", {"f": "json"})
        if not data:
            continue
        services = data.get("services", [])
        hits = [s for s in services if any(k in str(s.get("name", "")).lower() for k in KEYWORDS)]
        p(f"   {len(services)} services published, {len(hits)} match keywords")
        for svc in hits:
            svc_name = str(svc.get("name", "")).split("/")[-1]
            svc_type = svc.get("type")
            p(f"   - {svc_name} ({svc_type})")
            layers_url = f"{base}/arcgis/rest/services/{svc_name}/{svc_type}"
            meta = get(client, layers_url, {"f": "json"})
            layers = (meta or {}).get("layers") or []
            if not layers:
                # Some FeatureServers do not list layers on the service endpoint.
                # Probe layer 0 directly rather than reporting the service as empty.
                total = probe_layer(client, layers_url, 0, "(layer list absent, probed 0)")
                if total is not None:
                    record(f"{org_name} {svc_name}/0: rows={total}")
                continue
            for layer in layers[:6]:
                total = probe_layer(client, layers_url, layer.get("id"), layer.get("name"))
                if total is not None:
                    lid, lname = layer.get("id"), layer.get("name")
                    record(f"{org_name} {svc_name}/{lid} {lname!r}: rows={total}")


def discover_statcan(client: httpx.Client) -> None:
    """List StatCan cubes over GET and filter locally.

    Every POST to getCubeMetadata from a runner was answered with a connection
    reset or a read timeout, while this GET endpoint returned 200 in the same run.
    Filtering the full list locally also removes any need to recall a product id --
    the ids come from the response, which matters because 34100066 and 34100285
    are both plausible-looking building-permit tables that are now inactive.
    """
    rule("STATISTICS CANADA WDS")
    data = get(client, STATCAN_CUBES)
    if not data:
        p("   no cube list returned")
        return
    cubes = data if isinstance(data, list) else data.get("object", [])
    p(f"   {len(cubes)} cubes listed")
    terms = ("building permit", "housing start", "population and dwelling counts")
    for cube in cubes:
        title = str(cube.get("cubeTitleEn", ""))
        if not any(t in title.lower() for t in terms):
            continue
        active = cube.get("archived") == "2"
        if not active:
            continue
        line = (
            f"STATCAN {cube.get('productId')}: {title[:90]!r} "
            f"{str(cube.get('cubeStartDate'))[:10]} to {str(cube.get('cubeEndDate'))[:10]}"
        )
        p(f"   - {line}")
        record(line)


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

    rule("SUMMARY — confirmed from live responses")
    for line in FINDINGS:
        p(f"  {line}")
    p(
        f"\n{len(FINDINGS)} facts collected. None of this is fact in the repository "
        "until it is transcribed into config/sources.yml and docs/sources/*.md."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
