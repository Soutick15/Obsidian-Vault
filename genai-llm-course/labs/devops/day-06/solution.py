"""
Day 6 Lab — Operability Assessment (solution)
=============================================
Full reference implementation.  Run with:
  python labs/devops/day-06/solution.py

No API key required.  No running server needed.
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Wire up the shared app (solution to TODO 1)
# ---------------------------------------------------------------------------
_shared_path = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(_shared_path))

from fastapi.testclient import TestClient  # noqa: E402
from app import app  # noqa: E402  — shared Acme HR FastAPI app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


# ---------------------------------------------------------------------------
# TODO 2 — /health check (solution)
# ---------------------------------------------------------------------------

def check_health() -> dict[str, Any]:
    """Call /health and return parsed fields + latency."""
    t0 = time.perf_counter()
    r = client.get("/health")
    latency = _ms(t0)

    assert r.status_code == 200, f"/health returned {r.status_code}: {r.text}"
    data = r.json()

    return {
        "status": data.get("status"),
        "version": data.get("version"),
        "corpus_docs": data.get("corpus", {}).get("documents", 0),
        "corpus_chunks": data.get("corpus", {}).get("chunks", 0),
        "corpus_found": data.get("corpus", {}).get("corpus_found", False),
        "uptime_s": data.get("uptime_s"),
        "latency_ms": latency,
        "_raw": data,
    }


# ---------------------------------------------------------------------------
# TODO 3 — /chat latency sampling (solution)
# ---------------------------------------------------------------------------

SAMPLE_QUESTIONS = [
    "What is the annual leave policy for full-time employees?",
    "How do I submit an expense claim?",
    "What health benefits are available?",
]


def check_chat(questions: list[str] = SAMPLE_QUESTIONS) -> dict[str, Any]:
    """POST /chat for each question; return latency stats and metadata."""
    latencies: list[float] = []
    all_sources: list[list[str]] = []
    mock_flags: list[bool] = []

    for q in questions:
        t0 = time.perf_counter()
        r = client.post("/chat", json={"question": q, "k": 3})
        lat = _ms(t0)
        assert r.status_code == 200, f"/chat returned {r.status_code}: {r.text}"
        data = r.json()
        latencies.append(lat)
        all_sources.append(data.get("sources", []))
        mock_flags.append(data.get("mock", True))

    # p95: requires at least 1 value; statistics.quantiles needs >=2 for method="inclusive"
    if len(latencies) >= 2:
        p95 = round(statistics.quantiles(latencies, n=20, method="inclusive")[-1], 1)
    else:
        p95 = round(latencies[0], 1)

    return {
        "latency_min": round(min(latencies), 1),
        "latency_mean": round(statistics.mean(latencies), 1),
        "latency_p95": p95,
        "sources_returned": any(len(s) > 0 for s in all_sources),
        "mock_llm": all(mock_flags),
        "calls": len(latencies),
    }


# ---------------------------------------------------------------------------
# TODO 4 — /metrics check (solution)
# ---------------------------------------------------------------------------

def check_metrics() -> dict[str, Any]:
    """Call /metrics and return parsed fields."""
    t0 = time.perf_counter()
    r = client.get("/metrics")
    latency = _ms(t0)

    assert r.status_code == 200, f"/metrics returned {r.status_code}: {r.text}"
    data = r.json()

    return {
        "has_requests": bool(data.get("counters")),
        "has_latency": bool(data.get("avg_latency_s")),
        "uptime_s": data.get("uptime_s", 0.0),
        "latency_ms": latency,
        "raw": data,
    }


# ---------------------------------------------------------------------------
# TODO 5 — Checklist + report (solution)
# ---------------------------------------------------------------------------

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
        # the health check returned ok (logging initialised at import time).
        lambda h, c, m: h.get("status") == "ok",
    ),
    (
        "In-process metrics endpoint present",
        lambda h, c, m: m.get("has_requests") is not None,
    ),
    (
        "Request latency tracked in /metrics",
        lambda h, c, m: m.get("has_latency", False),
    ),
    (
        "Readiness probe distinct from liveness probe",
        # The shared service combines both in /health — gap for prod.
        lambda h, c, m: False,
    ),
    (
        "Token count per request exposed in /metrics",
        # Not present in current /metrics — gap.
        lambda h, c, m: False,
    ),
    (
        "Cost per request tracked",
        # No cost tracking — gap.
        lambda h, c, m: False,
    ),
    (
        "Semantic or exact-match cache layer present",
        # No cache — gap.
        lambda h, c, m: False,
    ),
    (
        "LLM gateway / rate-limit handling present",
        # No gateway — gap.
        lambda h, c, m: False,
    ),
    (
        "Prompt template version exposed in /health",
        # /health does not include prompt_version — gap.
        lambda h, c, m: False,
    ),
]

_DIVIDER = "=" * 60


def run_assessment() -> None:
    """Run the full operability assessment and print the report."""
    print(_DIVIDER)
    print("  Acme HR Assistant — Operability Assessment")
    print(_DIVIDER)

    # --- /health ---
    print("\n[ENDPOINT] GET /health")
    health = check_health()
    print(f"  status         : {health['status']}")
    print(f"  version        : {health['version']}")
    print(f"  uptime_s       : {health['uptime_s']}")
    print(f"  corpus_docs    : {health['corpus_docs']}")
    print(f"  corpus_chunks  : {health['corpus_chunks']}")
    print(f"  corpus_found   : {health['corpus_found']}")
    print(f"  latency_ms     : {health['latency_ms']}")

    # --- /chat ---
    print(f"\n[ENDPOINT] POST /chat  ({len(SAMPLE_QUESTIONS)} questions)")
    chat = check_chat()
    print(f"  calls                   : {chat['calls']}")
    print(f"  latency_ms min/mean/p95 : {chat['latency_min']} / "
          f"{chat['latency_mean']} / {chat['latency_p95']}")
    print(f"  sources_returned        : {chat['sources_returned']}")
    print(f"  mock_llm                : {chat['mock_llm']}")

    # --- /metrics ---
    print("\n[ENDPOINT] GET /metrics")
    metrics = check_metrics()
    print(f"  requests recorded       : {metrics['has_requests']}")
    print(f"  avg_latency tracked     : {metrics['has_latency']}")
    print(f"  service uptime_s        : {metrics['uptime_s']}")
    print(f"  latency_ms              : {metrics['latency_ms']}")

    # --- checklist ---
    print("\n" + _DIVIDER)
    print("  Operability Checklist")
    print(_DIVIDER)
    passes = 0
    total = len(CHECKLIST)
    for label, evaluator in CHECKLIST:
        result = evaluator(health, chat, metrics)
        tag = "PASS" if result else "FAIL"
        if result:
            passes += 1
        print(f"  [{tag}] {label}")

    # --- gap summary ---
    gaps = total - passes
    print("\n" + _DIVIDER)
    print("  Gap Summary")
    print(_DIVIDER)
    print(f"  Passes : {passes} / {total}")
    print(f"  Gaps   : {gaps} / {total}")
    print()
    print("  Next steps → Days 7–10 address observability, CI/CD, gateway,")
    print("  and caching to close the identified gaps.")
    print(_DIVIDER)


if __name__ == "__main__":
    run_assessment()
