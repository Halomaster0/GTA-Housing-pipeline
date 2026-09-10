"""PII contract tests: ruled drops are registered, review flags are explicit.

The DROP lists encode live observations from 2026-09-10 (field capture):
Toronto CONTACT_* and the Peel councillor/name columns exist in the source
schemas and must not survive into silver. If a source adds a new PII-shaped
column, these tests do not catch it — that is the drift detector's and the
silver review's job. These tests catch the opposite failure: a ruled drop
being edited out of the registry.
"""

from __future__ import annotations

import pytest

from src.ingest.pii import PII_DROP, PII_REVIEW, columns_for, drop_columns

pytestmark = pytest.mark.unit


def test_toronto_contacts_are_drops() -> None:
    drops = columns_for("toronto-development-applications")
    assert drops == ["CONTACT_NAME", "CONTACT_PHONE", "CONTACT_EMAIL"]


def test_peel_current_wards_drops() -> None:
    assert columns_for("peel-wards-current") == ["Mayor", "RegionalCo", "LocalCounc"]


def test_peel_prior_wards_drops() -> None:
    drops = columns_for("peel-wards-prior")
    for column in (
        "Mayor",
        "FirstName0",
        "LastName0",
        "Phone0",
        "email0",
        "FirstName1",
        "LastName1",
        "Phone1",
        "email1",
        "RC_Name",
    ):
        assert column in drops, f"{column} missing from peel-wards-prior drops"


def test_drop_columns_removes_only_listed() -> None:
    records = [{"A": 1, "CONTACT_NAME": "X", "CONTACT_PHONE": "Y", "CONTACT_EMAIL": "Z"}]
    cleaned = drop_columns(records, columns_for("toronto-development-applications"))
    assert cleaned == [{"A": 1}]
    # Input records are not mutated.
    assert records[0]["CONTACT_NAME"] == "X"


def test_drop_columns_tolerates_absent_column() -> None:
    assert drop_columns([{"A": 1}], ["CONTACT_NAME"]) == [{"A": 1}]


def test_review_lists_are_explicit_and_disjoint_from_drops() -> None:
    assert PII_REVIEW, "review list must not be empty: silent keeps are banned"
    for source_id, columns in PII_REVIEW.items():
        assert columns, f"{source_id}: empty review list"
        overlap = set(columns) & set(PII_DROP.get(source_id, []))
        assert not overlap, f"{source_id}: {overlap} in both DROP and REVIEW"


def test_all_drop_and_review_sources_have_ingest_specs() -> None:
    from src.ingest.spec import load_specs

    spec_ids = {spec.id for spec in load_specs()}
    for source_id in list(PII_DROP) + list(PII_REVIEW):
        assert source_id in spec_ids, f"{source_id}: PII entry without an ingest spec"
