"""Registry guards for config/sources.yml.

These tests encode the decisions of 2026-09-10 (HANDOVER-1 items 1-3) so they
cannot silently regress:

- No `_DEV`/`_UAT` layer URL may be registered without a written justification
  (Brampton's `_DEV` copies are frozen, plausible-looking, and wrong).
- Every `verified-live` entry must carry a real observation: `observed_rows`,
  a calibrated threshold, a named licence, and a verification date.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "sources.yml"

FORBIDDEN_SUFFIXES = ("_DEV", "_UAT")


def load_registry() -> list[dict]:
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    assert raw and "sources" in raw, "sources.yml has no top-level 'sources' key"
    return raw["sources"]


def test_no_unjustified_dev_uat_layers() -> None:
    """A _DEV/_UAT check_url without justification fails loudly.

    Justification means the entry's `notes` explicitly explains why the
    non-production copy is the correct feed. Absence of notes (or notes that
    never mention the suffix) is not justification.
    """
    offenders = []
    for entry in load_registry():
        url = entry.get("check_url", "")
        if any(suffix in url for suffix in FORBIDDEN_SUFFIXES):
            notes = entry.get("notes", "") or ""
            if not any(suffix in notes for suffix in FORBIDDEN_SUFFIXES):
                offenders.append(entry["id"])
    assert not offenders, "registered _DEV/_UAT layers without written justification: " + ", ".join(
        offenders
    )


def test_verified_live_entries_have_evidence() -> None:
    """`verified-live` must mean something: observation + threshold + licence + date."""
    problems = []
    for entry in load_registry():
        if entry.get("status") != "verified-live":
            continue
        for field in ("observed_rows", "verified_on", "licence"):
            if entry.get(field) in (None, "", 0):
                problems.append(f"{entry['id']}: missing {field}")
        if not entry.get("expected_min_rows_calibrated"):
            problems.append(f"{entry['id']}: threshold not calibrated")
        licence = (entry.get("licence") or "").upper()
        if "UNVERIFIED" in licence:
            problems.append(f"{entry['id']}: licence still unverified")
    assert not problems, "verified-live entries lacking evidence:\n" + "\n".join(problems)


def test_source_ids_unique() -> None:
    ids = [entry["id"] for entry in load_registry()]
    assert len(ids) == len(set(ids)), "duplicate source ids in registry"
