"""Build the landing-page municipality map from real bronze geometry.

Reads Peel municipal boundaries (Esri rings, EPSG:3857) and Toronto ward
polygons (GeoJSON, lon/lat) from the landed bronze layer plus permit counts
from docs/measure-reconciliation.json, and writes a simplified static SVG to
web/public/gta-map.svg. The page inlines the SVG (build-time file read) so
page CSS owns fills, fonts, and both colour schemes.

Rules (design-plan §8): real geography carrying real numbers. No schematic
shapes, no invented coordinates. Counts come from the reconciliation JSON,
so the map can never disagree with the status table beside it. Toronto is
drawn as its 25 ward polygons filled alike with seam-coloured strokes (no
internal borders). Caledon gets a neutral fill + "no permit feed" label
(ADR-0004), never a zero.

Usage:
    python scripts/build_map_svg.py [--ingest-date YYYY-MM-DD] [--out PATH]

Regenerate, never hand-edit the SVG (ADR-0009).
"""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path

import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parent.parent
R_EARTH = 6378137.0
MAX_POINTS_PER_RING = 250


def mercator_to_lonlat(x: float, y: float) -> tuple[float, float]:
    lon = math.degrees(x / R_EARTH)
    lat = math.degrees(math.atan(math.sinh(y / R_EARTH)))
    return lon, lat


def decimate(ring: list, cap: int = MAX_POINTS_PER_RING) -> list:
    if len(ring) <= cap:
        return ring
    step = math.ceil(len(ring) / cap)
    kept = ring[::step]
    if kept[-1] != ring[-1]:
        kept.append(ring[-1])
    return kept


def read_peel(ingest_date: str) -> dict[str, list[list[tuple[float, float]]]]:
    """MUN_NAME -> list of lon/lat rings."""
    files = sorted(
        (REPO_ROOT / "data" / "bronze" / "peel-municipal-boundary").glob(
            f"ingest_date={ingest_date}/*.parquet"
        )
    )
    if not files:
        raise SystemExit(f"build_map_svg: no peel-municipal-boundary for {ingest_date}")
    out: dict[str, list[list[tuple[float, float]]]] = {}
    for path in files:
        table = pq.read_table(path)
        names = table.column("MUN_NAME").to_pylist()
        geoms = table.column("_geometry").to_pylist()
        for name, geom in zip(names, geoms, strict=True):
            rings = []
            for ring in geom["rings"]:
                rings.append([mercator_to_lonlat(x, y) for x, y in decimate(ring)])
            out.setdefault(name, []).extend(rings)
    return out


def read_toronto_wards(ingest_date: str) -> list[list[tuple[float, float]]]:
    files = sorted(
        (REPO_ROOT / "data" / "bronze" / "toronto-wards").glob(
            f"ingest_date={ingest_date}/*.parquet"
        )
    )
    if not files:
        raise SystemExit(f"build_map_svg: no toronto-wards for {ingest_date}")
    polys: list[list[tuple[float, float]]] = []
    for path in files:
        table = pq.read_table(path)
        for raw in table.column("geometry").to_pylist():
            geom = json.loads(raw)
            coords = geom["coordinates"]
            rings = coords if geom["type"] == "MultiPolygon" else [coords]
            for poly in rings:
                polys.append([(x, y) for x, y in decimate(poly[0])])
    return polys


def project(
    polys: list[list[tuple[float, float]]], bbox: tuple[float, float, float, float]
) -> tuple[list[str], float, float]:
    lon0, lat0, lon1, lat1 = bbox
    width, height = 1000.0, 1000.0 * (lat1 - lat0) / max(lon1 - lon0, 1e-9)
    paths = []
    for ring in polys:
        pts = []
        for lon, lat in ring:
            x = (lon - lon0) / (lon1 - lon0) * width
            y = (1.0 - (lat - lat0) / (lat1 - lat0)) * height
            pts.append(f"{x:.1f},{y:.1f}")
        paths.append("M" + "L".join(pts) + "Z")
    return paths, width, height


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingest-date", default="2026-09-10")
    parser.add_argument("--out", default=str(REPO_ROOT / "web" / "public" / "gta-map.svg"))
    args = parser.parse_args()

    recon = json.loads(
        (REPO_ROOT / "docs" / "measure-reconciliation.json").read_text(encoding="utf-8")
    )
    counts = recon["permits_by_municipality"]
    peel = read_peel(args.ingest_date)
    toronto = read_toronto_wards(args.ingest_date)

    shapes = {
        "tor": toronto,
        "miss": peel.get("Mississauga", []),
        "bram": peel.get("Brampton", []),
        "cale": peel.get("Caledon", []),
    }
    if any(not v for v in shapes.values()):
        missing = sorted(k for k, v in shapes.items() if not v)
        raise SystemExit(f"build_map_svg: empty geometry for {missing}")

    all_pts = [pt for polys in shapes.values() for ring in polys for pt in ring]
    lons = [p[0] for p in all_pts]
    lats = [p[1] for p in all_pts]
    bbox = (min(lons), min(lats), max(lons), max(lats))

    names = {
        "tor": ("Toronto", counts.get("TOR", 0)),
        "miss": ("Mississauga", counts.get("MISS", 0)),
        "bram": ("Brampton", counts.get("BRAM", 0)),
        "cale": ("Caledon", None),
    }
    width = height = 0.0
    groups = []
    for key, polys in shapes.items():
        paths, width, height = project(polys, bbox)
        label, count = names[key]
        count_text = f"{count:,} permits" if count is not None else "no permit feed"
        title = f"{label}: {count_text} (gold layer, {args.ingest_date})"
        strokes = "".join(f'<path d="{d}" class="map-shape map-{key}"/>' for d in paths)
        xs = [float(p.split(",")[0]) for d in paths for p in d[1:-1].split("L")]
        ys = [float(p.split(",")[1]) for d in paths for p in d[1:-1].split("L")]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        groups.append(
            f'<g class="map-group" data-municipality="{key}">'
            f"<title>{html.escape(title)}</title>{strokes}"
            f'<text x="{cx:.1f}" y="{cy:.1f}" class="map-label" text-anchor="middle">'
            f"{html.escape(label)}</text>"
            f'<text x="{cx:.1f}" y="{cy + 34:.1f}" class="map-count" text-anchor="middle">'
            f"{html.escape(count_text)}</text></g>"
        )

    svg = (
        f"<!-- Generated by scripts/build_map_svg.py from bronze ingest_date={args.ingest_date} "
        f"and docs/measure-reconciliation.json. Regenerate, never hand-edit (ADR-0009). -->\n"
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        'role="img" aria-labelledby="mapTitle mapDesc" class="gta-map">'
        '<title id="mapTitle">GTA municipalities by permits issued</title>'
        '<desc id="mapDesc">Toronto, Mississauga, Brampton and Caledon drawn from '
        "real municipal boundary geometry, filled by gold-layer permit volume. "
        "Caledon has no permit feed.</desc>" + "".join(groups) + "</svg>\n"
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    total_pts = sum(len(r) for polys in shapes.values() for r in polys)
    print(f"map written: {out} ({total_pts} points, {len(shapes)} shapes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
