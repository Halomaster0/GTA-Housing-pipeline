"""Executor agent: validates, sanitizes, and runs read-only SQL queries against DuckDB."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

import duckdb

from src.common import config

logger = logging.getLogger(__name__)

FORBIDDEN_SQL_PATTERNS = [
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)\b",
    r"\b(ATTACH|DETACH|COPY|PRAGMA|EXPORT|IMPORT)\b",
    r";.*\S",  # multiple statements separated by semicolon
]


@dataclass
class ExecutionResult:
    success: bool
    rows: list[dict[str, Any]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    sql_executed: str = ""
    error: str | None = None


def validate_sql(sql: str) -> tuple[bool, str | None]:
    """Check that SQL is strictly a single, read-only SELECT statement."""
    cleaned = sql.strip().rstrip(";")
    upper = cleaned.upper()

    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return False, "Query must start with SELECT or WITH."

    for pattern in FORBIDDEN_SQL_PATTERNS:
        if re.search(pattern, upper):
            return False, f"Forbidden SQL token or pattern detected: {pattern}"

    return True, None


def execute_sql(sql: str, max_rows: int = 100) -> ExecutionResult:
    """Execute a sanitized read-only SQL query against the warehouse."""
    is_valid, error_msg = validate_sql(sql)
    if not is_valid:
        logger.error("SQL validation failed: %s", error_msg)
        return ExecutionResult(success=False, error=error_msg, sql_executed=sql)

    # Ensure limit is enforced
    cleaned_sql = sql.strip().rstrip(";")
    if "LIMIT" not in cleaned_sql.upper():
        exec_sql = f"{cleaned_sql} LIMIT {max_rows}"
    else:
        exec_sql = cleaned_sql

    start_time = time.perf_counter()
    try:
        con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
        try:
            rel = con.execute(exec_sql)
            columns = [desc[0] for desc in rel.description] if rel.description else []
            raw_rows = rel.fetchall()
            rows = [dict(zip(columns, row)) for row in raw_rows]
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return ExecutionResult(
                success=True,
                rows=rows,
                columns=columns,
                row_count=len(rows),
                execution_time_ms=elapsed_ms,
                sql_executed=exec_sql,
            )
        finally:
            con.close()
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.exception("DuckDB execution error: %s", exc)
        return ExecutionResult(
            success=False,
            execution_time_ms=elapsed_ms,
            sql_executed=exec_sql,
            error=str(exc),
        )

