"""LLM router and client for OpenRouter.

Routes to free models first. If free models are unavailable, rate-limited,
or timeout, falls back to the cheapest paid models.
"""

from __future__ import annotations

import logging
from typing import Any
import httpx

from src.common import config

logger = logging.getLogger(__name__)

# Free models to attempt in priority order
FREE_MODELS = [
    "dots-studio/dots-3-note-preview:free",
    "google/gemma-4-26b-a4b-it:free",
    "liquid/lfm-2.5-2.6b:free",
    "nvidia/nemotron-3.5-lightning:free",
]

# Lowest-cost paid models to fall back on
CHEAP_MODELS = [
    "mistralai/mistral-nemo",            # ~$0.03/M prompt, $0.03/M completion
    "meta-llama/llama-3.1-8b-instruct",  # ~$0.05/M prompt, $0.08/M completion
    "deepseek/deepseek-chat",            # ~$0.26/M prompt, $1.03/M completion
]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(Exception):
    """Raised when all models in the routing chain fail."""


def complete(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 1000,
    timeout: float = 12.0,
) -> dict[str, Any]:
    """Execute a chat completion routing through free models before paid fallbacks.

    Returns:
        dict with keys:
            content: str - text response
            model: str - model identifier that answered
            tier: str - 'free' or 'cheapest_paid'
            usage: dict - token counts and costs (if provided)
    """
    if not config.OPENROUTER_API_KEY:
        raise LLMError("OPENROUTER_API_KEY is not configured in .env")

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/Halomaster0/GTA-Housing-pipeline",
        "X-Title": "GTA Housing Pipeline",
        "Content-Type": "application/json",
    }

    # 1. Attempt free models first
    for model in FREE_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(OPENROUTER_URL, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    if not content:
                        logger.warning("Free model %s returned empty/null content; skipping.", model)
                        continue
                    actual_model = data.get("model", model)
                    logger.info("Successfully routed to free model: %s", actual_model)
                    return {
                        "content": content,
                        "model": actual_model,
                        "tier": "free",
                        "usage": data.get("usage", {}),
                    }
                logger.warning(
                    "Free model %s failed with status %d: %s",
                    model,
                    res.status_code,
                    res.text[:120],
                )
        except Exception as exc:
            logger.warning("Free model %s error: %s", model, exc)

    # 2. Fall back to cheapest paid models
    logger.info("Free tier exhausted or unavailable; routing to cheapest paid tier.")
    for model in CHEAP_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(OPENROUTER_URL, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    if not content:
                        logger.warning("Paid model %s returned empty/null content; skipping.", model)
                        continue
                    actual_model = data.get("model", model)
                    logger.info("Successfully routed to cheap paid model: %s", actual_model)
                    return {
                        "content": content,
                        "model": actual_model,
                        "tier": "cheapest_paid",
                        "usage": data.get("usage", {}),
                    }
                logger.warning(
                    "Paid model %s failed with status %d: %s",
                    model,
                    res.status_code,
                    res.text[:120],
                )
        except Exception as exc:
            logger.warning("Paid model %s error: %s", model, exc)

    raise LLMError("All model endpoints (free and cheapest paid) failed to respond.")

