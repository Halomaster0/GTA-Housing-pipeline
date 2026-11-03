"""Multi-agent query graph: orchestrates Planner, Executor, and Critic with tracing."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from src.ai import critic, executor, planner
from src.common import config

logger = logging.getLogger(__name__)

TRACES_DIR = config.REPO_ROOT / "traces"


@dataclass
class QueryResponse:
    trace_id: str
    question: str
    answer: str
    is_refusal: bool
    refusal_reason: str | None = None
    sql: str | None = None
    rows: list[dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    citations: list[str] = field(default_factory=list)
    confidence: float = 1.0
    latency_ms: float = 0.0
    stages: dict[str, Any] = field(default_factory=dict)


def run_query(question: str) -> QueryResponse:
    """Execute the full Planner -> Executor -> Critic multi-agent workflow."""
    start_time = time.perf_counter()
    trace_id = str(uuid.uuid4())
    stages: dict[str, Any] = {}

    logger.info("[%s] Beginning query workflow: %s", trace_id, question)

    # 1. PLANNER STAGE
    t0 = time.perf_counter()
    plan = planner.plan_query(question)
    stages["planner"] = {
        "latency_ms": (time.perf_counter() - t0) * 1000.0,
        "is_refusal": plan.is_refusal,
        "refusal_reason": plan.refusal_reason,
        "sql": plan.sql,
    }

    if plan.is_refusal:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        response = QueryResponse(
            trace_id=trace_id,
            question=question,
            answer=f"Query refused: {plan.refusal_reason}",
            is_refusal=True,
            refusal_reason=plan.refusal_reason,
            confidence=1.0,
            latency_ms=latency_ms,
            stages=stages,
        )
        _persist_trace(response)
        return response

    # 2. EXECUTOR STAGE (with max 1 retry on SQL failure)
    t0 = time.perf_counter()
    # The planner contract: a non-refusal plan always carries SQL.
    assert plan.sql is not None, "non-refusal plan must carry SQL"
    exec_result = executor.execute_sql(plan.sql)
    stages["executor"] = {
        "latency_ms": (time.perf_counter() - t0) * 1000.0,
        "success": exec_result.success,
        "row_count": exec_result.row_count,
        "sql_executed": exec_result.sql_executed,
        "error": exec_result.error,
    }

    # Bounded retry if SQL execution failed
    if not exec_result.success:
        logger.warning("[%s] SQL execution failed, retrying once...", trace_id)
        # Attempt fallback plan with error feedback
        retry_prompt = (
            f"The previous SQL failed with: {exec_result.error}. "
            f"Generate corrected DuckDB SQL for: {question}"
        )
        plan_retry = planner.plan_query(retry_prompt)
        # Only retry execution if we got valid non-refusal SQL back
        if not plan_retry.is_refusal and plan_retry.sql:
            exec_result = executor.execute_sql(plan_retry.sql)
            stages["executor_retry"] = {
                "success": exec_result.success,
                "error": exec_result.error,
                "sql": exec_result.sql_executed,
            }
        else:
            logger.warning(
                "[%s] Retry planner refused or returned no SQL: %s",
                trace_id,
                plan_retry.refusal_reason,
            )

    if not exec_result.success:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        response = QueryResponse(
            trace_id=trace_id,
            question=question,
            answer=f"Could not execute query in warehouse: {exec_result.error}",
            is_refusal=True,
            refusal_reason=exec_result.error,
            sql=exec_result.sql_executed,
            latency_ms=latency_ms,
            stages=stages,
        )
        _persist_trace(response)
        return response

    # 3. CRITIC STAGE
    t0 = time.perf_counter()
    review = critic.review_and_synthesize(question, exec_result.rows, exec_result.sql_executed)
    stages["critic"] = {
        "latency_ms": (time.perf_counter() - t0) * 1000.0,
        "is_faithful": review.is_faithful,
        "critique": review.critique,
    }

    total_latency_ms = (time.perf_counter() - start_time) * 1000.0

    response = QueryResponse(
        trace_id=trace_id,
        question=question,
        answer=review.answer,
        is_refusal=False,
        sql=exec_result.sql_executed,
        rows=exec_result.rows[:20],  # sample preview for response
        row_count=exec_result.row_count,
        citations=review.citations,
        confidence=1.0 if review.is_faithful else 0.8,
        latency_ms=total_latency_ms,
        stages=stages,
    )

    _persist_trace(response)
    return response


def _persist_trace(response: QueryResponse) -> None:
    """Write the full JSON execution trace to traces/{trace_id}.json."""
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    trace_path = TRACES_DIR / f"{response.trace_id}.json"
    try:
        data = asdict(response)
        trace_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.info("[%s] Persisted trace to %s", response.trace_id, trace_path)
    except Exception as exc:
        logger.error("Failed to persist trace %s: %s", response.trace_id, exc)
