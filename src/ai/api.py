"""FastAPI server wrapping the GTA Housing multi-agent query graph.

Endpoints:
  POST /ask  — Run planner → executor → critic pipeline
  GET  /health — Health check

Run locally:
    pip install fastapi uvicorn httpx python-dotenv duckdb
    uv run uvicorn src.ai.api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.ai.graph import run_query

logger = logging.getLogger(__name__)

app = FastAPI(title="GTA Housing Query API", version="0.1.0")


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    trace_id: str
    question: str
    answer: str
    is_refusal: bool
    refusal_reason: str | None = None
    sql: str | None = None
    rows: list[dict[str, Any]] = []
    row_count: int = 0
    citations: list[str] = []
    confidence: float = 1.0
    latency_ms: float = 0.0
    stages: dict[str, Any] = {}


@app.get("/health")
def health():
    return {"status": "ok", "service": "gta-housing-query-api"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question required")
    response: Any = run_query(req.question)
    return AskResponse(
        trace_id=response.trace_id,
        question=response.question,
        answer=response.answer,
        is_refusal=response.is_refusal,
        refusal_reason=response.refusal_reason,
        sql=response.sql,
        rows=response.rows,
        row_count=response.row_count,
        citations=response.citations,
        confidence=response.confidence,
        latency_ms=response.latency_ms,
        stages=response.stages,
    )
