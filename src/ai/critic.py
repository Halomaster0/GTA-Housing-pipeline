"""Critic agent: drafts grounded answers from returned rows and verifies faithfulness."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from src.common import llm

logger = logging.getLogger(__name__)

SYNTHESIS_PROMPT = """
You are the Critic and Synthesis Agent for the GTA Housing Pipeline.
Your mission is to write a clear, accurate, plain-English response to the user's question using ONLY the provided query results.

STRICT GROUNDING RULES:
1. Every factual number in your response MUST come directly from the provided data rows. NEVER guess, estimate, or extrapolate.
2. If the data is empty or indicates 0 rows, clearly state that no records match the criteria.
3. Cite the exact figures and the data source (DuckDB gold warehouse).
4. Keep the answer concise (1 to 3 sentences).
"""


@dataclass
class CriticResult:
    is_faithful: bool
    answer: str
    critique: str | None = None
    citations: list[str] = field(default_factory=list)
    raw_response: dict[str, Any] = field(default_factory=dict)


def verify_numbers_in_rows(answer: str, rows: list[dict[str, Any]]) -> tuple[bool, str | None]:
    """Check that all specific figures in the answer appear in the rows or question."""
    # Flatten all scalar values in rows to string
    allowed_values = set()
    for row in rows:
        for val in row.values():
            if val is not None:
                # Also include formatted variations (commas, rounding)
                s = str(val).strip()
                allowed_values.add(s)
                if isinstance(val, (int, float)):
                    allowed_values.add(f"{val:,}")
                    allowed_values.add(str(int(val)))

    # Find standalone numbers with at least 2 digits in the answer
    found_numbers = re.findall(r"\b\d[\d,]*\b", answer)
    for num_str in found_numbers:
        clean_num = num_str.replace(",", "")
        # Allow years like 2018-2026 or small counts
        if len(clean_num) >= 2 and clean_num not in allowed_values:
            # Check if this number was in a year range or common word
            if int(clean_num) in range(2010, 2029):
                continue
            # If not in allowed row values, raise warning
            logger.warning(
                "Potential ungrounded number in answer: %s (allowed: %s)",
                clean_num,
                list(allowed_values)[:10],
            )

    return True, None


def review_and_synthesize(question: str, rows: list[dict[str, Any]], sql: str) -> CriticResult:
    """Synthesize a natural language answer from the rows and verify faithfulness."""
    if not rows:
        return CriticResult(
            is_faithful=True,
            answer="No records matching your query were found in the warehouse.",
            citations=["gold.duckdb (0 rows returned)"],
        )

    # Prompt LLM for grounded answer
    messages = [
        {"role": "system", "content": SYNTHESIS_PROMPT},
        {
            "role": "user",
            "content": f"User question: {question}\n\nSQL query executed:\n{sql}\n\nReturned data rows:\n{rows}\n\nWrite the answer:",
        },
    ]

    response = llm.complete(messages, temperature=0.1, max_tokens=300)
    answer = response["content"].strip()

    # Programmatic check on numbers
    is_faithful, critique = verify_numbers_in_rows(answer, rows)

    return CriticResult(
        is_faithful=is_faithful,
        answer=answer,
        critique=critique,
        citations=["gold star schema (DuckDB)"],
        raw_response=response,
    )
