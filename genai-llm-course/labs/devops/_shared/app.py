"""
Acme HR Knowledge Assistant — FastAPI application.

Endpoints:
  GET  /health   — liveness + corpus stats
  POST /chat     — RAG-style Q&A over the HR corpus
  GET  /metrics  — lightweight in-process counters

Run locally:
  uvicorn labs.devops._shared.app:app --reload --port 8000

Or as a standalone script with self-test:
  python labs/devops/_shared/app.py --selftest
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from service import answer, corpus_info

# ---------------------------------------------------------------------------
# Configuration from environment variables
# ---------------------------------------------------------------------------
APP_VERSION = os.environ.get("APP_VERSION", "0.1.0")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
DEFAULT_K = int(os.environ.get("DEFAULT_K", "3"))

# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger("acme_hr_assistant")


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_JsonFormatter())
logger.handlers = [_handler]
logger.propagate = False

# ---------------------------------------------------------------------------
# In-process metrics counters
# ---------------------------------------------------------------------------
_counters: dict[str, int] = defaultdict(int)
_latencies: dict[str, list[float]] = defaultdict(list)
_start_time = time.time()


def _record(endpoint: str, latency_s: float) -> None:
    _counters[f"{endpoint}.requests"] += 1
    _latencies[endpoint].append(latency_s)


def _avg(vals: list[float]) -> float:
    return round(sum(vals) / len(vals), 4) if vals else 0.0


# ---------------------------------------------------------------------------
# Lifespan — log startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    info = corpus_info()
    logger.info(
        "Acme HR Assistant starting",
        extra={
            "version": APP_VERSION,
            "corpus_docs": info["documents"],
            "corpus_chunks": info["chunks"],
        },
    )
    yield
    logger.info("Acme HR Assistant shutting down")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Acme HR Knowledge Assistant",
    description=(
        "RAG-style HR Q&A service for Acme Corp. "
        "Runs with no API key (mock LLM by default). "
        "Intended as the shared system-under-operation for DevOps labs."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="HR question")
    k: int = Field(default=DEFAULT_K, ge=1, le=10, description="Number of context chunks to retrieve")


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    contexts: list[str]
    mock: bool = Field(description="True when the mock LLM generator was used")
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_s: float
    corpus: dict[str, Any]


# ---------------------------------------------------------------------------
# Middleware — request logging + timing
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.perf_counter()
    response: Response = await call_next(request)
    latency = time.perf_counter() - t0
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "latency_ms": round(latency * 1000, 2),
        },
    )
    return response


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["ops"])
async def health() -> HealthResponse:
    """Liveness + readiness check. Returns corpus stats and uptime."""
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        uptime_s=round(time.time() - _start_time, 1),
        corpus=corpus_info(),
    )


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(req: ChatRequest) -> ChatResponse:
    """Answer an HR question using lexical retrieval over the corpus."""
    t0 = time.perf_counter()
    logger.info("chat request", extra={"question_len": len(req.question), "k": req.k})

    result = answer(req.question, k=req.k)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    _record("/chat", latency_ms / 1000)

    logger.info(
        "chat response",
        extra={
            "sources": result["sources"],
            "mock": result["mock"],
            "latency_ms": latency_ms,
        },
    )
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        contexts=result["contexts"],
        mock=result["mock"],
        latency_ms=latency_ms,
    )


@app.get("/metrics", tags=["ops"])
async def metrics() -> JSONResponse:
    """
    Lightweight in-process request counters.
    Replace with Prometheus /metrics in observability labs.
    """
    data: dict[str, Any] = {
        "uptime_s": round(time.time() - _start_time, 1),
        "version": APP_VERSION,
        "counters": dict(_counters),
        "avg_latency_s": {k: _avg(v) for k, v in _latencies.items()},
    }
    return JSONResponse(content=data)


# ---------------------------------------------------------------------------
# Self-test — runs in-process, no server required, no credentials needed
# ---------------------------------------------------------------------------
def run_selftest() -> None:
    """
    Validate /health and /chat using FastAPI's TestClient.
    Exits 0 on success, 1 on failure.
    """
    from fastapi.testclient import TestClient

    print("[selftest] Starting Acme HR Assistant self-test...")
    client = TestClient(app)

    # --- /health ---
    r = client.get("/health")
    assert r.status_code == 200, f"/health returned {r.status_code}"
    health_data = r.json()
    assert health_data["status"] == "ok", f"unexpected status: {health_data['status']}"
    assert health_data["corpus"]["corpus_found"], (
        "Corpus not found — check data/hr-corpus/ exists relative to repo root"
    )
    print(f"[selftest] /health OK  — corpus docs={health_data['corpus']['documents']}, "
          f"chunks={health_data['corpus']['chunks']}")

    # --- /chat ---
    payload = {"question": "What is the annual leave policy for full-time employees?", "k": 3}
    r = client.post("/chat", json=payload)
    assert r.status_code == 200, f"/chat returned {r.status_code}: {r.text}"
    chat_data = r.json()
    assert chat_data["answer"], "Empty answer returned"
    assert chat_data["sources"], "No sources returned"
    assert len(chat_data["contexts"]) > 0, "No context chunks returned"
    print(f"[selftest] /chat  OK  — sources={chat_data['sources']}, mock={chat_data['mock']}")
    print(f"[selftest]             answer[:120]: {chat_data['answer'][:120]!r}")

    # --- /metrics ---
    r = client.get("/metrics")
    assert r.status_code == 200, f"/metrics returned {r.status_code}"
    print("[selftest] /metrics OK")

    print("[selftest] ALL CHECKS PASSED — exit 0")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if "--selftest" in sys.argv:
        run_selftest()
    else:
        uvicorn.run("app:app", host=HOST, port=PORT, log_level=LOG_LEVEL.lower())
