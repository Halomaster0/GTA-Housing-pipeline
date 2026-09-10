"""Reconcile the headline measure library against the gold warehouse.

Every number a future dashboard page or README prints must trace to one of
these queries (truth discipline, build-plan §4). The script runs the full
measure library against the local warehouse and writes the results to
``docs/measure-reconciliation.json`` (committed). A dashboard number that
disagrees with this file is wrong until proven otherwise.

Measures that cannot be computed yet are listed under ``pending`` with the
reason and the owner — they are defined, not silently dropped.

Usage:
    python scripts/reconcile_measures.py [--warehouse PATH] [--out PATH]

Exit non-zero on any warehouse error. No network, no cost.
"""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parent.parent


def bronze_status() -> dict:
    """Per-source landed state from bronze manifests (for the landing status table).

    Read from local manifests, not the warehouse: the manifest is the record
    of what the source gave us (reported vs landed), the warehouse is what we
    built from it. No src import — this script runs under any interpreter.
    """
    sources = []
    pattern = str(REPO_ROOT / "data" / "bronze" / "*" / "ingest_date=*" / "manifest.json")
    for path in sorted(glob.glob(pattern)):
        try:
            manifest = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        sources.append(
            {
                "source": manifest.get("source"),
                "family": manifest.get("family"),
                "ingest_date": manifest.get("ingest_date"),
                "rows_landed": manifest.get("row_count"),
                "rows_reported": manifest.get("reported_total"),
                "count_match": manifest.get("count_match"),
                "status": manifest.get("status"),
            }
        )
    dates = sorted({s["ingest_date"] for s in sources if s["ingest_date"]})
    return {"ingest_date": dates[-1] if dates else None, "sources": sources}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warehouse",
        default=str(REPO_ROOT / "data" / "warehouse.duckdb"),
        help="Path to the DuckDB warehouse built by `make transform`.",
    )
    parser.add_argument(
        "--out",
        default=str(REPO_ROOT / "docs" / "measure-reconciliation.json"),
        help="Where to write the reconciliation JSON (committed).",
    )
    return parser.parse_args()


def scalar(con: duckdb.DuckDBPyConnection, sql: str) -> object:
    return con.execute(sql).fetchone()[0]


def rows(con: duckdb.DuckDBPyConnection, sql: str) -> list:
    return [list(r) for r in con.execute(sql).fetchall()]


def git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def build_report(con: duckdb.DuckDBPyConnection) -> dict:
    report: dict = {
        "meta": {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "git_sha": git_sha(),
            "source": "gold warehouse via scripts/reconcile_measures.py",
        },
        "fact_totals": {
            "fct_permits": scalar(con, "SELECT COUNT(*) FROM gold.fct_permits"),
            "fct_applications": scalar(con, "SELECT COUNT(*) FROM gold.fct_applications"),
        },
        "bronze": bronze_status(),
        "integrity": {
            "orphan_permit_fks": scalar(
                con,
                "SELECT COUNT(*) FROM gold.fct_permits f "
                "LEFT JOIN gold.dim_municipality m USING (municipality_sk) "
                "WHERE m.municipality_sk IS NULL",
            ),
            "orphan_application_fks": scalar(
                con,
                "SELECT COUNT(*) FROM gold.fct_applications f "
                "LEFT JOIN gold.dim_municipality m USING (municipality_sk) "
                "WHERE m.municipality_sk IS NULL",
            ),
            "permits_null_geography": scalar(
                con, "SELECT COUNT(*) FROM gold.fct_permits WHERE geography_sk IS NULL"
            ),
            "applications_null_geography": scalar(
                con,
                "SELECT COUNT(*) FROM gold.fct_applications WHERE geography_sk IS NULL",
            ),
            "permits_unknown_use": scalar(
                con,
                "SELECT COUNT(*) FROM gold.fct_permits f "
                "JOIN gold.dim_use_type u ON f.use_type_sk = u.use_type_sk "
                "WHERE u.use_type_code = 'UNKNOWN'",
            ),
            "applications_unknown_use": scalar(
                con,
                "SELECT COUNT(*) FROM gold.fct_applications f "
                "JOIN gold.dim_use_type u ON f.use_type_sk = u.use_type_sk "
                "WHERE u.use_type_code = 'UNKNOWN'",
            ),
        },
        "permits_by_municipality": {
            r[0]: r[1]
            for r in rows(
                con,
                "SELECT m.municipality_code, COUNT(*) FROM gold.fct_permits f "
                "JOIN gold.dim_municipality m USING (municipality_sk) "
                "GROUP BY 1 ORDER BY 1",
            )
        },
        "permits_issued_by_municipality_year": [
            {"municipality": r[0], "year": r[1], "permits_issued": r[2]}
            for r in rows(
                con,
                "SELECT m.municipality_code, d.year, COUNT(*) "
                "FROM gold.fct_permits f "
                "JOIN gold.dim_municipality m USING (municipality_sk) "
                "JOIN gold.dim_date d ON f.date_issued_sk = d.date_sk "
                "GROUP BY 1, 2 ORDER BY 1, 2",
            )
        ],
        "net_units_by_municipality": {
            r[0]: {"net_units": r[1], "permit_rows": r[2], "null_unit_rows": r[3]}
            for r in rows(
                con,
                "SELECT m.municipality_code, SUM(f.unit_count_net_new), COUNT(*), "
                "SUM(CASE WHEN f.unit_count_net_new IS NULL THEN 1 ELSE 0 END) "
                "FROM gold.fct_permits f "
                "JOIN gold.dim_municipality m USING (municipality_sk) "
                "GROUP BY 1 ORDER BY 1",
            )
        },
        "unit_basis": "unknown (ADR-0003 — cross-municipality unit sums are NOT comparable)",
        "applications_by_municipality_status": [
            {"municipality": r[0], "status": r[1], "applications": r[2]}
            for r in rows(
                con,
                "SELECT m.municipality_code, s.status_code, COUNT(*) "
                "FROM gold.fct_applications f "
                "JOIN gold.dim_municipality m USING (municipality_sk) "
                "JOIN gold.dim_status s ON f.status_sk = s.status_sk "
                "GROUP BY 1, 2 ORDER BY 1, 3 DESC",
            )
        ],
        "permits_by_municipality_status": [
            {"municipality": r[0], "status": r[1], "permits": r[2]}
            for r in rows(
                con,
                "SELECT m.municipality_code, s.status_code, COUNT(*) "
                "FROM gold.fct_permits f "
                "JOIN gold.dim_municipality m USING (municipality_sk) "
                "JOIN gold.dim_status s ON f.status_sk = s.status_sk "
                "GROUP BY 1, 2 ORDER BY 1, 3 DESC",
            )
        ],
        "permit_applied_to_issued_median_days": {
            r[0]: {"permits_with_both_dates": r[1], "median_days": float(r[2])}
            for r in rows(
                con,
                "SELECT m.municipality_code, COUNT(*), "
                "MEDIAN(d2.calendar_date - d1.calendar_date) "
                "FROM gold.fct_permits f "
                "JOIN gold.dim_municipality m USING (municipality_sk) "
                "JOIN gold.dim_date d1 ON f.date_applied_sk = d1.date_sk "
                "JOIN gold.dim_date d2 ON f.date_issued_sk = d2.date_sk "
                "GROUP BY 1 ORDER BY 1",
            )
        },
        "application_submitted_to_decision_median_days": {
            r[0]: {"applications_with_both_dates": r[1], "median_days": float(r[2])}
            for r in rows(
                con,
                "SELECT m.municipality_code, COUNT(*), "
                "MEDIAN(d2.calendar_date - d1.calendar_date) "
                "FROM gold.fct_applications f "
                "JOIN gold.dim_municipality m USING (municipality_sk) "
                "JOIN gold.dim_date d1 ON f.date_submitted_sk = d1.date_sk "
                "JOIN gold.dim_date d2 ON f.date_decision_sk = d2.date_sk "
                "GROUP BY 1 ORDER BY 1",
            )
        },
        "construction_value_cad_by_municipality": {
            r[0]: {
                "total_cad": float(r[1]) if r[1] is not None else None,
                "permit_rows": r[2],
                "null_value_rows": r[3],
            }
            for r in rows(
                con,
                "SELECT m.municipality_code, SUM(f.construction_value_cad), COUNT(*), "
                "SUM(CASE WHEN f.construction_value_cad IS NULL THEN 1 ELSE 0 END) "
                "FROM gold.fct_permits f "
                "JOIN gold.dim_municipality m USING (municipality_sk) "
                "GROUP BY 1 ORDER BY 1",
            )
        },
        "pending_measures": {
            "units_per_capita": "DEFINED, UNCOMPUTABLE — dim_municipality.population_latest "
            "is NULL everywhere; needs StatCan census profiles (blocked on series-pull "
            "HTTP 406, Gate 2 item iii). Owner: data-quality-auditor.",
            "application_to_permit_days": "DEFINED, UNCOMPUTABLE — no permit↔application "
            "key exists (ADR-0006, related_application_number NULL everywhere). "
            "Owner: transform-engineer (needs a proven key first).",
            "statcan_control_totals": "DEFINED, UNCOMPUTABLE — StatCan series unpulled "
            "(HTTP 406). No per-capita or control-total measure publishes until "
            "reconciliation exists. Owner: ingestion-engineer.",
            "brampton_construction_value": "DEFINED, EMPTY — Brampton feed carries no "
            "value field (all 221,319 rows NULL). Page shows Mississauga + Toronto "
            "only, labelled. Owner: none (source limitation).",
        },
    }
    return report


def main() -> int:
    args = parse_args()
    warehouse = Path(args.warehouse)
    if not warehouse.exists():
        print(f"reconcile_measures: warehouse not found: {warehouse}", file=sys.stderr)
        print("Run `make transform` first.", file=sys.stderr)
        return 1

    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        report = build_report(con)
    finally:
        con.close()

    out = Path(args.out)
    out.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")

    totals = report["fact_totals"]
    print(f"fact totals: permits={totals['fct_permits']} applications={totals['fct_applications']}")
    print(f"permits by muni: {report['permits_by_municipality']}")
    print(f"net units by muni: {report['net_units_by_municipality']}")
    print(f"permit applied->issued medians: {report['permit_applied_to_issued_median_days']}")
    print(
        "app submitted->decision medians: "
        f"{report['application_submitted_to_decision_median_days']}"
    )
    print(f"pending measures: {len(report['pending_measures'])} (defined, uncomputable)")
    print(f"reconciliation written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
