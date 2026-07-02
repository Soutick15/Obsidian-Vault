"""
Day 6 Lab — Operability Assessment (starter)
=============================================
Goal: exercise the shared Acme HR Assistant and produce a structured
operability report against a production-readiness checklist.

No API key required.  No running server needed — we use FastAPI's
in-process TestClient.

Work through the five TODO blocks in order.
Run: python labs/devops/day-06/starter.py
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# TODO 1 — Wire up the shared app
# ---------------------------------------------------------------------------
# The shared FastAPI app lives at labs/devops/_shared/app.py.
# To import it from this file's location we need to add the _shared directory
# to sys.path so that `from app import app` resolves correctly.
#
# Hint: use pathlib.Path(__file__).resolve().parents[1] / "_shared"
# Then: from fastapi.testclient import TestClient
#       from app import app
#
# Replace the two "..." placeholders below.

_shared_path = ...  # Path to the _shared directory
sys.path.insert(0, str(_shared_path))

# from fastapi.testclient import TestClient
# from app import app

# client = TestClient(app)

# ---------------------------------------------------------------------------
# Helper: measure endpoint latency
# ---------------------------------------------------------------------------

def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


# ---------------------------------------------------------------------------
# TODO 2 — Call /health and extract fields
# ---------------------------------------------------------------------------
# Call GET /health with the TestClient.
# Extract: status, version, corpus docs count, corpus chunks count.
# Also measure latency in ms.
#
# Return a dict with keys: status, version, corpus_docs, corpus_chunks,
#   corpus_found, latency_ms

def check_health() -> dict[str, Any]:
    """Call /health and return parsed fields + latency."""
    # TODO: implement this function
    # Hint: t0 = time.perf_counter(); r = client.get("/health"); latency = _ms(t0)
    raise NotImplementedError("TODO 2 — implement check_health()")


# ---------------------------------------------------------------------------
# TODO 3 — Call /chat with multiple questions and measure latency
# ---------------------------------------------------------------------------
# Send each question in `questions` as a POST /chat request.
# Collect per-call latency (ms). Return a summary dict with:
#   latency_min, latency_mean, latency_p95 (all in ms, rounded to 1 dp)
#   sources_returned: bool (True if at least one response had sources)
#   mock_llm: bool (True if all responses used mock=True)
#   calls: int

SAMPLE_QUESTIONS = [
    "What is the annual leave policy for full-time employees?",
    "How do I submit an expense claim?",
    "What health benefits are available?",
]


def check_chat(questions: list[str] = SAMPLE_QUESTIONS) -> dict[str, Any]:
    """POST /chat for each question; return latency stats and metadata."""
    # TODO: implement this function
    # Hint: iterate questions, record latency per call; use statistics.quantiles
    raise NotImplementedError("TODO 3 — implement check_chat()")


# ---------------------------------------------------------------------------
# TODO 4 — Call /metrics and parse counters
# ---------------------------------------------------------------------------
# Call GET /metrics.
# Return a dict with:
#   has_requests: bool   — True if 'counters' key exists and is non-empty
#   has_latency:  bool   — True if 'avg_latency_s' key exists and is non-empty
#   uptime_s:     float
#   raw:          dict   — the full metrics payload (for printing)

def check_metrics() -> dict[str, Any]:
    """Call /metrics and return parsed fields."""
    # TODO: implement this function
    raise NotImplementedError("TODO 4 — implement check_metrics()")


# ---------------------------------------------------------------------------
# TODO 5 — Evaluate checklist and print the operability report
# ---------------------------------------------------------------------------
# Use the results from check_health(), check_chat(), check_metrics() to
# evaluate each item in CHECKLIST.  Each item is a tuple:
#   (label: str, evaluator: callable -> bool)
# The evaluator receives (health_result, chat_result, metrics_result)
# and returns True (PASS) or False (FAIL).
#
# Print the report in the format shown in the README.

CHECKLIST: list[tuple[str, Any]] = [
    (
        "Liveness endpoint (/health) responds 200",
        lambda h, c, m: h.get("status") == "ok",
    ),
    (
        "Corpus loaded and non-empty",
        lambda h, c, m: h.get("corpus_found") and h.get("corpus_docs", 0) > 0,
    ),
    (
        "Structured JSON logging configured",
        # The shared app uses a JSON formatter; we treat this as present if
        # the app started without errors (health returned ok).
        lambda h, c, m: h.get("status") == "ok",
    ),
    (
        "In-process metrics endpoint present",
        lambda h, c, m: m.get("has_requests") is not None,
    ),
    (
        "Request latency tracked",
        lambda h, c, m: m.get("has_latency", False),
    ),
    (
        "Readiness probe distinct from liveness probe",
        # The shared service only has /health (combined); no /health/ready
        lambda h, c, m: False,  # gap — intentionally always fails for this lab
    ),
    (
        "Token count per request not in metrics",
        lambda h, c, m: False,  # gap
    ),
    (
        "Cost per request not tracked",
        lambda h, c, m: False,  # gap
    ),
    (
        "No semantic cache layer present",
        lambda h, c, m: False,  # gap
    ),
    (
        "No LLM gateway / rate-limit handling",
        lambda h, c, m: False,  # gap
    ),
    (
        "Prompt template version not exposed in /health",
        lambda h, c, m: False,  # gap
    ),
]


def run_assessment() -> None:
    """Run the full operability assessment and print the report."""
    print("=" * 60)
    print("  Acme HR Assistant — Operability Assessment")
    print("=" * 60)

    # --- collect results ---
    print("\n[ENDPOINT] GET /health")
    # TODO: call check_health() and print the fields
    # Hint: health = check_health(); then print each field
    raise NotImplementedError("TODO 5a — call check_health() and print results")

    print("\n[ENDPOINT] POST /chat")
    # TODO: call check_chat() and print the latency stats
    raise NotImplementedError("TODO 5b — call check_chat() and print results")

    print("\n[ENDPOINT] GET /metrics")
    # TODO: call check_metrics() and print the counters
    raise NotImplementedError("TODO 5c — call check_metrics() and print results")

    # --- checklist ---
    print("\n" + "=" * 60)
    print("  Operability Checklist")
    print("=" * 60)
    passes = 0
    # TODO: iterate CHECKLIST, evaluate each item, print PASS/FAIL
    # Hint: for label, evaluator in CHECKLIST:
    #           result = evaluator(health, chat, metrics)
    raise NotImplementedError("TODO 5d — evaluate checklist and print results")

    # --- gap summary ---
    print("\n" + "=" * 60)
    print("  Gap Summary")
    print("=" * 60)
    # TODO: print passes/total and gaps/total
    # TODO: print the "Next steps" line
    raise NotImplementedError("TODO 5e — print gap summary")


if __name__ == "__main__":
    run_assessment()
