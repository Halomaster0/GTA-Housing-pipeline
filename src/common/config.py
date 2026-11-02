"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Load local .env if present
load_dotenv(REPO_ROOT / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# /ask answers from the September build, the same figures the published Power BI
# report shows. The October warehouse (data/warehouse.duckdb) stays the transform
# target and the working source until the October Toronto data is validated.
DUCKDB_PATH = Path(os.getenv("DUCKDB_PATH", str(REPO_ROOT / "data" / "warehouse-sept.duckdb")))
LLM_DAILY_SPEND_CEILING_USD = float(os.getenv("LLM_DAILY_SPEND_CEILING_USD", "2.0"))
API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

