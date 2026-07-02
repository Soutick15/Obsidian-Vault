"""
Observability module — metrics, structured logging, trace context.

TODOs:
  1. Add Prometheus counters for request_count, error_count, latency_histogram
  2. Add structured JSON logging with request_id
  3. (Optional) Add OpenTelemetry trace_id propagation

Run in mock mode: python -c "from capstone.devops.starter.observability import record_request; print('OK')"
"""
import logging
import json
import os
import time
import uuid
from typing import Optional

MOCK_MODE = os.getenv("LLM_PROVIDER", "mock") == "mock"

# --- Prometheus metrics (optional dep) ---
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    _PROMETHEUS_AVAILABLE = True
    REQUEST_COUNT = Counter("acme_hr_requests_total", "Total requests", ["endpoint", "status"])
    REQUEST_LATENCY = Histogram("acme_hr_request_latency_seconds", "Request latency", ["endpoint"])
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    REQUEST_COUNT = None
    REQUEST_LATENCY = None

# Structured logger
logger = logging.getLogger("acme_hr.observability")

def _json_log(level: str, message: str, **kwargs):
    record = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "level": level, "message": message, **kwargs}
    print(json.dumps(record))

def record_request(endpoint: str, status: int, latency_s: float, request_id: Optional[str] = None):
    """
    Record a request in metrics and structured log.

    TODO: Increment Prometheus counters if available.
    TODO: Add request_id to log record.
    """
    rid = request_id or str(uuid.uuid4())[:8]
    _json_log("INFO", f"Request recorded", endpoint=endpoint, status=status, latency_s=round(latency_s, 4), request_id=rid)
    if _PROMETHEUS_AVAILABLE and REQUEST_COUNT:
        REQUEST_COUNT.labels(endpoint=endpoint, status=str(status)).inc()
        if REQUEST_LATENCY:
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency_s)

def get_metrics_text() -> str:
    """
    Return Prometheus metrics in text format.

    TODO: Return generate_latest() output if prometheus_client available.
    TODO: Fall back to plain-text counters if not.
    """
    if _PROMETHEUS_AVAILABLE:
        from prometheus_client import generate_latest
        return generate_latest().decode("utf-8")
    return "# prometheus_client not installed — install with: pip install prometheus-client\n"

def new_trace_id() -> str:
    """Return a new trace ID (UUID4 hex)."""
    return uuid.uuid4().hex

if __name__ == "__main__":
    record_request("/health", 200, 0.001)
    print(get_metrics_text()[:200])
    print("observability OK")
