"""
Day 14 Lab — FastAPI HR Assistant (solution.py)
===============================================
Complete working implementation.

Usage:
    # Self-test (no server, no API key):
    python labs/developer/day-14/solution.py --selftest

    # Start server:
    uvicorn labs.developer.day_14.solution:app --reload --port 8000

Provider flexibility (set via env):
    LLM_PROVIDER=mock        (default — no key needed)
    LLM_PROVIDER=anthropic   (needs ANTHROPIC_API_KEY)
    LLM_PROVIDER=openai      (needs OPENAI_API_KEY)
"""

import json
import os
import sys
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
APP_API_KEY = os.getenv("APP_API_KEY", "changeme")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
CORPUS_DIR = os.getenv("CORPUS_DIR", "data/hr-corpus")
APP_VERSION = os.getenv("APP_VERSION", "dev")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "10"))
RATE_WINDOW = 60.0


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question for the HR assistant",
    )
    session_id: str | None = Field(None, description="Optional session identifier")


class HealthResponse(BaseModel):
    status: str
    version: str
    provider: str


# ---------------------------------------------------------------------------
# Rate limiter (in-memory, single-process)
# ---------------------------------------------------------------------------
_request_log: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(client_id: str) -> None:
    now = time.time()
    window = [t for t in _request_log[client_id] if now - t < RATE_WINDOW]
    _request_log[client_id] = window
    if len(window) >= RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit: {RATE_LIMIT} requests per {int(RATE_WINDOW)}s",
        )
    _request_log[client_id].append(now)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
_bearer = HTTPBearer()


def verify_api_key(
    creds: HTTPAuthorizationCredentials = Security(_bearer),
) -> None:
    if creds.credentials != APP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


# ---------------------------------------------------------------------------
# Mock LLM (no API key required)
# ---------------------------------------------------------------------------
_MOCK_RESPONSES = {
    "pto": "According to HR policy, employees receive 15 PTO days per year after 1 year of service, increasing to 20 days after 3 years of service.",
    "vacation": "Vacation days accrue at 1.25 days per month. Unused days roll over up to a maximum of 30 days.",
    "benefits": "The company offers health, dental, and vision insurance. Enrollment is open during your first 30 days and each November.",
    "salary": "Salary reviews occur annually in Q1. Contact HR for your compensation band and grade information.",
    "remote": "Remote work is permitted up to 3 days per week for eligible roles. Manager approval required.",
    "default": "Thank you for your HR question. Please consult the HR portal at hr.acme.example or contact hr@acme.example for detailed information.",
}


def _mock_stream(question: str):
    """Yield answer tokens word-by-word — deterministic, no API key."""
    q = question.lower()
    answer = _MOCK_RESPONSES["default"]
    for key, resp in _MOCK_RESPONSES.items():
        if key in q:
            answer = resp
            break
    for word in answer.split():
        yield word + " "


def _anthropic_stream(question: str):
    """Stream from Anthropic claude-haiku-4-5."""
    import anthropic  # type: ignore

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-haiku-4-5",
        max_tokens=512,
        system="You are a concise HR assistant. Answer using only provided HR policy.",
        messages=[{"role": "user", "content": question}],
    ) as stream:
        for text in stream.text_stream:
            yield text


def _openai_stream(question: str):
    """Stream from OpenAI gpt-5-mini."""
    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-5-mini",
        max_tokens=512,
        stream=True,
        messages=[
            {"role": "system", "content": "You are a concise HR assistant."},
            {"role": "user", "content": question},
        ],
    )
    for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


def llm_stream(question: str):
    """Dispatch to the correct LLM backend based on LLM_PROVIDER env var."""
    if LLM_PROVIDER == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
        yield from _anthropic_stream(question)
    elif LLM_PROVIDER == "openai" and os.getenv("OPENAI_API_KEY"):
        yield from _openai_stream(question)
    else:
        yield from _mock_stream(question)


# ---------------------------------------------------------------------------
# SSE generator
# ---------------------------------------------------------------------------
async def token_generator(question: str) -> AsyncGenerator[str, None]:
    """Wrap llm_stream as an async SSE generator."""
    for chunk in llm_stream(question):
        payload = json.dumps({"chunk": chunk})
        yield f"data: {payload}\n\n"
    yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI):
    print(
        f"[startup] HR Assistant API ready — provider={LLM_PROVIDER} version={APP_VERSION}"
    )
    yield
    print("[shutdown] HR Assistant API stopped.")


app = FastAPI(
    title="HR Knowledge Assistant API",
    description="Streaming LLM-powered HR Q&A service (Day 14 lab).",
    version=APP_VERSION,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    """Liveness check — no auth required."""
    return HealthResponse(status="ok", version=APP_VERSION, provider=LLM_PROVIDER)


@app.post("/chat", tags=["chat"])
async def chat(
    req: ChatRequest,
    request: Request,
    _auth: None = Depends(verify_api_key),
) -> StreamingResponse:
    """
    Stream an LLM answer to an HR question as SSE.

    Authorization header: `Bearer <APP_API_KEY>`
    """
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)
    return StreamingResponse(
        token_generator(req.question),
        media_type="text/event-stream",
    )


# ---------------------------------------------------------------------------
# Self-test (uses FastAPI TestClient — no server needed)
# ---------------------------------------------------------------------------
def _run_selftest() -> None:
    from fastapi.testclient import TestClient  # starlette, bundled with fastapi

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {APP_API_KEY}"}

    print("[selftest] GET /health ...", end=" ")
    r = client.get("/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["status"] == "ok", f"status field wrong: {data}"
    print(f"OK -> {data}")

    print("[selftest] POST /chat  ...", end=" ")
    with client.stream(
        "POST",
        "/chat",
        headers=headers,
        json={"question": "What is the PTO policy?"},
    ) as r:
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        chunks = []
        for line in r.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                payload = json.loads(line[6:])
                chunks.append(payload.get("chunk", ""))
        assert chunks, "No SSE chunks received"
    print(f"OK -> received {len(chunks)} chunks")

    print("[selftest] POST /chat  without auth ...", end=" ")
    r2 = client.post("/chat", json={"question": "test"})
    assert r2.status_code in (401, 403), (
        f"Expected 401/403 (no bearer), got {r2.status_code}"
    )
    print(f"OK -> {r2.status_code} as expected")

    print("[selftest] POST /chat  empty question ...", end=" ")
    r3 = client.post("/chat", headers=headers, json={"question": ""})
    assert r3.status_code == 422, f"Expected 422, got {r3.status_code}"
    print(f"OK -> 422 as expected")

    print("\n[selftest] PASSED")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _run_selftest()
    else:
        import uvicorn

        uvicorn.run(
            "labs.developer.day_14.solution:app", host="0.0.0.0", port=8000, reload=True
        )
