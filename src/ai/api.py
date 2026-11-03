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
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.ai.graph import run_query

logger = logging.getLogger(__name__)

# Comma-separated origins allowed to call the API from a browser (the static site).
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o.strip()
]

app = FastAPI(title="GTA Housing Query API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


class AskRequest(BaseModel):
    # Bounded so one request cannot push a large prompt through a paid model.
    question: str = Field(max_length=500)


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
def health() -> dict[str, str]:
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
