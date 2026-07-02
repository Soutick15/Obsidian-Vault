# Day 11 Lab — LLM Observability: Prometheus Metrics, Structured Traces & Load Testing

**Track:** DevOps | **Difficulty:** Intermediate | **Runtime:** ~60–75 min

---

## What You'll Build

You'll instrument the shared Acme HR Knowledge Assistant with:

1. **Prometheus-style `/metrics` endpoint** — Prometheus text-format exposition of RED metrics (request count, error count, latency histogram) plus LLM-specific counters (token counts, cost, retrieve/generate step latencies).
2. **Per-request structured trace logging** — every `/chat` request emits a JSON trace with a root span and child spans for retrieval and generation, each carrying duration and token data.
3. **Load workload generator** — fires 20 questions at the in-process test client to populate metrics, then prints a metrics summary and one sample trace.

No API key required. No external Prometheus server needed — you parse the text-format output directly.

---

## Prerequisites

```bash
pip install -r requirements.txt
```

---

## Files

| File | Purpose |
|---|---|
| `starter.py` | Skeleton with TODO comments — your starting point |
| `solution.py` | Complete reference implementation |
| `requirements.txt` | Python dependencies |

---

## Running the Lab

```bash
# Complete the TODOs in starter.py, then:
python starter.py

# Or run the reference solution directly:
python solution.py
```

Expected output (abbreviated):

```
[load] Sent 20 requests — 20 success, 0 errors
[metrics summary]
  llm_requests_total{status="success"} = 20
  llm_requests_total{status="error"}   = 0
  llm_request_duration_seconds p50 ~ 0.014 s
  llm_request_duration_seconds p99 ~ 0.028 s
  llm_tokens_total{type="input"}  = 4820
  llm_tokens_total{type="output"} = 1340
  llm_cost_usd_total               = 0.0

[sample trace]
  trace_id : a3f9c1d2
  spans    :
    root      0–312 ms  status=success
    retrieve  0–44 ms   k=3 top_score=0.87
    generate  44–312 ms model=mock in_tokens=241 out_tokens=67 cost=0.0
```

---

## Lab Tasks (starter.py TODOs)

### TODO 1 — MetricsRegistry
Implement an in-memory `MetricsRegistry` class with:
- `Counter(name, labels)` — increments with `inc(label_values, amount=1)`
- `Histogram(name, labels, buckets)` — records with `observe(label_values, value)`
- `format_prometheus()` — returns Prometheus text-format string

### TODO 2 — Register Metrics
Create the five metrics in the global registry:
- `llm_requests_total` (counter, labels: endpoint, status)
- `llm_errors_total` (counter, labels: endpoint, error_type)
- `llm_request_duration_seconds` (histogram, buckets: [0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0])
- `llm_tokens_total` (counter, labels: type)
- `llm_cost_usd_total` (counter, no labels)

### TODO 3 — Structured Trace Logger
Implement `TraceLogger` that:
- Generates a random 8-hex-char `trace_id` per request
- Supports `start_span(name)` / `end_span(name, **attrs)` recording duration
- Returns the completed trace as a dict (`{"trace_id": ..., "spans": [...]}`)

### TODO 4 — Instrumented Chat Handler
Write `instrumented_chat(client, question, k)` that:
- Creates a trace
- Calls the shared `answer()` function with timing for retrieve+generate steps
- Records all metrics
- Returns `(response_data, trace)`

### TODO 5 — /metrics Endpoint
Add a `/metrics` route to the FastAPI app that returns `registry.format_prometheus()` with `Content-Type: text/plain; version=0.0.4`.

### TODO 6 — Load Workload
Send 20 diverse HR questions through the in-process test client, collect traces, then:
- Print a metrics summary (parsed from `/metrics`)
- Print one sample trace in readable format

---

## Langfuse Reference Snippet

The following snippet demonstrates how you would instrument this service with Langfuse when an API key is available. It is for reference only — the lab runs without it.

```python
# pip install langfuse
# Required env vars: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
# (These are NOT needed to run the lab — mock instrumentation is used instead)

from langfuse.decorators import observe, langfuse_context

@observe(name="retrieve")
def langfuse_retrieve(question: str, k: int) -> list[str]:
    from service import answer as svc_answer
    # In a real RAG pipeline you'd call your retriever here
    langfuse_context.update_current_observation(
        metadata={"k": k}
    )
    return []  # placeholder

@observe(as_type="generation", name="generate")
def langfuse_generate(question: str, contexts: list[str]) -> str:
    langfuse_context.update_current_observation(
        model="claude-haiku-4-5",
        usage={"input": 300, "output": 70},
        metadata={"cost_usd": 0.0004},
    )
    return ""  # placeholder

@observe(name="hr-chat")
def langfuse_chat(question: str) -> str:
    ctxs = langfuse_retrieve(question, k=3)
    return langfuse_generate(question, ctxs)
```

---

## Extension Challenges

1. Add a `llm_retrieve_duration_seconds` histogram for just the retrieval step and a `llm_generate_duration_seconds` histogram for the generation step. Print their p50/p99 in the summary.
2. Implement a simple LLM-as-judge scorer: after each answer, check whether the word count of the answer is in the range [20, 300]. If not, increment a `llm_quality_violations_total` counter.
3. Write a `parse_histogram_quantile(metrics_text, metric_name, quantile)` function that computes an approximate quantile from histogram bucket counts using linear interpolation.
4. Add a `session_id` field to traces and group the 20-request workload into 4 "sessions" of 5 questions each.
