"""
Day 11 Lab — LLM Observability: Prometheus Metrics & Structured Traces
======================================================================
Complete reference solution.

Run with:
    python solution.py

No API key required.
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
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

# ── Structured JSON logging ─────────────────────────────────────────────────

class _JSONFormatter(logging.Formatter):
    """Emit each log record as a single compact JSON line."""

    _SKIP = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime", "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        for k, v in record.__dict__.items():
            if k not in self._SKIP:
                payload[k] = v
        return json.dumps(payload)


_handler = logging.StreamHandler()
_handler.setFormatter(_JSONFormatter())
logger = logging.getLogger("day11")
logger.setLevel(logging.INFO)
logger.addHandler(_handler)
logger.propagate = False


# ═══════════════════════════════════════════════════════════════════════════
# §1 — Hand-rolled Prometheus-compatible MetricsRegistry
# ═══════════════════════════════════════════════════════════════════════════

class _Counter:
    """Simple label-aware counter."""

    def __init__(self, name: str, help_text: str, label_names: tuple[str, ...]) -> None:
        self.name = name
        self.help_text = help_text
        self.label_names = label_names
        self._values: dict[tuple, float] = defaultdict(float)

    def inc(self, label_values: tuple = (), amount: float = 1.0) -> None:
        self._values[label_values] += amount

    def format_prometheus(self) -> str:
        lines = [
            f"# HELP {self.name} {self.help_text}",
            f"# TYPE {self.name} counter",
        ]
        for lv, val in sorted(self._values.items()):
            label_str = _format_labels(self.label_names, lv)
            lines.append(f"{self.name}{label_str} {val}")
        # Emit a zero line if no data so the metric always appears
        if not self._values:
            lines.append(f"{self.name} 0")
        return "\n".join(lines)


class _Histogram:
    """Label-aware histogram with configurable buckets."""

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def __init__(
        self,
        name: str,
        help_text: str,
        label_names: tuple[str, ...],
        buckets: tuple[float, ...] = DEFAULT_BUCKETS,
    ) -> None:
        self.name = name
        self.help_text = help_text
        self.label_names = label_names
        self.buckets = sorted(buckets)
        # Per label-value-combo: bucket_counts, sum, count
        self._data: dict[tuple, dict] = {}

    def _ensure(self, lv: tuple) -> dict:
        if lv not in self._data:
            self._data[lv] = {
                "buckets": defaultdict(int),
                "sum": 0.0,
                "count": 0,
            }
        return self._data[lv]

    def observe(self, label_values: tuple = (), value: float = 0.0) -> None:
        d = self._ensure(label_values)
        d["sum"] += value
        d["count"] += 1
        for b in self.buckets:
            if value <= b:
                d["buckets"][b] += 1
        # +Inf bucket always counts
        d["buckets"][math.inf] += 1

    def format_prometheus(self) -> str:
        lines = [
            f"# HELP {self.name} {self.help_text}",
            f"# TYPE {self.name} histogram",
        ]
        for lv, d in sorted(self._data.items()):
            label_str = _format_labels(self.label_names, lv)
            # d["buckets"][b] already stores the cumulative count of values <= b
            # (observe() increments every bucket whose le >= value).
            # Emit directly — do NOT accumulate again.
            for b in self.buckets:
                le_str = str(b)
                count = d["buckets"].get(b, 0)
                lines.append(f"{self.name}_bucket{_format_labels_with_le(self.label_names, lv, le_str)} {count}")
            # +Inf bucket
            lines.append(
                f"{self.name}_bucket{_format_labels_with_le(self.label_names, lv, '+Inf')} {d['buckets'].get(math.inf, 0)}"
            )
            lines.append(f"{self.name}_sum{label_str} {d['sum']:.6f}")
            lines.append(f"{self.name}_count{label_str} {d['count']}")
        return "\n".join(lines)


def _format_labels(names: tuple[str, ...], values: tuple) -> str:
    if not names:
        return ""
    pairs = ",".join(f'{n}="{v}"' for n, v in zip(names, values))
    return "{" + pairs + "}"


def _format_labels_with_le(names: tuple[str, ...], values: tuple, le: str) -> str:
    pairs = [f'{n}="{v}"' for n, v in zip(names, values)]
    pairs.append(f'le="{le}"')
    return "{" + ",".join(pairs) + "}"


class MetricsRegistry:
    """Container for all Prometheus metrics. Formats to text exposition format."""

    def __init__(self) -> None:
        self._metrics: list[_Counter | _Histogram] = []

    def counter(
        self, name: str, help_text: str, label_names: tuple[str, ...] = ()
    ) -> _Counter:
        c = _Counter(name, help_text, label_names)
        self._metrics.append(c)
        return c

    def histogram(
        self,
        name: str,
        help_text: str,
        label_names: tuple[str, ...] = (),
        buckets: tuple[float, ...] = _Histogram.DEFAULT_BUCKETS,
    ) -> _Histogram:
        h = _Histogram(name, help_text, label_names, buckets)
        self._metrics.append(h)
        return h

    def format_prometheus(self) -> str:
        """Return valid Prometheus text exposition format."""
        return "\n\n".join(m.format_prometheus() for m in self._metrics) + "\n"


# ═══════════════════════════════════════════════════════════════════════════
# §2 — Register metrics
# ═══════════════════════════════════════════════════════════════════════════

registry = MetricsRegistry()

requests_counter = registry.counter(
    "llm_requests_total",
    "Total LLM chat requests",
    label_names=("endpoint", "status"),
)
errors_counter = registry.counter(
    "llm_errors_total",
    "Total LLM request errors",
    label_names=("endpoint", "error_type"),
)
latency_hist = registry.histogram(
    "llm_request_duration_seconds",
    "End-to-end request latency in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
tokens_counter = registry.counter(
    "llm_tokens_total",
    "Cumulative token count",
    label_names=("type",),
)
cost_counter = registry.counter(
    "llm_cost_usd_total",
    "Cumulative cost in USD",
)


# ═══════════════════════════════════════════════════════════════════════════
# §3 — TraceLogger
# ═══════════════════════════════════════════════════════════════════════════

class TraceLogger:
    """
    Lightweight per-request distributed trace recorder.

    Generates a unique trace_id and records named spans with duration
    and arbitrary attributes. Emits a structured JSON log line when
    each span closes.
    """

    def __init__(self) -> None:
        import secrets
        self.trace_id: str = secrets.token_hex(4)  # 8 hex chars
        self._spans: list[dict] = []
        self._span_starts: dict[str, float] = {}

    def start_span(self, name: str) -> None:
        """Record the start time for a named span."""
        self._span_starts[name] = time.perf_counter()

    def end_span(self, name: str, **attrs: Any) -> None:
        """
        Close a span, compute duration_ms, append to trace,
        and emit a structured log line.
        """
        start = self._span_starts.pop(name, time.perf_counter())
        duration_ms = (time.perf_counter() - start) * 1000
        span = {"name": name, "duration_ms": round(duration_ms, 2), **attrs}
        self._spans.append(span)
        # Emit structured log — use extra dict so JSONFormatter picks up keys
        logger.info(
            f"span.end:{name}",
            extra={"trace_id": self.trace_id, "span": name, "duration_ms": round(duration_ms, 2), **attrs},
        )

    def to_dict(self) -> dict:
        return {"trace_id": self.trace_id, "spans": list(self._spans)}


# ═══════════════════════════════════════════════════════════════════════════
# §4 — Instrumented chat handler
# ═══════════════════════════════════════════════════════════════════════════

def instrumented_chat(
    client: TestClient, question: str, k: int = 3
) -> tuple[dict, dict]:
    """
    POST /chat through the in-process test client with full instrumentation.

    Timing model:
      - We time the full round-trip as the root span.
      - We simulate retrieve/generate sub-spans by splitting the total
        duration 20%/80%. In a real split pipeline you'd time each
        call independently.

    Returns:
        (response_json, trace_dict)
    """
    trace = TraceLogger()
    status = "success"

    trace.start_span("root")

    # ── Retrieve span (simulated from full call timing) ──────────────────
    trace.start_span("retrieve")
    t0 = time.perf_counter()

    try:
        resp = client.post("/chat", json={"question": question, "k": k})
        total_s = time.perf_counter() - t0

        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}")

        data = resp.json()

    except Exception as exc:  # noqa: BLE001
        total_s = time.perf_counter() - t0
        status = "error"
        error_type = type(exc).__name__

        # Close open spans with error info
        trace._span_starts["retrieve"] = time.perf_counter() - total_s * 0.2
        trace.end_span("retrieve", k=k, top_score=0.0, error=str(exc))
        trace._span_starts["generate"] = time.perf_counter() - total_s * 0.8
        trace.end_span("generate", model="mock", in_tokens=0, out_tokens=0, cost_usd=0.0, error=str(exc))
        trace.end_span("root", status="error", error=str(exc))

        errors_counter.inc(("/chat", error_type))
        requests_counter.inc(("/chat", "error"))
        latency_hist.observe((), total_s)

        return {}, trace.to_dict()

    # ── Simulate sub-span timing ─────────────────────────────────────────
    retrieve_s = total_s * 0.20
    generate_s = total_s * 0.80

    top_score = round(random.uniform(0.70, 0.98), 3)
    trace._span_starts["retrieve"] = time.perf_counter() - retrieve_s
    trace.end_span("retrieve", k=k, top_score=top_score)

    # Token estimates
    in_tokens = len(question.split()) * 4 + 200
    out_tokens = max(10, len(data.get("answer", "").split()) * 4 // 3)
    cost_usd = 0.0  # mock LLM — no real cost

    trace._span_starts["generate"] = time.perf_counter() - generate_s
    trace.end_span("generate", model="mock", in_tokens=in_tokens, out_tokens=out_tokens, cost_usd=cost_usd)

    trace.end_span("root", status=status)

    # ── Record metrics ────────────────────────────────────────────────────
    requests_counter.inc(("/chat", "success"))
    latency_hist.observe((), total_s)
    tokens_counter.inc(("input",), in_tokens)
    tokens_counter.inc(("output",), out_tokens)
    cost_counter.inc((), cost_usd)

    return data, trace.to_dict()


# ═══════════════════════════════════════════════════════════════════════════
# §5 — /metrics endpoint (Prometheus text format)
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/metrics-prom", tags=["ops"])
async def prometheus_metrics() -> Response:
    """
    Prometheus text-format metrics exposition endpoint.

    Returns all registered metrics in the Prometheus exposition format
    (text/plain; version=0.0.4). A real Prometheus scraper points at this
    endpoint; in the lab we fetch it via TestClient and parse it directly.
    """
    text = registry.format_prometheus()
    return Response(content=text, media_type="text/plain; version=0.0.4")


# ═══════════════════════════════════════════════════════════════════════════
# §6 — Metrics text-format parser helpers
# ═══════════════════════════════════════════════════════════════════════════

def _parse_counter(text: str, metric_name: str, label_filter: dict[str, str] | None = None) -> float:
    """
    Extract a counter value from Prometheus text format.

    Args:
        text: Full /metrics response body.
        metric_name: Metric name (e.g. "llm_requests_total").
        label_filter: Optional dict of label=value pairs to match
                      (e.g. {"status": "success"}).

    Returns:
        float value, or 0.0 if not found.
    """
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if not line.startswith(metric_name):
            continue
        # Check label filter
        if label_filter:
            if not all(f'{k}="{v}"' in line for k, v in label_filter.items()):
                continue
        # Extract value (last token)
        try:
            return float(line.split()[-1])
        except ValueError:
            continue
    return 0.0


def _parse_histogram_quantile(
    text: str, metric_name: str, quantile: float
) -> float:
    """
    Approximate a quantile from a Prometheus histogram using linear interpolation.

    Args:
        text: Full /metrics response body.
        metric_name: Base histogram name (e.g. "llm_request_duration_seconds").
        quantile: Desired quantile in (0, 1), e.g. 0.5 or 0.99.

    Returns:
        Approximate quantile value in the histogram's units, or -1.0 if
        insufficient data.
    """
    bucket_name = metric_name + "_bucket"
    count_name = metric_name + "_count"

    buckets: list[tuple[float, float]] = []  # (le, cumulative_count)
    total_count = 0.0

    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if line.startswith(bucket_name):
            # Extract le value and cumulative count
            try:
                # Format: name_bucket{le="0.05"} 12
                le_part = line.split('le="')[1].split('"')[0]
                val = float(line.split()[-1])
                le = float("inf") if le_part == "+Inf" else float(le_part)
                buckets.append((le, val))
            except (IndexError, ValueError):
                continue
        elif line.startswith(count_name):
            try:
                total_count = float(line.split()[-1])
            except ValueError:
                continue

    if total_count == 0 or not buckets:
        return -1.0

    target = quantile * total_count
    prev_le, prev_count = 0.0, 0.0

    for le, count in sorted(buckets, key=lambda x: (math.isinf(x[0]), x[0])):
        if math.isinf(le):
            continue
        if count >= target:
            # Linear interpolation within this bucket
            if count == prev_count:
                return prev_le
            fraction = (target - prev_count) / (count - prev_count)
            return prev_le + fraction * (le - prev_le)
        prev_le, prev_count = le, count

    # All values in last finite bucket
    return prev_le


# ═══════════════════════════════════════════════════════════════════════════
# §7 — Load workload + summary report
# ═══════════════════════════════════════════════════════════════════════════

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


def _print_trace(trace: dict) -> None:
    """Print a trace in a human-readable waterfall format."""
    print(f"\n[sample trace]")
    print(f"  trace_id : {trace['trace_id']}")
    print(f"  spans    :")
    for span in trace["spans"]:
        name = span["name"]
        dur = span.get("duration_ms", 0)
        attrs = {k: v for k, v in span.items() if k not in ("name", "duration_ms")}
        attr_str = "  ".join(f"{k}={v}" for k, v in attrs.items())
        print(f"    {name:<10} {dur:>7.1f} ms   {attr_str}")


def run_load_and_report() -> None:
    """Fire 20 questions, parse /metrics, print summary and a sample trace."""
    client = TestClient(app, raise_server_exceptions=False)

    print("=" * 60)
    print("Day 11 Lab — Running load workload (20 requests)")
    print("=" * 60)

    traces: list[dict] = []
    successes = 0
    errors = 0

    for i, q in enumerate(QUESTIONS, 1):
        data, trace = instrumented_chat(client, q, k=3)
        traces.append(trace)
        root = next((s for s in trace["spans"] if s["name"] == "root"), {})
        if root.get("status") == "success":
            successes += 1
        else:
            errors += 1

    print(f"\n[load] Sent {len(QUESTIONS)} requests — {successes} success, {errors} errors")

    # ── Fetch and parse /metrics ──────────────────────────────────────────
    resp = client.get("/metrics-prom")
    assert resp.status_code == 200, f"/metrics-prom returned {resp.status_code}"
    metrics_text = resp.text

    req_success = _parse_counter(metrics_text, "llm_requests_total", {"status": "success"})
    req_error = _parse_counter(metrics_text, "llm_requests_total", {"status": "error"})
    tok_input = _parse_counter(metrics_text, "llm_tokens_total", {"type": "input"})
    tok_output = _parse_counter(metrics_text, "llm_tokens_total", {"type": "output"})
    cost_total = _parse_counter(metrics_text, "llm_cost_usd_total")

    p50 = _parse_histogram_quantile(metrics_text, "llm_request_duration_seconds", 0.50)
    p99 = _parse_histogram_quantile(metrics_text, "llm_request_duration_seconds", 0.99)

    print("\n[metrics summary]")
    print(f'  llm_requests_total{{status="success"}} = {req_success:.0f}')
    print(f'  llm_requests_total{{status="error"}}   = {req_error:.0f}')
    print(f"  llm_request_duration_seconds p50 ~ {p50:.4f} s" if p50 > 0 else "  llm_request_duration_seconds p50 ~ <1 bucket")
    print(f"  llm_request_duration_seconds p99 ~ {p99:.4f} s" if p99 > 0 else "  llm_request_duration_seconds p99 ~ <1 bucket")
    print(f'  llm_tokens_total{{type="input"}}  = {tok_input:.0f}')
    print(f'  llm_tokens_total{{type="output"}} = {tok_output:.0f}')
    print(f"  llm_cost_usd_total               = {cost_total:.6f}")

    # ── Print one sample trace ────────────────────────────────────────────
    if traces:
        _print_trace(traces[0])

    # ── Raw /metrics snippet (first 20 lines) ────────────────────────────
    print("\n[/metrics-prom raw output — first 20 lines]")
    for line in metrics_text.splitlines()[:20]:
        print(" ", line)

    print("\n[done] Observability lab complete.")


# ── Langfuse reference snippet (documented; requires API key) ──────────────
# The following shows how you would instrument this service with Langfuse.
# It is NOT executed during the lab — just read it and refer to the README.
#
# from langfuse.decorators import observe, langfuse_context
#
# @observe(name="retrieve")
# def langfuse_retrieve(question: str, k: int) -> list[str]:
#     langfuse_context.update_current_observation(metadata={"k": k})
#     return []
#
# @observe(as_type="generation", name="generate")
# def langfuse_generate(question: str, contexts: list[str]) -> str:
#     langfuse_context.update_current_observation(
#         model="claude-haiku-4-5",
#         usage={"input": 300, "output": 70},
#         metadata={"cost_usd": 0.0},
#     )
#     return ""
#
# @observe(name="hr-chat")
# def langfuse_chat(question: str) -> str:
#     ctxs = langfuse_retrieve(question, k=3)
#     return langfuse_generate(question, ctxs)


# ── Entrypoint ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_load_and_report()
