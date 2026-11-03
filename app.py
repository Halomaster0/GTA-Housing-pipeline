"""Vercel entrypoint for the query API. The app itself lives in src/ai/api.py."""

from src.ai.api import app

__all__ = ["app"]
