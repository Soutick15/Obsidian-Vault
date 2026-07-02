"""
Day 11 Lab — LLM Observability: Prometheus Metrics & Structured Traces
======================================================================
Starter file — complete each TODO block.

Run with:
    python starter.py

No API key required.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import secrets
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

# ── Shared service import ───────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
from app import app  # FastAPI app  # noqa: E402
from service import answer  # noqa: E402

from fastapi import Response
from fastapi.testclient import TestClient

# ── Structured JSON logging setup ──────────────────────────────────────────

class _JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%f"),
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        # Attach any extra keys the caller passed in
        for key, val in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info",
                "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "message",
                "asctime", "taskName",
            }:
                payload[key] = val
        return json.dumps(payload)


_handler = logging.StreamHandler()
_handler.setFormatter(_JSONFormatter())
logger = logging.getLogger("day11")
logger.setLevel(logging.INFO)
logger.addHandler(_handler)
logger.propagate = False


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1 — MetricsRegistry
# ═══════════════════════════════════════════════════════════════════════════
# Implement a hand-rolled Prometheus-compatible metrics registry.
#
# Requirements:
#   class MetricsRegistry:
#       def counter(self, name, help_text, label_names=()) -> _Counter
#       def histogram(self, name, help_text, label_names=(), buckets=(...)) -> _Histogram
#       def format_prometheus(self) -> str
#           Returns valid Prometheus text format for ALL registered metrics.
#
# _Counter:
#   def inc(self, label_values=(), amount=1) -> None
#
# _Histogram:
#   def observe(self, label_values=(), value=0.0) -> None
#   Stores bucket counts (le=...), _sum, _count per label combination.
#
# Prometheus text format reminder:
#   # HELP <name> <help text>
#   # TYPE <name> <counter|histogram>
#   <name>{label="value",...} <number>
#
# For histograms emit _bucket, _sum, _count lines.
# ────────────────────────────────────────────────────────────────────────────

# TODO: implement MetricsRegistry, _Counter, _Histogram here
class MetricsRegistry:
    pass  # Replace with your implementation


# ═══════════════════════════════════════════════════════════════════════════
# TODO 2 — Register metrics
# ═══════════════════════════════════════════════════════════════════════════
# Create a global registry and register these five metrics:
#
#   llm_requests_total        counter   labels: endpoint, status
#   llm_errors_total          counter   labels: endpoint, error_type
#   llm_request_duration_seconds  histogram  buckets: [0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
#   llm_tokens_total          counter   labels: type
#   llm_cost_usd_total        counter   (no labels)
# ────────────────────────────────────────────────────────────────────────────

registry = MetricsRegistry()
# TODO: register your metrics here
# requests_counter = registry.counter(...)
# errors_counter   = registry.counter(...)
# latency_hist     = registry.histogram(...)
# tokens_counter   = registry.counter(...)
# cost_counter     = registry.counter(...)


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3 — TraceLogger
# ═══════════════════════════════════════════════════════════════════════════
# Implement a lightweight per-request trace recorder.
#
# class TraceLogger:
#   def __init__(self):
#       self.trace_id = <random 8-char hex string>
#       self._spans = []
#       self._span_starts = {}
#
#   def start_span(self, name: str) -> None
#       Record start time for this span name.
#
#   def end_span(self, name: str, **attrs) -> None
#       Compute duration_ms; append span dict to self._spans.
#       Span dict: {"name": name, "duration_ms": ..., **attrs}
#       Also emit a structured log line via logger with trace_id attached.
#
#   def to_dict(self) -> dict
#       Return {"trace_id": self.trace_id, "spans": self._spans}
# ────────────────────────────────────────────────────────────────────────────

class TraceLogger:
    pass  # Replace with your implementation


# ═══════════════════════════════════════════════════════════════════════════
# TODO 4 — Instrumented chat handler
# ═══════════════════════════════════════════════════════════════════════════
# Write a function:
#
#   def instrumented_chat(client: TestClient, question: str, k: int = 3)
#       -> tuple[dict, dict]:
#
# Steps:
#   1. Create a TraceLogger; start root span "root"
#   2. Start span "retrieve"; call answer() and time *just* the retrieval
#      portion — since answer() does both, you can simulate span timing by
#      measuring the full call and attributing 20% to retrieve, 80% to generate.
#      (In a real split pipeline you'd time each independently.)
#   3. POST to /chat via client; capture response JSON
#   4. End spans with appropriate attributes:
#        retrieve: k=k, top_score=round(random.uniform(0.7, 0.98), 3)
#        generate: model="mock", in_tokens=<estimate>, out_tokens=<estimate>, cost_usd=0.0
#      Estimate tokens: in_tokens = len(question.split()) * 4 + 200
#                       out_tokens = len(response["answer"].split()) * 4 // 3
#   5. End root span with status="success" or "error"
#   6. Record all metrics (requests, latency, tokens, cost)
#   7. Return (response_json, trace.to_dict())
# ────────────────────────────────────────────────────────────────────────────

def instrumented_chat(client: TestClient, question: str, k: int = 3) -> tuple[dict, dict]:
    # TODO: implement
    raise NotImplementedError("Complete TODO 4")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 5 — /metrics-prom endpoint
# ═══════════════════════════════════════════════════════════════════════════
# Add a route to the FastAPI app that returns the Prometheus text format.
#
# @app.get("/metrics-prom", tags=["ops"])
# async def prometheus_metrics():
#     text = registry.format_prometheus()
#     return Response(content=text, media_type="text/plain; version=0.0.4")
# ────────────────────────────────────────────────────────────────────────────

# TODO: add the route here


# ═══════════════════════════════════════════════════════════════════════════
# TODO 6 — Load workload + summary
# ═══════════════════════════════════════════════════════════════════════════
# Implement run_load_and_report():
#   1. Create a TestClient for the app
#   2. Fire 20 diverse HR questions (use the QUESTIONS list below)
#   3. Collect all traces; count successes and errors
#   4. Fetch /metrics and parse the text to print a summary:
#        - llm_requests_total for each status label
#        - p50 and p99 from the latency histogram (approximate from buckets)
#        - llm_tokens_total for input and output
#        - llm_cost_usd_total
#   5. Print one sample trace in readable format
# ────────────────────────────────────────────────────────────────────────────

QUESTIONS = [
    "How many days of annual leave do I get?",
    "What is the parental leave policy?",
    "How do I submit an expense report?",
    "When is the performance review cycle?",
    "What health insurance plans are available?",
    "Can I work from home permanently?",
    "How do I request a salary advance?",
    "What is the overtime policy?",
    "How do I enroll in the 401k plan?",
    "What is the bereavement leave policy?",
    "How do I report a workplace safety issue?",
    "What are the company's core working hours?",
    "Can I carry over unused vacation days?",
    "How do I request a leave of absence?",
    "What is the tuition reimbursement limit?",
    "How do I update my emergency contact?",
    "What is the employee referral bonus?",
    "How do I access the employee assistance programme?",
    "What is the policy on side projects?",
    "How do I apply for an internal transfer?",
]


def run_load_and_report() -> None:
    # TODO: implement
    raise NotImplementedError("Complete TODO 6")


# ── Entrypoint ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Day 11 Lab — LLM Observability (starter)\n")
    run_load_and_report()
