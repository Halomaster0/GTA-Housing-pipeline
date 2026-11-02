"""
Repair the golden evaluation set (evals/golden_questions.yaml).

Two classes of defect existed in the hand-authored golden set:

  1. expected_sql was written against a schema that does not exist
     (use_type_name, dim_geography.municipality_sk, status_code='ACTIVE',
     use_type_code='residential', ...).
  2. expected_facts were copied from a stale warehouse snapshot, so they no
     longer matched what the question's own reference SQL returns.

Repair rules
-------------
* Apply corrected reference SQL (SQL_OVERRIDES / QUESTION_REWRITES).
* Re-derive *count* facts by executing the reference SQL against the current
  warehouse.  Facts that are qualifiers (a year, a ward code) are detected
  because they occur in the question text or in the query output, and are kept.
* Label facts are kept only when the question or the query output can justify
  them; impossible labels (e.g. 'ACTIVE', which is not a status in dim_status)
  are dropped or the question is rewritten.
* The YAML document structure (top-level keys) is preserved.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

import duckdb
import yaml

HERE = Path(__file__).resolve().parent
GOLDEN = HERE / "golden_questions.yaml"
# Re-baselined 2026-11-02 against the September build (the /ask data source).
DB = HERE.parent / "data" / "warehouse-sept.duckdb"

# --- Corrected reference SQL -------------------------------------------------
SQL_OVERRIDES: dict[str, str] = {
    # dim_status has no 'ACTIVE'; "still open" == application status not terminal.
    "agg-07": (
        "SELECT count(*) AS open_applications FROM gold.fct_applications a "
        "JOIN gold.dim_status s ON a.status_sk = s.status_sk "
        "WHERE s.applies_to = 'application' AND s.is_terminal = FALSE;"
    ),
    "comp-02": (
        "SELECT m.municipality_name, count(*) AS open_applications "
        "FROM gold.fct_applications a "
        "JOIN gold.dim_municipality m ON a.municipality_sk = m.municipality_sk "
        "JOIN gold.dim_status s ON a.status_sk = s.status_sk "
        "WHERE s.applies_to = 'application' AND s.is_terminal = FALSE "
        "AND m.municipality_code IN ('MISS', 'BRAM') "
        "GROUP BY m.municipality_name ORDER BY m.municipality_name;"
    ),
    # No COMMERCIAL/INDUSTRIAL use types exist; use the real ones.
    # Mississauga has no mixed-use permits; Brampton does.
    "comp-08": (
        "SELECT u.use_type_label, count(*) AS permits_issued "
        "FROM gold.fct_permits p "
        "JOIN gold.dim_municipality m ON p.municipality_sk = m.municipality_sk "
        "JOIN gold.dim_use_type u ON p.use_type_sk = u.use_type_sk "
        "WHERE m.municipality_code = 'BRAM' "
        "AND u.use_type_code IN ('RESIDENTIAL', 'MIXED_USE') "
        "AND p.date_issued_sk IS NOT NULL "
        "GROUP BY u.use_type_label ORDER BY u.use_type_label;"
    ),
    "sem-04": (
        "SELECT count(*) AS mixed_use_permits FROM gold.fct_permits p "
        "JOIN gold.dim_municipality m ON p.municipality_sk = m.municipality_sk "
        "JOIN gold.dim_use_type u ON p.use_type_sk = u.use_type_sk "
        "WHERE m.municipality_code = 'BRAM' "
        "AND u.use_type_code = 'MIXED_USE' AND p.date_issued_sk IS NOT NULL;"
    ),
    # No permit fact row carries use_type_code='UNKNOWN'; use infrastructure.
    "sem-08": (
        "SELECT count(*) AS infrastructure_permits FROM gold.fct_permits p "
        "JOIN gold.dim_use_type u ON p.use_type_sk = u.use_type_sk "
        "WHERE u.use_type_code = 'INFRASTRUCTURE';"
    ),
    "sem-03": (
        "SELECT count(*) AS institutional_permits FROM gold.fct_permits p "
        "JOIN gold.dim_municipality m ON p.municipality_sk = m.municipality_sk "
        "JOIN gold.dim_use_type u ON p.use_type_sk = u.use_type_sk "
        "WHERE m.municipality_code = 'BRAM' "
        "AND u.use_type_code = 'INSTITUTIONAL' AND p.date_issued_sk IS NOT NULL;"
    ),
    # dim_geography links to municipality by name (there is no municipality_sk).
    "geo-07": (
        "SELECT count(DISTINCT g.ward_code) AS distinct_wards "
        "FROM gold.dim_geography g WHERE g.municipality = 'Mississauga';"
    ),
    "geo-08": (
        "SELECT count(*) AS ward_records FROM gold.dim_geography g "
        "WHERE g.municipality = 'Toronto';"
    ),
    # dim_use_type column is use_type_label (not use_type_name).
    "sem-01": (
        "SELECT u.use_type_label, count(*) AS permit_count "
        "FROM gold.fct_permits p "
        "JOIN gold.dim_use_type u ON p.use_type_sk = u.use_type_sk "
        "GROUP BY u.use_type_label ORDER BY permit_count DESC;"
    ),
    # 'ACTIVE' is not an application status; compare closed vs under review.
    "comp-07": (
        "SELECT s.status_code, count(*) AS application_count "
        "FROM gold.fct_applications a "
        "JOIN gold.dim_status s ON a.status_sk = s.status_sk "
        "WHERE s.applies_to = 'application' "
        "AND s.status_code IN ('CLOSED', 'UNDER_REVIEW') "
        "GROUP BY s.status_code ORDER BY s.status_code;"
    ),
}

# use_type_code values are upper-case in dim_use_type.
SQL_LITERAL_FIXES: dict[str, tuple[str, str]] = {
    "sem-02": ("u.use_type_code = 'residential'", "u.use_type_code = 'RESIDENTIAL'"),
    "sem-05": ("u.use_type_code = 'institutional'", "u.use_type_code = 'INSTITUTIONAL'"),
    "sem-07": ("u.use_type_code = 'mixed-use'", "u.use_type_code = 'MIXED_USE'"),
    "sem-08": ("u.use_type_code = 'unknown'", "u.use_type_code = 'UNKNOWN'"),
}

QUESTION_REWRITES: dict[str, str] = {
    "agg-07": (
        "How many development applications across the GTA are still open "
        "(submitted, under review, or under appeal)?"
    ),
    "comp-02": (
        "Compare the number of still-open development applications between "
        "Mississauga and Brampton."
    ),
    "comp-07": (
        "How do closed development application counts compare to under-review "
        "application counts across all GTA municipalities?"
    ),
    "comp-08": (
        "In Brampton, are there more residential or mixed-use permits issued?"
    ),
    "sem-03": "How many institutional permits were issued in Brampton?",
    "sem-04": "How many mixed-use permits were issued in Brampton?",
    "sem-08": "How many infrastructure permits exist in the warehouse?",
}

# Label facts that the query itself dictates.
LABEL_OVERRIDES: dict[str, list[str]] = {
    "agg-07": [],
    "comp-02": ["Brampton", "Mississauga"],
    "comp-07": ["CLOSED", "UNDER_REVIEW"],
    "comp-08": ["Residential", "Mixed use"],
    "sem-01": ["Residential", "Mixed use", "Institutional"],
    "sem-03": ["Brampton", "institutional"],
    "sem-04": ["Brampton", "mixed-use"],
    "sem-08": ["infrastructure"],
}

NUMERIC_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def is_numeric(fact: object) -> bool:
    return bool(NUMERIC_RE.match(str(fact).replace(",", "").strip()))


def fmt(value: object) -> str:
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def norm(text: object) -> str:
    return str(text).lower().replace("_", " ").strip()


def load_questions() -> tuple[dict, list[dict]]:
    doc = yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))
    if isinstance(doc, list):
        return {"questions": doc}, doc
    for value in doc.values():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return doc, value
    raise SystemExit("Could not locate question list in golden_questions.yaml")


def main() -> None:
    doc, questions = load_questions()
    con = duckdb.connect(str(DB), read_only=True)
    changes: list[str] = []

    for q in questions:
        qid = q["id"]

        if qid in QUESTION_REWRITES:
            old = q["question"]
            q["question"] = QUESTION_REWRITES[qid]
            changes.append(f"{qid}: question rewritten\n    - {old}\n    + {q['question']}")

        sql = SQL_OVERRIDES.get(qid)
        if sql is None:
            sql = q.get("expected_sql")
            if qid in SQL_LITERAL_FIXES:
                old_frag, new_frag = SQL_LITERAL_FIXES[qid]
                sql = sql.replace(old_frag, new_frag)
                changes.append(f"{qid}: sql literal fixed -> {new_frag}")
        if sql:
            q["expected_sql"] = sql

        facts = list(q.get("expected_facts") or [])
        if not sql:
            continue

        try:
            rows = con.execute(sql).fetchall()
        except Exception as exc:
            changes.append(f"{qid}: SQL STILL FAILS -> {exc}")
            continue

        out_text = " ".join(str(v) for row in rows for v in row)
        out_norm = norm(out_text)
        numeric_values = [
            fmt(v)
            for row in rows
            for v in row
            if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool)
        ]

        question_norm = norm(q["question"])
        kept: list[str] = []
        stale_counts: list[str] = []

        for fact in facts:
            token = norm(fact)
            if is_numeric(fact):
                # A numeric fact is a qualifier (year / ward code) when it is
                # visible in the question or in the query output.
                if token in question_norm or token in out_norm:
                    kept.append(str(fact))
                else:
                    stale_counts.append(str(fact))
            else:
                if token in question_norm or token in out_norm:
                    kept.append(str(fact))
                else:
                    changes.append(f"{qid}: dropped impossible label fact {fact!r}")

        if qid in LABEL_OVERRIDES:
            kept = [k for k in kept if norm(k) not in {norm(x) for x in LABEL_OVERRIDES[qid]}]
            kept += [str(x) for x in LABEL_OVERRIDES[qid]]

        if stale_counts:
            if numeric_values:
                kept += numeric_values
                changes.append(
                    f"{qid}: counts {stale_counts} -> {numeric_values}"
                )
            else:
                changes.append(f"{qid}: counts {stale_counts} but query returned no number")
        elif qid in LABEL_OVERRIDES:
            changes.append(f"{qid}: labels -> {kept}")

        q["expected_facts"] = kept

    con.close()

    GOLDEN.write_text(
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )

    print(f"Rewrote {GOLDEN}")
    print(f"{len(changes)} change(s):\n")
    for c in changes:
        print(" -", c)


if __name__ == "__main__":
    main()
