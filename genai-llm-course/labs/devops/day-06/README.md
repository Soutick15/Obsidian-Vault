# Day 6 Lab — Operability Assessment

**Track:** DevOps | **Day:** 6 of 15 | **Duration:** ~75 minutes

---

## Goal

Produce a structured **operability report** for the shared Acme HR Assistant by:

1. Exercising all three endpoints (`/health`, `/chat`, `/metrics`) via FastAPI's in-process `TestClient` — no running server needed.
2. Measuring per-endpoint latency (min, mean, p95).
3. Evaluating the service against a production-readiness checklist derived from the DOES framework.
4. Printing a gap report that identifies what is present, what is missing, and what to build next.

---

## Prerequisites

- Completed Days 1–5 (course foundation).
- Read `curriculum/devops/Day-06-llm-systems-to-operate.md`.
- Python 3.11+ with a virtual environment active.

---

## Setup

```bash
# From repo root
pip install -r labs/devops/day-06/requirements.txt

# Verify the shared service works first
python labs/devops/_shared/app.py --selftest
```

---

## Files

| File | Purpose |
|---|---|
| `README.md` | This file |
| `requirements.txt` | Lab dependencies |
| `starter.py` | Your working file — complete the TODOs |
| `solution.py` | Full reference implementation |

---

## Tasks (starter.py)

The `starter.py` file has five clearly marked TODO blocks:

1. **TODO 1** — Import the shared app via `sys.path` manipulation and create a `TestClient`.
2. **TODO 2** — Call `/health` and validate the response structure.
3. **TODO 3** — Call `/chat` with multiple questions; measure per-call latency.
4. **TODO 4** — Call `/metrics` and parse the counters.
5. **TODO 5** — Evaluate the checklist and print the structured operability report.

Work through them in order. Each TODO has a hint comment.

---

## Running

```bash
# Your work-in-progress
python labs/devops/day-06/starter.py

# Reference solution
python labs/devops/day-06/solution.py
```

Expected output (abridged):
```
=== Acme HR Assistant — Operability Assessment ===

[ENDPOINT] GET /health
  status         : ok
  version        : 0.1.0
  corpus_docs    : 12
  corpus_chunks  : 87
  latency_ms     : 4.2

[ENDPOINT] POST /chat  (3 questions)
  latency_ms min/mean/p95 : 8.1 / 11.4 / 14.9
  sources returned        : yes
  mock_llm                : true

[ENDPOINT] GET /metrics
  requests recorded       : yes
  avg_latency tracked     : yes

=== Operability Checklist ===
  [PASS] Liveness endpoint (/health) responds 200
  [PASS] Corpus loaded and non-empty
  [PASS] Structured JSON logging configured
  [PASS] In-process metrics endpoint present
  [PASS] Request latency tracked
  [FAIL] Readiness probe distinct from liveness probe
  [FAIL] Token count per request not in metrics
  [FAIL] Cost per request not tracked
  [FAIL] No semantic cache layer present
  [FAIL] No LLM gateway / rate-limit handling
  [FAIL] Prompt template version not exposed in /health

=== Gap Summary ===
  Passes : 5 / 11
  Gaps   : 6 / 11

Next steps → Days 7-10 will address observability, gateway, and caching.
```

---

## Reflection Questions

After running the solution, consider:

- Which gaps are the highest operational risk if this service handled 1,000 requests/day?
- The `/health` endpoint returns `corpus_found: true`. What would a readiness probe additionally need to check?
- If the mock LLM were replaced with a real API call, which checklist items would become critical immediately?

---

## Connection to Curriculum

| Day | Builds on this lab |
|---|---|
| Day 7 | Adds structured Prometheus-style metrics (addressing the token-count and cost gaps) |
| Day 8 | Adds CI/CD pipeline with the `--selftest` as the smoke-test gate |
| Day 9 | Adds an LLM gateway layer (addressing the rate-limit gap) |
| Day 10 | Adds semantic caching (addressing the cache gap) |
