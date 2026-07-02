# Day 12 Lab — Reliability & Resilience: Retry, Circuit Breaker, Failover, SLO

## Objectives

By completing this lab you will have:

1. Implemented **exponential backoff with full jitter** for a 429/5xx retry loop.
2. Written a **per-call timeout** wrapper that aborts slow provider calls.
3. Built a **three-state circuit breaker** (Closed / Open / Half-Open) that trips on repeated failures and self-heals.
4. Wired a **multi-provider failover chain** (primary → secondary) with final **graceful degradation** to a cached/canned answer.
5. Run a workload against deterministic mock providers with injected failures and printed an **SLO attainment report** (availability, latency, retry count, circuit-breaker trips, failovers).

## Files

```
labs/devops/day-12/
├── README.md           ← you are here
├── requirements.txt    ← stdlib only; no API key required
├── starter.py          ← work through TODO markers (6 tasks)
└── solution.py         ← reference implementation; run to verify
```

## Setup

No dependencies beyond the Python standard library:

```bash
# Confirm Python 3.11+
python --version

# Run the reference solution (no API key needed)
python labs/devops/day-12/solution.py
```

## Run the solution

```bash
python labs/devops/day-12/solution.py
```

## Expected output (approximate)

```
============================================================
 Day 12 — Resilience Wrapper: Workload Run
============================================================

Primary provider config : failure_rate=0.45, latency_ms=50, timeout_ms=200
Secondary provider config: failure_rate=0.20, latency_ms=80, timeout_ms=200
Circuit breaker         : threshold=3, recovery=5.0s
Retry policy            : max_attempts=3, base=0.05s, cap=1.0s

Running 20 requests...

  R01  SUCCESS   primary   retries=0  lat=  52ms  "How many days of annual leave?"
  R02  DEGRADED  cache     retries=2  lat= 210ms  "What is the dental benefit?"
  R03  SUCCESS   primary   retries=1  lat= 158ms  "How do I submit an expense?"
  R04  FAILOVER  secondary retries=2  lat= 340ms  "When does probation end?"
  ...

============================================================
 SLO REPORT
============================================================
Total requests      : 20
Successful answers  : 18  (90.0%)
  via primary       : 11
  via secondary     :  4
  via degradation   :  3
Failed (no answer)  :  2  (10.0%)

Retries issued      : 23
Circuit breaker trips:  2  (primary CB tripped 2×)
Failover activations:  5

Availability SLI    : 90.0%   target ≥ 95.0%   MISS ✗
P99 latency SLI     : 412ms   target ≤ 4000ms  PASS ✓
Retry rate SLI      : 19.2%   target ≤ 30.0%   PASS ✓
Degraded-answer rate:  15.0%  target ≤ 20.0%   PASS ✓

SLOs met: 3 / 4
Error budget (avail): consumed 200.0% of monthly budget this run
============================================================
```

> Numbers will vary slightly because jitter uses `random`. Availability will fluctuate; the key check is that the **four SLI columns print**, retries/CB/failover paths are exercised, and the script exits successfully.

## Tasks

Work through `starter.py` in order. Each task is bracketed with `# === TODO-N ===` markers:

| Task | Component | What you implement |
|---|---|---|
| TODO-1 | `backoff_wait()` | Exponential backoff with full jitter |
| TODO-2 | `TimeoutWrapper` | Per-call timeout using `threading.Timer` |
| TODO-3 | `CircuitBreaker` | Closed/Open/Half-Open state machine |
| TODO-4 | `MockProvider` | Deterministic mock with injected failure rate + latency |
| TODO-5 | `ResilienceWrapper.call()` | Retry loop → circuit breaker → primary → secondary → degradation |
| TODO-6 | `SLOReporter.report()` | Compute and print SLI attainment vs. targets |

## Grading yourself

- **Basic pass:** All 6 TODOs complete; `python starter.py` runs without error.
- **Good:** SLO report prints all four SLIs; retries, CB trips, and failovers are all > 0 in the run.
- **Excellent:** Modify `PRIMARY_FAILURE_RATE` to 0.8 and confirm the circuit breaker trips more aggressively and the availability SLI drops; lower to 0.1 and confirm availability improves.
- **Stretch:** Add a sliding-window failure count (count only failures in the last 60 s) instead of a cumulative counter.

## Provider configuration constants

Adjust in `starter.py` / `solution.py` to explore different failure modes:

| Constant | Default | Effect |
|---|---|---|
| `PRIMARY_FAILURE_RATE` | 0.45 | Fraction of primary calls that fail (429 or 5xx) |
| `SECONDARY_FAILURE_RATE` | 0.20 | Fraction of secondary calls that fail |
| `PRIMARY_LATENCY_MS` | 50 | Base latency per primary call (ms) |
| `SECONDARY_LATENCY_MS` | 80 | Base latency per secondary call (ms) |
| `CALL_TIMEOUT_MS` | 200 | Abort call if it exceeds this (ms) |
| `CB_FAILURE_THRESHOLD` | 3 | Failures before circuit opens |
| `CB_RECOVERY_TIMEOUT_S` | 5.0 | Seconds before circuit tries Half-Open |

## LiteLLM reference (for production use)

The mock providers in this lab simulate what LiteLLM's Router does in production:

```python
from litellm import Router

router = Router(
    model_list=[
        {"model_name": "primary", "litellm_params": {"model": "claude-haiku-4-5", "api_key": "..."}},
        {"model_name": "secondary", "litellm_params": {"model": "gpt-5-mini", "api_key": "..."}},
    ],
    num_retries=3,
    timeout=30,
    fallbacks=[{"primary": ["secondary"]}],
    allowed_fails=3,
    cooldown_time=30,
)
response = router.completion(model="primary", messages=[{"role": "user", "content": question}])
```

This lab builds the same logic from scratch so you understand what the router is doing internally.
