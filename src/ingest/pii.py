"""PII column registry: what is dropped at bronze→silver, and what is flagged.

Two tiers, deliberately separate:

- DROP: columns proven to identify individuals (Toronto applicant contact
  fields; Peel councillor contact/name columns — all observed live
  2026-09-10). Silver drops these unconditionally; a data test enforces it.
- REVIEW: name/org columns that *may* identify individuals (builders,
  applicants, planners, contractors). Silver decides per column with a
  documented reason; nothing here is auto-dropped, nothing is auto-kept.

The Open Government Licence - Toronto excludes Personal Information, which
is why CONTACT_* cannot survive into any published layer regardless of
utility.
"""

from __future__ import annotations

from typing import Any

# Columns removed at bronze→silver, no exceptions. Keys are ingest spec ids.
PII_DROP: dict[str, list[str]] = {
    "toronto-development-applications": ["CONTACT_NAME", "CONTACT_PHONE", "CONTACT_EMAIL"],
    "peel-wards-current": ["Mayor", "RegionalCo", "LocalCounc"],
    "peel-wards-prior": [
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
    ],
}

# Columns flagged for a documented silver-time decision. Presence here means
# "decide explicitly", not "drop" and not "keep".
PII_REVIEW: dict[str, list[str]] = {
    "toronto-building-permits-active": ["BUILDER_NAME"],
    "toronto-building-permits-cleared": ["BUILDER_NAME"],
    "mississauga-site-plan-applications": ["APPLICANT", "PLANNER"],
    "mississauga-rezoning-applications": ["APPLICANT", "PLANNER"],
    "brampton-building-permits": ["BUILDER", "CONTRACTOR"],
}


def drop_columns(records: list[dict[str, Any]], columns: list[str]) -> list[dict[str, Any]]:
    """Return copies of records without the listed columns.

    Missing columns are ignored (a source that stops publishing a PII field
    is good news, not an error) — but callers that need a guarantee should
    assert absence separately via tests/data/.
    """
    doomed = set(columns)
    return [{k: v for k, v in record.items() if k not in doomed} for record in records]


def columns_for(source_id: str) -> list[str]:
    return list(PII_DROP.get(source_id, []))
