# Day 11 — Observability for LLM Systems: Traces, Metrics & Structured Logs

**Track:** DevOps | **Day:** 11 of 15 | **Prerequisites:** Days 6–10

---

## 1. Objectives

By the end of this day you will be able to:

- Explain the **three pillars of observability** (logs, metrics, traces) and describe what changes — and what stays the same — when observing LLM systems versus conventional microservices.
- Instrument a Python service to emit **Prometheus-style metrics** (RED metrics, latency histogram, token/cost counters) via a `/metrics` text-format endpoint.
- Attach a **structured trace** to every request: a root span with child spans for the retrieval and generation steps, each carrying duration, token counts, and a trace ID.
- Describe how **Langfuse** and **LangSmith** extend OpenTelemetry concepts for LLM-specific observability (sessions, token cost on spans, prompt versioning).
- Define alert thresholds that matter for LLM applications (latency percentiles, error rate, token/cost drift, answer-quality drift).
- Run a **load workload**, parse a Prometheus text-format `/metrics` response, and summarise the resulting histogram and counters.

---

## 2. Concept Reading

### 2.1 The Three Pillars — and What LLMs Add

The three-pillar model (logs, metrics, traces) describes observability for any distributed system. LLM services fit the model, but each pillar gains LLM-specific dimensions:

| Pillar | Conventional meaning | LLM-specific additions |
|---|---|---|
| **Logs** | Timestamped event records | Prompt/completion content, retrieved chunks, provider response metadata, refusal reasons |
| **Metrics** | Numeric time series (counters, gauges, histograms) | Token counts per request, cost per request, cache-hit rate, model latency distribution |
| **Traces** | Causally-linked spans across service hops | Retrieval span (k, latency, scores), LLM span (model, tokens, cost), tool-call spans in agents |

The most important difference is **semantic depth**: a 200 ms latency spike in a conventional service is opaque until you look at traces. In an LLM service that same spike might be explained entirely by a 400-token increase in the retrieved context — and that context increase might itself be explained by a corpus expansion pushed an hour earlier. Observability for LLM systems must surface *why* generation costs or latency changed, not just *that* it changed.

---

### 2.2 Distributed Tracing — OpenTelemetry, Langfuse, LangSmith

**OpenTelemetry (OTel)** is the CNCF standard for distributed tracing. Every request gets a `trace_id`; within the trace each logical operation is a `span` with a start time, end time, and arbitrary key/value attributes.

For LLM pipelines the minimal useful span set is:

```
Trace: trace_id=abc123  [POST /chat — 310 ms total]
├── Span: retrieve       [0 ms → 45 ms]   k=3, top_score=0.87
└── Span: generate       [45 ms → 308 ms] model=mock, in_tokens=312, out_tokens=67, cost_usd=0.0
```

**Langfuse** (open-source, self-hostable) wraps OTel concepts into an LLM-first SDK. Key additions:

| Langfuse concept | OTel equivalent | Extra value |
|---|---|---|
| `trace` | Trace | Associates with a user session and input/output at the trace level |
| `span` / `generation` | Span | `generation` subtype carries model name, token counts, cost, prompt version |
| `session_id` | Baggage/attribute | Groups multiple traces from the same user conversation |
| `scores` | — (no OTel equivalent) | Human or automated quality scores attached post-hoc |

**LangSmith** (LangChain's hosted observability platform) follows a similar model. Its key differentiator is tight integration with LangChain/LangGraph — chains and agents are automatically wrapped without code changes. Token counts, latency, and cost are captured at every node. LangSmith also supports **dataset-based regression testing**: record production traces, evaluate them against a reference set, and catch quality regressions before they reach users.

Both tools export to standard OTel backends (Jaeger, Tempo, Honeycomb) via OTLP, so you are not locked in.

**Instrumenting with Langfuse (reference — requires API key):**

```python
# pip install langfuse
# Env: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

lf = Langfuse()

@observe()
def retrieve(question: str, k: int) -> list[str]:
    # ... your retrieval logic ...
    langfuse_context.update_current_observation(
        metadata={"k": k, "top_score": 0.87}
    )
    return contexts

@observe(as_type="generation")
def generate(question: str, contexts: list[str]) -> str:
    # ... your LLM call ...
    langfuse_context.update_current_observation(
        model="claude-haiku-4-5",
        usage={"input": 312, "output": 67},
        metadata={"cost_usd": 0.0004},
    )
    return answer

@observe(name="hr-chat")
def chat(question: str) -> str:
    ctxs = retrieve(question, k=3)
    return generate(question, ctxs)
```

The `@observe` decorator automatically creates parent/child spans and flushes them to Langfuse on function exit. No key is needed for the lab — the lab implements equivalent logic by hand.

---

### 2.3 Metrics with Prometheus & Grafana

**Prometheus** scrapes a `/metrics` HTTP endpoint that returns plain-text in a defined format. A typical LLM service exposes:

**RED metrics** (the standard for request-driven services):

| Metric name | Type | Description |
|---|---|---|
| `llm_requests_total` | Counter | Total requests (label: `endpoint`, `status`) |
| `llm_errors_total` | Counter | Total errors (label: `endpoint`, `error_type`) |
| `llm_request_duration_seconds` | Histogram | End-to-end latency |

**LLM-specific additions:**

| Metric name | Type | Description |
|---|---|---|
| `llm_tokens_total` | Counter | Cumulative tokens (label: `type=input\|output`) |
| `llm_cost_usd_total` | Counter | Cumulative cost in USD |
| `llm_retrieve_duration_seconds` | Histogram | Retrieval step latency |
| `llm_generate_duration_seconds` | Histogram | Generation step latency |
| `llm_cache_hits_total` | Counter | Cache hits (label: `cache_type`) |

**Prometheus text format** (what `/metrics` must return):

```
# HELP llm_requests_total Total LLM chat requests
# TYPE llm_requests_total counter
llm_requests_total{endpoint="/chat",status="success"} 142
llm_requests_total{endpoint="/chat",status="error"} 3

# HELP llm_request_duration_seconds Request latency histogram
# TYPE llm_request_duration_seconds histogram
llm_request_duration_seconds_bucket{le="0.05"} 12
llm_request_duration_seconds_bucket{le="0.1"} 58
llm_request_duration_seconds_bucket{le="0.25"} 131
llm_request_duration_seconds_bucket{le="0.5"} 142
llm_request_duration_seconds_bucket{le="1.0"} 145
llm_request_duration_seconds_bucket{le="+Inf"} 145
llm_request_duration_seconds_sum 18.43
llm_request_duration_seconds_count 145
```

**Grafana** reads from Prometheus via PromQL. The most useful panels for an LLM service:

| Panel | PromQL | Why it matters |
|---|---|---|
| Request rate | `rate(llm_requests_total[5m])` | Traffic baseline |
| Error rate | `rate(llm_errors_total[5m]) / rate(llm_requests_total[5m])` | Immediate alerting |
| p99 latency | `histogram_quantile(0.99, rate(llm_request_duration_seconds_bucket[5m]))` | User-perceived slowness |
| Cost rate | `rate(llm_cost_usd_total[1h]) * 3600` | $/hour spend |
| Token rate | `rate(llm_tokens_total{type="input"}[5m])` | Input token growth |

**Using the `prometheus_client` library (Python):**

```python
from prometheus_client import Counter, Histogram, start_http_server, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter("llm_requests_total", "Total requests", ["endpoint", "status"])
LATENCY = Histogram("llm_request_duration_seconds", "Request latency",
                    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0])
TOKEN_COUNT = Counter("llm_tokens_total", "Cumulative tokens", ["type"])
COST = Counter("llm_cost_usd_total", "Cumulative USD cost")

# Record a request
with LATENCY.time():
    result = answer(question)
REQUEST_COUNT.labels(endpoint="/chat", status="success").inc()
TOKEN_COUNT.labels(type="input").inc(result.get("input_tokens", 0))
```

The library's `generate_latest()` function returns the Prometheus text format bytes; your FastAPI endpoint just returns those bytes with `Content-Type: text/plain; version=0.0.4`.

---

### 2.4 Structured Logging

Unstructured logs (`print("answering question...")`) are useless at scale. **Structured logging** emits JSON — every log line is machine-parseable:

```json
{
  "ts": "2026-06-18T10:23:01.412Z",
  "level": "INFO",
  "trace_id": "a3f9c1d2",
  "span": "generate",
  "model": "mock",
  "in_tokens": 312,
  "out_tokens": 67,
  "duration_ms": 263.1,
  "cost_usd": 0.0,
  "question_hash": "8f3c..."
}
```

Key design rules:

1. **Every log line carries a `trace_id`** so you can correlate all log lines from one request.
2. **Log at the span boundary**: one log line when a span opens (optional), one when it closes (always, with duration and outcome).
3. **Never log raw prompt/completion text in production** unless your security review explicitly permits it — it creates PII/IP exposure. Log a hash or a truncated prefix instead.
4. **Use Python's `logging` module with a JSON formatter** — do not use `print()`. The `pythonjsonlogger` library or a custom `logging.Formatter` subclass both work.

---

### 2.5 Quality & Drift Monitoring in Production

Observability for LLM systems is not complete without tracking *answer quality* — because metrics and traces cannot tell you whether the generated text is correct.

**Production quality monitoring approaches:**

| Technique | How it works | Cost |
|---|---|---|
| **LLM-as-judge** | A second (cheaper) LLM scores each answer: relevance, groundedness, coherence | Low per-call cost; needs calibration |
| **Embedding drift** | Compute embedding of each question; alert when centroid drifts from baseline | No LLM needed; catches topic-shift and corpus poisoning |
| **Retrieval score monitoring** | Track top-1 cosine/BM25 score; a drop means the corpus no longer covers the incoming question distribution | Cheap; surfaces corpus staleness |
| **A/B quality log** | Randomly route a small % of traffic to a new model/prompt; compare LLM-judge scores | Requires traffic volume |
| **Human labelling pipeline** | Sample 1% of production traces; route to labellers; compute accuracy weekly | Ground truth; expensive |

**Alerting thresholds** (example — calibrate for your system):

| Metric | Warning | Critical |
|---|---|---|
| Error rate (5 min window) | > 2% | > 5% |
| p99 latency | > 2 s | > 5 s |
| Cost per request | > 2× 7-day mean | > 5× 7-day mean |
| Retrieval top-1 score | < 0.4 | < 0.2 |
| LLM-judge score (0–1) | < 0.7 | < 0.5 |
| Daily spend | > 80% of budget | > 100% of budget |

**Drift detection for embeddings:**

```python
import numpy as np

class DriftMonitor:
    def __init__(self, window: int = 1000):
        self.baseline_centroid: np.ndarray | None = None
        self.window = window
        self._recent: list[np.ndarray] = []

    def update(self, embedding: np.ndarray) -> float | None:
        """Returns cosine distance from baseline, or None if baseline not set."""
        self._recent.append(embedding)
        if len(self._recent) >= self.window and self.baseline_centroid is None:
            self.baseline_centroid = np.mean(self._recent, axis=0)
        if self.baseline_centroid is None:
            return None
        centroid = np.mean(self._recent[-self.window:], axis=0)
        cos_sim = np.dot(centroid, self.baseline_centroid) / (
            np.linalg.norm(centroid) * np.linalg.norm(self.baseline_centroid) + 1e-9
        )
        return float(1.0 - cos_sim)  # drift = cosine distance
```

---

### 2.6 Dashboards & Alerting — What Thresholds Matter

A well-designed LLM observability dashboard has four rows:

**Row 1 — Traffic & Availability** (RED): request rate, error rate, p50/p99 latency. Set alerting on error rate and p99 latency. These are the same as any service.

**Row 2 — Cost & Tokens**: tokens/minute (input and output separately), cost/hour, cost/request rolling mean. Alert on cost/request deviation (2× rolling mean triggers a page).

**Row 3 — LLM-Specific Quality**: retrieval top-1 score distribution, LLM-judge score distribution (if enabled), cache hit rate. Alert on retrieval score collapse (corpus staleness) and judge score decline (model regression or prompt drift).

**Row 4 — Infrastructure**: CPU/memory, GPU utilisation (if self-hosted), Kubernetes pod restarts, queue depth. These are standard SRE metrics.

**Alert routing**: cost/token alerts go to the engineering + finance channel; quality alerts go to the ML team; availability alerts go to the on-call engineer.

---

## 3. Hands-On Lab

See `labs/devops/day-11/` for:
- `README.md` — lab instructions
- `requirements.txt` — dependencies
- `starter.py` — skeleton with TODO comments
- `solution.py` — complete reference implementation

The lab instruments the shared HR app with Prometheus-style metrics, per-request structured trace logging, and a load workload. Run with:

```bash
cd labs/devops/day-11
pip install -r requirements.txt
python solution.py
```

No API key required.

---

## 4. Self-Check Quiz

**Q1. Name the three pillars of observability. For each pillar, give one metric/log field/span attribute that is unique to LLM systems.**

<details>
<summary>Show answer</summary>

The three pillars are **logs**, **metrics**, and **traces**. LLM-specific additions per pillar:
- **Logs**: prompt/completion content, retrieved chunks, provider response metadata, refusal reasons.
- **Metrics**: token counts per request, cost per request, cache-hit rate, model latency distribution.
- **Traces**: retrieval span attributes (k, top score, latency), LLM generation span attributes (model name, token counts, cost), tool-call spans in agents.

</details>

**Q2. What is the difference between a `span` and a `generation` in Langfuse terminology?**

<details>
<summary>Show answer</summary>

A **span** is the generic Langfuse equivalent of an OTel span — it represents any timed operation (e.g., retrieval, a database call) and carries start time, end time, and arbitrary key/value attributes.

A **generation** is a specialised span subtype for LLM calls. It carries first-class fields for `model`, `usage` (input/output token counts), `cost`, and `prompt_version`, which are not part of the standard OTel span schema. Use `generation` for any step that calls a language model; use `span` for all other steps.

</details>

**Q3. Write the Prometheus text-format lines for a counter `llm_requests_total` with label `status="success"` at value 57.**

<details>
<summary>Show answer</summary>

```
# HELP llm_requests_total Total LLM chat requests
# TYPE llm_requests_total counter
llm_requests_total{status="success"} 57
```

The `# HELP` and `# TYPE` comment lines are required before the first sample line. The label set is enclosed in `{}` and the value follows after a space.

</details>

**Q4. Why should you never log raw prompt/completion text in production without a security review?**

<details>
<summary>Show answer</summary>

Raw prompts and completions may contain:
- **PII** — user names, employee IDs, salary figures, or health information embedded in questions or retrieved context.
- **Intellectual property** — proprietary HR policies or internal documents surfaced by the retrieval step.
- **Authentication-adjacent data** — session context that could help an attacker reconstruct a user's intent.

Logging this data creates a persistent, often broadly-accessible record that violates data minimisation principles (GDPR, CCPA) and widens the blast radius of a log-pipeline breach. Instead, log a SHA-256 hash of the question and token counts only; store full content only in a separate, access-controlled, short-retention log stream if operationally required.

</details>

**Q5. A new corpus of HR documents was uploaded yesterday. Which observability signal would *first* indicate that retrieval quality has degraded, and why?**

<details>
<summary>Show answer</summary>

The **retrieval top-1 cosine/BM25 score** would be the first signal to drop. When the corpus changes, the embedding index must be rebuilt; if the new documents shift the vector space or the index is partially stale, the similarity scores returned for incoming queries will fall — even before any user notices a wrong answer. This signal precedes LLM-judge score degradation because it sits earlier in the pipeline and requires no LLM inference to compute.

</details>

**Q6. What is the difference between embedding drift and retrieval score monitoring? When would you use each?**

<details>
<summary>Show answer</summary>

- **Embedding drift** monitors the *query* side: it tracks the centroid of incoming question embeddings over time and alerts when the distribution shifts away from the baseline. Use it to detect that users are asking questions outside the system's designed scope (input/semantic drift).
- **Retrieval score monitoring** monitors the *retrieval* side: it tracks the top-1 similarity score returned by the vector store for each query. Use it to detect that the corpus no longer covers the incoming questions well — typically caused by corpus staleness, index corruption, or a change in the embedding model.

Use both together: a drop in retrieval scores with stable query embeddings points to a corpus problem; a drift in query embeddings with stable retrieval scores points to a user-behaviour shift.

</details>

**Q7. Your p99 latency alert fires at 5 s but your p50 is 120 ms. What does this pattern suggest about the latency distribution?**

<details>
<summary>Show answer</summary>

The distribution is **heavily right-skewed with a long tail** — the vast majority of requests (the median) complete quickly at ~120 ms, but a small fraction (roughly the top 1%) take dramatically longer at ≥ 5 s. This pattern is typical of LLM services where most requests hit a cache or use a short context, while occasional requests involve long retrieved contexts, retries, or cold-start model loading. The alert is real and worth investigating, but the impact is limited to a small proportion of users. Focus diagnosis on what distinguishes the slow outliers (context length? specific query patterns? downstream provider timeouts?).

</details>

**Q8. Explain why `rate(llm_cost_usd_total[1h]) * 3600` gives you cost-per-hour in Grafana.**

<details>
<summary>Show answer</summary>

`llm_cost_usd_total` is a Prometheus **counter** (monotonically increasing). `rate(...[1h])` computes the **per-second** rate of increase averaged over the last 1 hour — i.e., dollars per second. Multiplying by 3600 (seconds per hour) converts the per-second rate to a **per-hour** rate, giving an intuitive cost-per-hour figure. If you used `[5m]` the result would be noisier (more responsive to bursts) but still correct after the `* 3600` scaling.

</details>

**Q9. Your `/metrics-prom` endpoint returns an empty body after deploying a new version. What is the most likely cause, and what would you check first?**

<details>
<summary>Show answer</summary>

The most likely causes in order of probability:
1. **Metric registration failure** — the `prometheus_client` registry was not initialised or the metric objects were defined inside a function/conditional block that was never executed. Check that all `Counter`/`Histogram` objects are defined at module level and that the module is imported at startup.
2. **Wrong endpoint handler** — the route `/metrics-prom` was not re-registered in the new version (e.g., a merge conflict dropped the route). Check the route table (`app.routes` in FastAPI).
3. **`generate_latest()` not called** — the handler returns an empty `Response()` instead of `Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)`. Inspect the handler code.

First check: call the endpoint manually (`python -c "import requests; print(requests.get('http://localhost:8000/metrics-prom').text)"`) and compare with the previous version's output to narrow down whether the endpoint exists but is empty, or returns a 404.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. OpenTelemetry already handles distributed tracing. Why do tools like Langfuse and LangSmith exist on top of it?**

<details>
<summary>Show answer</summary>

OTel is generic — it knows about spans and attributes, but nothing about prompts, tokens, or costs. Langfuse/LangSmith add:
- A `generation` span subtype with first-class `model`, `usage` (tokens), and `cost` fields.
- A `score` concept for attaching human or automated quality judgments to any trace post-hoc.
- UI designed for navigating thousands of LLM traces (prompt diffs, cost breakdowns, latency waterfall per node).
- Dataset management: record production traces, edit them into golden examples, run regression evals against them.

You *could* build all of this on raw OTel, but Langfuse and LangSmith give you the LLM-specific schema and UI out of the box.

</details>

**Q2. Prometheus histograms use pre-defined bucket boundaries. How do you choose good buckets for LLM latency?**

<details>
<summary>Show answer</summary>

LLM latency distributions are typically bimodal: cached/mock responses at < 50 ms, real LLM calls at 200 ms–5 s depending on model and output length. A useful bucket set is:

```
[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
```

The default `prometheus_client` buckets (`[0.005, 0.01, 0.025, ...]`) are tuned for web application response times in the millisecond range — they will cluster all LLM calls into the `+Inf` bucket, making percentile estimates useless. Always override buckets for LLM services.

</details>

**Q3. What is "semantic drift" in the context of LLM observability, and how is it different from model drift?**

<details>
<summary>Show answer</summary>

**Model drift** refers to the LLM itself changing behaviour — due to a model update, fine-tune change, or prompt change. The model produces different answers to the same questions over time.

**Semantic drift** (or *input drift*) refers to the *incoming query distribution* shifting away from what the system was designed for. Users start asking questions the corpus does not cover, or about topics outside the system's scope. Retrieval scores drop; the LLM answers from limited context.

You detect them differently:
- Model drift: LLM-judge scores change while retrieval scores hold steady.
- Input drift: retrieval scores drop (or question embedding centroid drifts) while model behaviour on *in-distribution* questions is unchanged.

</details>

**Q4. Structured logs, metrics, and traces all capture latency. Why do you need all three?**

<details>
<summary>Show answer</summary>

They answer different questions:
- **Logs** answer: *what happened in this specific request?* (full context, one-off debugging)
- **Metrics** answer: *what is the overall system doing right now, and over time?* (aggregation, alerting, dashboards)
- **Traces** answer: *where did time go in this specific request across service boundaries?* (performance profiling, root cause)

A latency spike shows up in metrics (p99 rises). You then use traces to identify *which span* (retrieval? generation?) accounts for it. You then use logs from the same `trace_id` to inspect the exact payload (long context? unusual question?) that caused it. Each pillar is useless without the others.

</details>

**Q5. How should you handle the tension between logging enough detail for debugging and avoiding PII exposure from prompt/completion logging?**

<details>
<summary>Show answer</summary>

A layered approach works well in practice:
1. **Always log**: `trace_id`, `span`, `duration_ms`, `token_counts`, `status_code`, `question_hash` (SHA-256 of raw question).
2. **Log in dev/staging only**: truncated question (first 50 chars), truncated completion.
3. **Log with consent and encryption at rest**: full prompt/completion in a separate, access-controlled log stream with a short retention window (e.g., 7 days).
4. **Never log**: retrieved documents that may contain employee personal data, full PII fields, authentication tokens.

Use a structured log field `pii_tier: [none | truncated | full]` to mark each log line's sensitivity level, and apply different retention policies per tier.

</details>

**Q6. Your Prometheus counter `llm_requests_total` shows a sudden flat line (no new increments) after a deployment. Alert is firing. Walk through the diagnosis.**

<details>
<summary>Show answer</summary>

A flat counter means either (a) no requests are reaching the instrumented handler, or (b) the metrics registry was re-initialised and lost its state. Diagnosis steps:

1. **Check if the app is receiving traffic** — look at the access log or a separate `http_requests_total` metric that counts all routes. If that is also flat, the issue is upstream (load balancer, DNS, ingress) not the metrics instrumentation.
2. **Check `/metrics-prom` directly** — if the endpoint returns HTTP 200 but the counter is missing entirely (not at 0, but absent), the metric was not re-registered after the deployment (e.g., a module-level registry was reset). Verify that the registry initialisation runs at startup, not inside a request handler.
3. **Check if the counter is stuck at 0 vs. not incrementing** — a counter at 0 that was present before the deploy suggests the handler is not being reached (routing bug, middleware short-circuiting). A missing counter suggests registration failure.
4. **Compare the running image** — confirm the deployed image matches the expected tag (`kubectl describe pod` → `Image`). A stale image from cache can explain why new instrumentation is absent.

The most common root cause after a deployment: the new code registers metrics inside a conditional block or lazy initialisation path that was not triggered in the new deployment environment.

</details>

---

## 6. Further Reading

- [OpenTelemetry Python SDK](https://opentelemetry-python.readthedocs.io/) — Official OTel Python instrumentation guide.
- [Langfuse Documentation](https://langfuse.com/docs) — Open-source LLM observability; covers traces, scores, datasets (Day 11).
- [LangSmith Documentation](https://docs.smith.langchain.com) — LLM observability and tracing; production monitoring (Day 11).
- [Prometheus Data Model](https://prometheus.io/docs/concepts/data_model/) — Counter, gauge, histogram, summary semantics.
- [Google SRE Book — Chapter 6: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) — The canonical RED/USE methodology.
- [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/) — Threshold and anomaly-based alerting for Prometheus metrics.

---

## 7. Key Takeaways

| Topic | Key takeaway |
|---|---|
| Three pillars | Metrics (aggregation), logs (per-request detail), traces (cross-service flow) — LLM systems need all three plus eval scores as a fourth signal. |
| LLM-specific metrics | Token counts, cost per request, cache hit rate, and retrieval score are not in standard web observability stacks — you must instrument them explicitly. |
| OpenTelemetry vs Langfuse | OTel provides generic spans and attributes; Langfuse/LangSmith add LLM-specific `generation` types, token/cost tracking, and quality scores with a purpose-built UI. |
| Prometheus histograms | Default buckets are tuned for millisecond web latency — always override with LLM-appropriate buckets (e.g., 50 ms–10 s range). |
| Structured logging | Log `trace_id`, token counts, and `question_hash`; never log raw PII or full prompt/completions in production without access controls and short retention. |
| Semantic vs model drift | Semantic drift = query distribution shifts; model drift = model behaviour changes. Different signals, different remediation. |
| Alerting thresholds | Cost-per-hour, p99 latency, retrieval score drop, and error rate are the four LLM-specific alert dimensions beyond standard SRE signals. |
| `/metrics-prom` endpoint | Exposes Prometheus text-format metrics; used instead of `/metrics` to avoid clashing with the shared app's existing JSON `/metrics` endpoint. |
