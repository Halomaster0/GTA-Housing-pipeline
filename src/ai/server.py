#!/usr/bin/env python3
"""Run FastAPI server (port 8000) for GTA Housing query pipeline."""

import uvicorn

from src.ai.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
