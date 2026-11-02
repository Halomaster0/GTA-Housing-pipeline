"""Planner agent: classifies intent, enforces boundary checks, and generates SQL plans."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from src.common import llm

logger = logging.getLogger(__name__)

GOLD_SCHEMA_PROMPT = """
You are the query planner for the GTA Housing Pipeline.
Your role is to translate questions about GTA building permits and development applications into read-only SQL queries against DuckDB.

SCHEMA CONTEXT:
The database contains a dimensional star schema in the 'gold' schema.
These column names and values are EXACT - do not invent alternatives:

- gold.fct_permits:
    permit_sk (BIGINT)
    municipality_sk (BIGINT, joins gold.dim_municipality.municipality_sk)
    permit_number (VARCHAR)
    geography_sk (BIGINT, joins gold.dim_geography.geography_sk)
    use_type_sk (INTEGER, joins gold.dim_use_type.use_type_sk)
    use_type_raw (VARCHAR), use_type_classification_method (VARCHAR)
    status_sk (INTEGER, joins gold.dim_status.status_sk), status_raw (VARCHAR)
    date_applied_sk (BIGINT, joins gold.dim_date.date_sk)
    date_issued_sk (BIGINT, joins gold.dim_date.date_sk, NULL if not yet issued)
    date_closed_sk (BIGINT, joins gold.dim_date.date_sk)
    unit_count_net_new (BIGINT; Toronto is net of demolition, Brampton/Mississauga are gross - NEVER SUM ACROSS MUNICIPALITIES)
    unit_count_basis (VARCHAR)
    construction_value_cad (DECIMAL(21,2))
    floor_area_sqm (DOUBLE)

- gold.fct_applications:
    application_sk (BIGINT)
    municipality_sk (BIGINT, joins gold.dim_municipality.municipality_sk)
    application_number (VARCHAR)
    geography_sk (BIGINT, joins gold.dim_geography.geography_sk)
    use_type_sk (INTEGER, joins gold.dim_use_type.use_type_sk)
    use_type_classification_method (VARCHAR)
    status_sk (INTEGER, joins gold.dim_status.status_sk), status_raw (VARCHAR)
    date_submitted_sk (BIGINT, joins gold.dim_date.date_sk)
    date_decision_sk (BIGINT, joins gold.dim_date.date_sk; Mississauga only, Toronto & Brampton are NULL)
    unit_count_proposed (BIGINT), unit_count_basis (VARCHAR)

- gold.dim_municipality:
    municipality_sk (BIGINT)
    municipality_code (VARCHAR: 'TOR', 'MISS', 'BRAM', 'CALE', 'PEEL')
    municipality_name (VARCHAR: 'Toronto', 'Mississauga', 'Brampton', 'Caledon', 'Peel Region')
    municipality_tier (VARCHAR), parent_region_code (VARCHAR)
    is_permit_issuing_authority (BOOLEAN: True for TOR, MISS, BRAM; False for CALE, PEEL)

- gold.dim_date:
    date_sk (BIGINT)
    calendar_date (DATE), year (INTEGER), quarter (INTEGER), month (INTEGER), month_name (VARCHAR)

- gold.dim_status:
    status_sk (INTEGER)
    applies_to (VARCHAR: 'permit' or 'application')
    status_code (VARCHAR)
    status_label (VARCHAR)
    is_terminal (BOOLEAN)
    PERMIT status_code values: 'APPLIED', 'UNDER_REVIEW', 'ISSUED', 'CLOSED', 'CANCELLED', 'EXPIRED', 'UNKNOWN'
    APPLICATION status_code values: 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REFUSED', 'APPEALED', 'WITHDRAWN', 'CLOSED', 'UNKNOWN'
    There is NO 'ACTIVE' status code. "still open" / "not final" / "active" applications
    = applications whose status is not terminal: status_code IN ('SUBMITTED', 'UNDER_REVIEW', 'APPEALED')
    (equivalently s.applies_to = 'application' AND s.is_terminal = FALSE).

- gold.dim_use_type:
    use_type_sk (INTEGER)
    use_type_code (VARCHAR: 'RESIDENTIAL', 'MIXED_USE', 'INSTITUTIONAL', 'INFRASTRUCTURE', 'OTHER', 'UNKNOWN')
    use_type_label (VARCHAR: 'Residential', 'Mixed use', 'Institutional', 'Infrastructure', 'Other non-residential scope', 'No use signal in source')
    applies_to (VARCHAR: 'both')
    There is NO 'COMMERCIAL' and NO 'INDUSTRIAL' use type.

- gold.dim_geography:
    geography_sk (BIGINT)
    municipality (VARCHAR: 'Toronto', 'Mississauga', 'Brampton', 'Caledon')  <-- NAME, not a key
    ward_code (VARCHAR, e.g. '1', '10'), ward_name (VARCHAR, e.g. 'Ward 1')
    vintage (VARCHAR), is_current (BOOLEAN)
    dim_geography has NO municipality_sk column. Join it to a municipality by NAME:
    CORRECT: WHERE g.municipality = 'Toronto' AND g.ward_code = '10'
    WRONG:   JOIN gold.dim_municipality m ON g.municipality_sk = m.municipality_sk

CRITICAL SQL RULES — follow these exactly:

*** ABSOLUTE PRIORITY RULE ***
"ISSUED permits" ALWAYS means: date_issued_sk IS NOT NULL
NEVER use dim_status.status_code = 'ISSUED' — that is WRONG and will be severely penalized.
The status_code='ISSUED' filter only matches a SUBSET of records and produces 10x too few counts.
The dim_status table exists for filtering application lifecycle statuses (UNDER_REVIEW, CLOSED, APPROVED, ...), NOT for permit issuance counts.

CORRECT: SELECT COUNT(*) FROM gold.fct_permits WHERE date_issued_sk IS NOT NULL
CORRECT: SELECT COUNT(*) FROM gold.fct_permits p JOIN gold.dim_municipality m ON p.municipality_sk = m.municipality_sk WHERE m.municipality_code = 'MISS' AND p.date_issued_sk IS NOT NULL
WRONG:   SELECT COUNT(*) FROM gold.fct_permits p JOIN gold.dim_status s ON p.status_sk = s.status_sk WHERE s.status_code = 'ISSUED'

1. "ISSUED permits" means date_issued_sk IS NOT NULL. Do NOT filter on dim_status.status_code = 'ISSUED'; that is unreliable.
   CORRECT: SELECT COUNT(*) FROM gold.fct_permits WHERE date_issued_sk IS NOT NULL
   WRONG:   SELECT COUNT(*) FROM gold.fct_permits p JOIN gold.dim_status s ON ... WHERE s.status_code = 'ISSUED'

2. "All permit records" (total permits, without issued filter) means no date filter at all.
   CORRECT: SELECT COUNT(*) FROM gold.fct_permits p JOIN gold.dim_municipality m ON p.municipality_sk = m.municipality_sk WHERE m.municipality_code = 'TOR'

3. Date arithmetic: date_sk is a surrogate key, NOT a day number. NEVER subtract two date_sk values.
   Join gold.dim_date for real dates and use:
   DATEDIFF('day', d1.calendar_date, d2.calendar_date) or (d2.calendar_date - d1.calendar_date)

4. Municipality filter: for gold.dim_municipality ALWAYS use municipality_code ('TOR', 'MISS', 'BRAM'), NEVER municipality_name.
   WRONG: WHERE m.municipality_name = 'Toronto'
   (gold.dim_geography is the exception: it stores the municipality NAME in g.municipality.)

5. Always add LIMIT 1000 to aggregations; LIMIT 100 to row-level queries.

6. DO NOT add a LIMIT to COUNT(*) or SUM() aggregations that return a single row.

7. "Still open / active / not final development applications" =
   status_code IN ('SUBMITTED', 'UNDER_REVIEW', 'APPEALED') on gold.fct_applications.
   There is no 'ACTIVE' status code.

BOUNDARY & REFUSAL RULES:
1. GEOGRAPHIC SCOPE: The pipeline only covers Toronto, Mississauga, Brampton, and Peel Region. Questions about Vancouver, Montreal, Calgary, Ottawa, etc. MUST be refused.
2. PII / PRIVACY: Personal names, owner names, phone numbers, or individual applicant identities are scrubbed and MUST be refused.
3. PRICE FORECASTING: The pipeline does not predict real estate prices or market trends. Questions asking for 2030 prices or market forecasts MUST be refused.
4. PERMIT-APPLICATION LINKAGE: No linking key exists in municipal sources between permits and applications (ADR-0006). Questions asking for application-to-permit turnaround time MUST be refused.
5. PER-CAPITA METRICS: Population per-capita figures (measure P1) are pending StatCan ingestion and MUST be refused as not yet computable.
6. APPLICATION DECISION DATES: Decision dates are only reported for Mississauga. Questions asking for Toronto or Brampton application decision times MUST be refused.
7. CALEDON & PEEL: Caledon issues no permits in these feeds (ADR-0004); Peel is upper-tier and issues no building permits. Asking for Caledon or Peel building permits MUST be refused.
8. NET UNITS ACROSS MUNICIPALITIES: NEVER sum unit_count_net_new across municipalities (methodology differs). If asked, refuse with this reason.

OUTPUT FORMAT:
You MUST respond with valid JSON containing:
{
  "refusal": true or false,
  "refusal_reason": "Explanation if refusal is true, otherwise null",
  "intent": "Brief description of the query intent",
  "sql": "DuckDB SQL query if refusal is false, otherwise null"
}
"""


@dataclass
class Plan:
    is_refusal: bool
    refusal_reason: str | None = None
    intent: str = ""
    sql: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


def plan_query(question: str, _retry: bool = False) -> Plan:
    """Analyze a user question and generate a structured execution plan or refusal."""
    logger.info("Planning question: %s", question)
    
    # Fast programmatic boundary checks before calling LLM
    q_lower = question.lower()
    
    if any(city in q_lower for city in ["vancouver", "montreal", "calgary", "edmonton", "ottawa"]):
        return Plan(
            is_refusal=True,
            refusal_reason="This pipeline only covers the Greater Toronto Area (Toronto, Mississauga, Brampton, and Peel Region).",
            intent="Out of geographic scope"
        )
        
    if any(w in q_lower for w in ["owner", "applicant name", "who owns", "who applied"]):
        return Plan(
            is_refusal=True,
            refusal_reason="Personally identifiable information (PII) including owner and applicant names is intentionally scrubbed from the warehouse.",
            intent="PII request"
        )

    if any(w in q_lower for w in ["forecast", "predict home price", "future price", "price in 2030", "market forecast"]):
        return Plan(
            is_refusal=True,
            refusal_reason="This project is an open data pipeline and does not forecast housing market sale prices.",
            intent="Forecasting out of scope"
        )

    if "application to permit" in q_lower or "application-to-permit" in q_lower:
        return Plan(
            is_refusal=True,
            refusal_reason="Per ADR-0006, no linking key exists between development applications and building permits in source feeds; this duration is not computable.",
            intent="Unlinked entities (ADR-0006)"
        )

    if "per-capita" in q_lower or "per capita" in q_lower:
        return Plan(
            is_refusal=True,
            refusal_reason="Per-capita metrics (P1) are pending Statistics Canada census profile integration and are not yet computable.",
            intent="Pending measure P1"
        )

    if ("decision" in q_lower or "turnaround" in q_lower) and "application" in q_lower and ("toronto" in q_lower or "brampton" in q_lower):
        return Plan(
            is_refusal=True,
            refusal_reason="Decision dates for development applications are not published by Toronto or Brampton municipal feeds.",
            intent="Missing decision date field"
        )

    if ("caledon" in q_lower or "peel" in q_lower) and "permit" in q_lower:
        return Plan(
            is_refusal=True,
            refusal_reason="Neither Caledon nor Peel Region issues building permits in the ingested data feeds (ADR-0004).",
            intent="Non-issuing municipal authority"
        )

    # Prompt the LLM for SQL generation
    messages = [
        {"role": "system", "content": GOLD_SCHEMA_PROMPT},
        {"role": "user", "content": f"User question: {question}\n\nReturn JSON only."}
    ]

    response = llm.complete(messages, temperature=0.1, max_tokens=1200)

    # Guard: LLM unavailable or returned empty content
    if response is None or response.get("content") is None:
        logger.error("LLM returned None content for question: %s", question)
        return Plan(
            is_refusal=True,
            refusal_reason="The AI query service is temporarily unavailable. Please try again.",
            intent="LLM unavailable",
        )

    text = response["content"].strip()
    
    # Strip markdown fences if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        parsed = json.loads(text)
        
        # Validate that issued‑permit queries use date_issued_sk IS NOT NULL, not dim_status
        if not parsed.get("refusal") and parsed.get("sql"):
            sql_lower = parsed["sql"].lower()
            # If question contains keywords like "issued permits" or "how many permits were issued"
            if ("issued" in q_lower and "permit" in q_lower) or "how many permits were issued" in q_lower:
                # Check if SQL contains dim_status with 'issued' (incorrect) and NOT date_issued_sk IS NOT NULL (correct)
                has_dim_status = "dim_status" in sql_lower and "status_code" in sql_lower
                has_date_filter = "date_issued_sk is not null" in sql_lower or "date_issued_sk is not null" in sql_lower or "date_issued_sk is not null" in sql_lower.replace(' ', '').lower()
                if has_dim_status and not has_date_filter:
                    # Ask the LLM to retry with correct SQL
                    logger.warning(
                        "Planner returned SQL for issued permits that uses dim_status instead of date_issued_sk. Refusing to allow incorrect pattern."
                    )
                    return Plan(
                        is_refusal=True,
                        refusal_reason="Issued‑permit queries must use `date_issued_sk IS NOT NULL`. Please generate a compliant query.",
                        intent="Invalid issued‑permit query pattern",
                        sql=None,
                        raw_response=response,
                    )
        
        return Plan(
            is_refusal=parsed.get("refusal", False),
            refusal_reason=parsed.get("refusal_reason"),
            intent=parsed.get("intent", ""),
            sql=parsed.get("sql"),
            raw_response=response
        )
    except json.JSONDecodeError as err:
        logger.warning("Failed to parse planner JSON: %s. Response was: %s", err, text)
        # Fallback if model output SQL directly
        if "SELECT" in text.upper():
            return Plan(
                is_refusal=False,
                intent="Direct SQL fallback",
                sql=text,
                raw_response=response
            )
        # One retry: a single unparseable reply refused the question outright
        # (trend-06, 2026-11-02). Costs one extra model call, only on this path.
        if not _retry:
            logger.warning("Planner output unparseable; retrying once.")
            return plan_query(question, _retry=True)
        return Plan(
            is_refusal=True,
            refusal_reason="Could not construct a valid query plan for this question.",
            intent="Parse failure",
            raw_response=response
        )

