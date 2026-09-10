"""Key-stability checker tests, including the proven Toronto duplicate shape.

The observe-policy fixture mirrors the live 2026-09-10 finding (ADR-0005):
several address-rows sharing one APPLICATION#. The checker must report that
shape without failing — while the unique policy fails loudly on it.
"""

from __future__ import annotations

import pytest

from src.ingest.base import IngestError
from src.ingest.keys import check_keys

pytestmark = pytest.mark.unit


def test_unique_passes_on_distinct_keys() -> None:
    records = [{"PERMIT_NUM": "A"}, {"PERMIT_NUM": "B"}]
    check = check_keys("s", records, ["PERMIT_NUM"], "unique")
    assert check.passed and check.duplicates == 0 and check.distinct == 2


def test_unique_fails_loudly_on_duplicates() -> None:
    records = [{"PERMIT_NUM": "A"}, {"PERMIT_NUM": "A"}]
    check = check_keys("s", records, ["PERMIT_NUM"], "unique")
    assert not check.passed and check.duplicates == 1


def test_observe_reports_toronto_application_shape() -> None:
    records = [
        {"APPLICATION#": "22 114201 WET 05 OZ", "STREET_NUM": "5 A"},
        {"APPLICATION#": "22 114201 WET 05 OZ", "STREET_NUM": "7"},
        {"APPLICATION#": "21 235816 WET 07 OZ", "STREET_NUM": "1"},
    ]
    check = check_keys("toronto-development-applications", records, ["APPLICATION#"], "observe")
    assert check.passed and check.rows == 3 and check.distinct == 2 and check.duplicates == 1


def test_missing_key_column_is_loud_under_both_policies() -> None:
    with pytest.raises(IngestError):
        check_keys("s", [{"OTHER": 1}], ["PERMIT_NUM"], "unique")
    with pytest.raises(IngestError):
        check_keys("s", [{"OTHER": 1}], ["PERMIT_NUM"], "observe")


def test_composite_keys_and_nulls() -> None:
    records = [{"A": "x", "B": None}, {"A": "x", "B": None}]
    check = check_keys("s", records, ["A", "B"], "unique")
    assert not check.passed


def test_empty_batch_passes_with_zero_counts() -> None:
    check = check_keys("s", [], ["PERMIT_NUM"], "unique")
    assert check.passed and check.rows == 0 and check.distinct == 0
