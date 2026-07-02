"""
Day 14 Lab — FastAPI HR Assistant (starter.py)
===============================================
Fill in every # TODO to complete the lab.
Run the self-test when done:
    python labs/developer/day-14/solution.py --selftest

Provider flexibility:
  - Set LLM_PROVIDER=mock (default)  -> no API key needed
  - Set LLM_PROVIDER=anthropic       -> needs ANTHROPIC_API_KEY
  - Set LLM_PROVIDER=openai          -> needs OPENAI_API_KEY
"""

import asyncio
import json
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

load_dotenv()

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------
APP_API_KEY = os.getenv("APP_API_KEY", "changeme")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")  # mock | anthropic | openai
CORPUS_DIR = os.getenv("CORPUS_DIR", "data/hr-corpus")
APP_VERSION = os.getenv("APP_VERSION", "dev")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "10"))
RATE_WINDOW = 60.0  # seconds

# ---------------------------------------------------------------------------
# TODO 1: Define Pydantic request and response models
#   - ChatRequest: field `question` (str, min_length=1, max_length=2000)
#                  field `session_id` (str | None, default None)
#   - HealthResponse: field `status` (str), `version` (str)
# ---------------------------------------------------------------------------

# TODO 2: Implement in-memory rate limiter
#   - Use a dict mapping client_id -> list of timestamps
#   - Drop timestamps older than RATE_WINDOW
#   - Raise HTTP 429 if count >= RATE_LIMIT
#   Function signature: def check_rate_limit(client_id: str) -> None

# TODO 3: Implement bearer-token auth
#   - Use HTTPBearer()
#   - Compare creds.credentials to APP_API_KEY
#   - Raise HTTP 401 if mismatch
#   Function signature: def verify_api_key(creds: HTTPAuthorizationCredentials) -> None

# ---------------------------------------------------------------------------
# Mock LLM — runs without any API key
# ---------------------------------------------------------------------------
MOCK_RESPONSES = {
    "pto": "According to HR policy, employees receive 15 PTO days per year after 1 year of service, increasing to 20 days after 3 years.",
    "benefits": "The company offers health, dental, and vision insurance. Full details are in the Benefits Guide.",
    "salary": "Salary reviews occur annually in Q1. Contact HR for compensation band information.",
    "default": "Thank you for your question. Please consult the HR portal or contact hr@acme.example for detailed information.",
}


def mock_llm_stream(question: str):
    """Yield answer tokens word-by-word (deterministic, no API key)."""
    q_lower = question.lower()
    for key, response in MOCK_RESPONSES.items():
        if key in q_lower:
            answer = response
            break
    else:
        answer = MOCK_RESPONSES["default"]
    for word in answer.split():
        yield word + " "


# TODO 4: Implement `llm_stream(question: str)` that dispatches to:
#   - mock_llm_stream if LLM_PROVIDER == "mock"
#   - Anthropic streaming if LLM_PROVIDER == "anthropic" (model: claude-haiku-4-5)
#   - OpenAI streaming if LLM_PROVIDER == "openai" (model: gpt-5-mini)
#   Each path should yield string chunks.
#   Hint: check os.getenv("ANTHROPIC_API_KEY") / os.getenv("OPENAI_API_KEY") before calling real APIs.

# ---------------------------------------------------------------------------
# TODO 5: Implement the async SSE generator
#   Function: async def token_generator(question: str) -> AsyncGenerator[str, None]
#   - Call llm_stream(question) for each chunk
#   - Yield SSE-formatted lines: f'data: {json.dumps({"chunk": chunk})}\n\n'
#   - After all chunks, yield 'data: [DONE]\n\n'
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# TODO 6: Create the FastAPI app with a lifespan context manager
#   - In startup: print a ready message (optionally load vector index onto app.state)
#   - Store app in variable `app`
# ---------------------------------------------------------------------------

# TODO 7: Implement GET /health
#   - No auth required
#   - Returns HealthResponse(status="ok", version=APP_VERSION)

# TODO 8: Implement POST /chat
#   - Requires verify_api_key dependency
#   - Calls check_rate_limit(request.client.host)
#   - Returns StreamingResponse(token_generator(req.question), media_type="text/event-stream")
