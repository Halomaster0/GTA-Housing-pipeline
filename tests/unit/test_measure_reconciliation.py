"""Contract test for the committed measure reconciliation file.

`docs/measure-reconciliation.json` is the serving contract (ADR-0008): every
dashboard number must agree with it. This test guards the file's shape so a
stale, hand-edited, or partially-written reconciliation fails CI instead of
reaching a report page. Values themselves are verified by re-running
`scripts/reconcile_measures.py`, not asserted here.
"""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]
RECONCILIATION = REPO_ROOT / "docs" / "measure-reconciliation.json"

KNOWN_MUNICIPALITIES = {"TOR", "MISS", "BRAM", "CALE", "PEEL"}


def load_report() -> dict:
    assert RECONCILIATION.exists(), (
        f"{RECONCILIATION} missing — run `make reconcile` "
        "(scripts/reconcile_measures.py) to regenerate it"
    )
    return json.loads(RECONCILIATION.read_text(encoding="utf-8"))


def test_required_sections_present() -> None:
    report = load_report()
    for section in (
        "meta",
        "fact_totals",
        "permits_by_municipality",
        "permits_issued_by_municipality_year",
        "net_units_by_municipality",
        "applications_by_municipality_status",
        "permits_by_municipality_status",
        "permit_applied_to_issued_median_days",
        "application_submitted_to_decision_median_days",
        "construction_value_cad_by_municipality",
        "pending_measures",
    ):
        assert section in report, f"reconciliation missing section: {section}"


def test_fact_totals_sane() -> None:
    totals = load_report()["fact_totals"]
    assert totals["fct_permits"] > 0 and totals["fct_applications"] > 0
    by_muni = load_report()["permits_by_municipality"]
    assert set(by_muni) <= KNOWN_MUNICIPALITIES
    assert sum(by_muni.values()) == totals["fct_permits"]


def test_pending_measures_defined_not_dropped() -> None:
    pending = load_report()["pending_measures"]
    for key in (
        "units_per_capita",
        "application_to_permit_days",
        "statcan_control_totals",
        "brampton_construction_value",
    ):
        assert key in pending, f"pending measure silently dropped: {key}"
        assert "DEFINED" in pending[key]


def test_medians_non_negative() -> None:
    report = load_report()
    for muni, entry in report["permit_applied_to_issued_median_days"].items():
        assert entry["median_days"] >= 0, f"negative median for {muni}"
        assert entry["permits_with_both_dates"] > 0
