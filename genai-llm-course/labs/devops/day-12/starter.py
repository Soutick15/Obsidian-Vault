"""
Day 12 — Reliability & Resilience: Retry, Circuit Breaker, Failover, SLO
DevOps Track | Starter file — work through the TODO markers in order.

Run:
    python labs/devops/day-12/starter.py

No API key required. All provider calls use deterministic mocks with injected
failures. Set ANTHROPIC_API_KEY or OPENAI_API_KEY to use a real provider.

Shared service import (do not modify):
    sys.path.insert(...) wires labs/devops/_shared/ onto the path so that
    `from service import answer` works regardless of your cwd.
"""

from __future__ import annotations

import pathlib
import random
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Shared service import — do not modify
# ---------------------------------------------------------------------------
_HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parents[1] / "_shared"))
from service import answer  # noqa: E402  (import after sys.path mutation)

# ---------------------------------------------------------------------------
# Configuration constants — adjust to explore failure modes
# ---------------------------------------------------------------------------
PRIMARY_FAILURE_RATE   = 0.45   # fraction of primary calls that fail (429/5xx)
SECONDARY_FAILURE_RATE = 0.20   # fraction of secondary calls that fail
PRIMARY_LATENCY_MS     = 50     # base latency per primary call (ms)
SECONDARY_LATENCY_MS   = 80     # base latency per secondary call (ms)
CALL_TIMEOUT_MS        = 200    # abort call if it exceeds this (ms)
CB_FAILURE_THRESHOLD   = 3      # failures before circuit opens
CB_RECOVERY_TIMEOUT_S  = 5.0   # seconds before circuit tries Half-Open

RETRY_MAX_ATTEMPTS     = 3
RETRY_BASE_S           = 0.05   # base wait in seconds (small for fast lab run)
RETRY_CAP_S            = 1.0    # maximum wait cap in seconds

# SLO targets
SLO_AVAILABILITY       = 0.95   # ≥ 95% of requests return an answer
SLO_P99_LATENCY_MS     = 4_000  # P99 latency ≤ 4 000 ms
SLO_RETRY_RATE         = 0.30   # retry fraction ≤ 30%
SLO_DEGRADED_RATE      = 0.20   # degraded-answer fraction ≤ 20%

# ---------------------------------------------------------------------------
# Workload
# ---------------------------------------------------------------------------
WORKLOAD = [
    "How many days of annual leave do I get?",
    "What is the dental benefit for dependants?",
    "How do I submit an expense report?",
    "When does my probation period end?",
    "What is the parental leave policy?",
    "How do I request a remote work arrangement?",
    "What is the pension contribution matching?",
    "How do I report a workplace incident?",
    "What are the core working hours?",
    "How do I access the learning and development budget?",
    # Repeats and paraphrases to exercise cache hits in degradation
    "How many annual leave days am I entitled to?",
    "Tell me about dental coverage for family members.",
    "How many vacation days per year?",
    "What is the process for submitting expenses?",
    "Explain the remote working policy.",
    "What pension matching does the company offer?",
    "How do I report a safety incident?",
    "What hours must I be at my desk?",
    "Is there a training budget?",
    "What is the vision benefit?",
]

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class ProviderError(Exception):
    """Raised by a provider on a transient error (429, 5xx)."""

class TimeoutError(Exception):  # noqa: A001
    """Raised when a call exceeds its deadline."""

class CircuitOpenError(Exception):
    """Raised when the circuit breaker is Open and rejects a call."""


# ===========================================================================
# TODO-1: backoff_wait
# ===========================================================================
# Implement exponential backoff with FULL JITTER.
#
# Formula (full jitter variant):
#     wait = random.uniform(0, min(cap, base * 2^attempt))
#
# Parameters:
#   attempt    : int  — zero-indexed attempt number (0 = first retry)
#   base       : float — base wait in seconds (default RETRY_BASE_S)
#   cap        : float — maximum wait in seconds (default RETRY_CAP_S)
#
# Returns:
#   float — seconds to wait before the next attempt
#
# Example values (non-deterministic, but bounded):
#   attempt=0 → uniform(0, 0.05)
#   attempt=1 → uniform(0, 0.10)
#   attempt=2 → uniform(0, 0.20)
#   attempt=3 → uniform(0, 0.40)   # capped at cap if base*2^attempt > cap
#
# Do NOT use time.sleep() here — just return the wait duration.
# ===========================================================================

def backoff_wait(
    attempt: int,
    base: float = RETRY_BASE_S,
    cap: float = RETRY_CAP_S,
) -> float:
    # === TODO-1: implement full-jitter exponential backoff ===
    raise NotImplementedError("TODO-1: implement backoff_wait()")


# ===========================================================================
# TODO-2: TimeoutWrapper
# ===========================================================================
# Implement a per-call timeout using threading.Timer.
#
# The `run(fn, *args, **kwargs)` method must:
#   1. Start a threading.Timer that sets a flag after `timeout_s` seconds.
#   2. Call fn(*args, **kwargs) in the current thread.
#   3. Cancel the timer if fn returns before the timeout.
#   4. If the timer fires before fn returns, raise TimeoutError.
#
# Implementation hint:
#   - Use a threading.Event to signal timeout.
#   - After fn() returns, check whether the event was set; if so, discard the
#     result and raise TimeoutError (the call was too slow even if it "returned").
#   - Alternatively, raise from the timer thread is unreliable — use the event
#     check pattern instead.
#
# The constructor takes:
#   timeout_ms : int — timeout in milliseconds
# ===========================================================================

class TimeoutWrapper:
    def __init__(self, timeout_ms: int = CALL_TIMEOUT_MS):
        self.timeout_s = timeout_ms / 1_000

    def run(self, fn, *args, **kwargs):
        # === TODO-2: implement timeout wrapper ===
        raise NotImplementedError("TODO-2: implement TimeoutWrapper.run()")


# ===========================================================================
# TODO-3: CircuitBreaker
# ===========================================================================
# Implement a three-state circuit breaker: CLOSED → OPEN → HALF_OPEN.
#
# State machine:
#   CLOSED   : all calls pass through; failure_count increments on each failure.
#              → OPEN when failure_count >= failure_threshold.
#
#   OPEN     : all calls raise CircuitOpenError immediately (no network call).
#              → HALF_OPEN when time.time() - _opened_at >= recovery_timeout.
#
#   HALF_OPEN: exactly ONE probe call is allowed through.
#              → CLOSED on success  (reset failure_count to 0).
#              → OPEN   on failure  (record new opened_at; increment trips).
#
# The `call(fn, *args, **kwargs)` method:
#   1. If OPEN: check whether recovery_timeout has elapsed.
#      - If yes, transition to HALF_OPEN.
#      - If no,  raise CircuitOpenError.
#   2. Attempt fn(*args, **kwargs).
#   3. On success: call _on_success() and return the result.
#   4. On exception: call _on_failure() and re-raise.
#
# Track:
#   self.state          : str   — current state string
#   self.failure_count  : int   — cumulative failures since last close
#   self.trips          : int   — total times circuit has tripped to OPEN
#
# Provide a `reset()` method that sets state=CLOSED, failure_count=0.
# ===========================================================================

class CircuitBreaker:
    CLOSED    = "closed"
    OPEN      = "open"
    HALF_OPEN = "half-open"

    def __init__(
        self,
        failure_threshold: int   = CB_FAILURE_THRESHOLD,
        recovery_timeout:  float = CB_RECOVERY_TIMEOUT_S,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout
        self.state             = self.CLOSED
        self.failure_count     = 0
        self.trips             = 0
        self._opened_at: float = 0.0

    def call(self, fn, *args, **kwargs):
        # === TODO-3: implement circuit breaker call() ===
        raise NotImplementedError("TODO-3: implement CircuitBreaker.call()")

    def _on_success(self) -> None:
        # === TODO-3: implement _on_success() ===
        raise NotImplementedError("TODO-3: implement _on_success()")

    def _on_failure(self) -> None:
        # === TODO-3: implement _on_failure() ===
        raise NotImplementedError("TODO-3: implement _on_failure()")

    def reset(self) -> None:
        self.state         = self.CLOSED
        self.failure_count = 0


# ===========================================================================
# TODO-4: MockProvider
# ===========================================================================
# Implement a deterministic mock LLM provider with configurable failure injection.
#
# `generate(question: str) -> dict` must:
#   1. Sleep for `latency_ms / 1000` seconds to simulate network latency.
#   2. With probability `failure_rate`, raise ProviderError(f"{name}: simulated 429").
#   3. Otherwise, call `answer(question)` from the shared service and return the dict.
#
# Constructor parameters:
#   name         : str   — provider name (e.g., "primary", "secondary")
#   failure_rate : float — probability [0, 1] of raising ProviderError on each call
#   latency_ms   : int   — fixed latency to inject (ms)
#
# Use random.random() < failure_rate for the failure check.
# Use the module-level `random` object (not a seeded one) so failures are
# non-deterministic across runs (realistic) but the overall distribution is
# controlled by failure_rate.
# ===========================================================================

class MockProvider:
    def __init__(self, name: str, failure_rate: float, latency_ms: int):
        self.name         = name
        self.failure_rate = failure_rate
        self.latency_ms   = latency_ms

    def generate(self, question: str) -> dict[str, Any]:
        # === TODO-4: implement mock provider with injected failure + latency ===
        raise NotImplementedError("TODO-4: implement MockProvider.generate()")


# ---------------------------------------------------------------------------
# Degradation cache — pre-populated with canned answers
# ---------------------------------------------------------------------------
_DEGRADATION_CACHE: dict[str, str] = {
    "default": (
        "Our LLM service is temporarily unavailable. "
        "For HR questions, please contact hr@acme.example or "
        "consult the employee handbook at handbook.acme.example."
    ),
}

def _get_degraded_answer(question: str) -> dict[str, Any]:
    """Return a cached or canned answer when all providers are unavailable."""
    cached = _DEGRADATION_CACHE.get(question.lower().strip())
    answer_text = cached if cached else _DEGRADATION_CACHE["default"]
    return {
        "answer":   answer_text,
        "sources":  [],
        "contexts": [],
        "mock":     True,
        "degraded": True,
    }


# ===========================================================================
# TODO-5: ResilienceWrapper
# ===========================================================================
# Implement the full resilience call() method.
#
# `call(question: str) -> CallRecord` must:
#   1. Record wall-clock start time.
#   2. Try the PRIMARY provider:
#      a. For each attempt in range(RETRY_MAX_ATTEMPTS):
#         i.  Try: self._cb_primary.call(self._timeout.run, self._primary.generate, question)
#         ii. On success: return a CallRecord(provider="primary", degraded=False, ...).
#         iii.On CircuitOpenError: break out of the retry loop immediately (go to step 3).
#         iv. On ProviderError or TimeoutError: increment retry_count; if not last attempt,
#             sleep backoff_wait(attempt); continue.
#   3. Try the SECONDARY provider:
#      a. For each attempt in range(RETRY_MAX_ATTEMPTS):
#         i.  Try: self._cb_secondary.call(self._timeout.run, self._secondary.generate, question)
#         ii. On success: return a CallRecord(provider="secondary", degraded=False, ...).
#         iii.On CircuitOpenError: break immediately (go to step 4).
#         iv. On ProviderError or TimeoutError: increment retry_count; if not last attempt,
#             sleep backoff_wait(attempt); continue.
#   4. Return graceful degradation:
#      result = _get_degraded_answer(question)
#      return CallRecord(provider="degraded", degraded=True, result=result, ...)
#
# All paths must populate CallRecord.latency_ms with (time.time() - start) * 1000.
# CallRecord.retries must be the total number of failed attempts across both providers.
#
# The constructor (provided — do not modify) wires up the components.
# ===========================================================================

@dataclass
class CallRecord:
    question:   str
    provider:   str          # "primary" | "secondary" | "degraded"
    degraded:   bool
    result:     dict[str, Any]
    latency_ms: float
    retries:    int


class ResilienceWrapper:
    def __init__(
        self,
        primary:   MockProvider,
        secondary: MockProvider,
        cb_primary:   CircuitBreaker,
        cb_secondary: CircuitBreaker,
        timeout:   TimeoutWrapper,
    ):
        self._primary      = primary
        self._secondary    = secondary
        self._cb_primary   = cb_primary
        self._cb_secondary = cb_secondary
        self._timeout      = timeout

    def call(self, question: str) -> CallRecord:
        # === TODO-5: implement the full retry → CB → primary → secondary → degradation chain ===
        raise NotImplementedError("TODO-5: implement ResilienceWrapper.call()")


# ===========================================================================
# TODO-6: SLOReporter
# ===========================================================================
# Implement the report() method that computes and prints SLI attainment.
#
# Given self.records: list[CallRecord], compute and print:
#
#   1. Total requests, successful (non-failed), failed count and percentage.
#   2. Breakdown of successes by provider ("primary", "secondary", "degraded").
#      Note: "degraded" answers count as successful (an answer was returned).
#      "failed" means no answer at all — this happens only if ResilienceWrapper
#      raises an uncaught exception (unlikely with full degradation implemented).
#   3. Total retries issued.
#   4. Primary circuit breaker trip count (self._cb_primary.trips).
#   5. Secondary circuit breaker trip count (self._cb_secondary.trips).
#   6. Count of failover activations (records where provider == "secondary").
#
#   SLI computations:
#     availability_sli  = len(successful) / total
#     retry_rate_sli    = total_retries / total          (retries per request)
#     degraded_rate_sli = len(degraded records) / total
#     p99_latency_sli   = sorted latencies at 99th percentile
#
#   For each SLI, print the value, the target, and PASS ✓ or MISS ✗.
#
#   Monthly error budget for availability:
#     budget_min = 43_200 * (1 - SLO_AVAILABILITY)
#     consumed_min = (1 - availability_sli) * 43_200
#     print consumed as percentage of budget.
#
# The constructor stores records and circuit breaker references (provided).
# ===========================================================================

class SLOReporter:
    def __init__(
        self,
        records:       list[CallRecord],
        cb_primary:    CircuitBreaker,
        cb_secondary:  CircuitBreaker,
    ):
        self.records      = records
        self._cb_primary  = cb_primary
        self._cb_secondary = cb_secondary

    def report(self) -> None:
        # === TODO-6: implement SLO report ===
        raise NotImplementedError("TODO-6: implement SLOReporter.report()")


# ---------------------------------------------------------------------------
# Main workload runner — do not modify
# ---------------------------------------------------------------------------
def run_workload() -> None:
    primary   = MockProvider("primary",   PRIMARY_FAILURE_RATE,   PRIMARY_LATENCY_MS)
    secondary = MockProvider("secondary", SECONDARY_FAILURE_RATE, SECONDARY_LATENCY_MS)
    cb_p      = CircuitBreaker(CB_FAILURE_THRESHOLD, CB_RECOVERY_TIMEOUT_S)
    cb_s      = CircuitBreaker(CB_FAILURE_THRESHOLD, CB_RECOVERY_TIMEOUT_S)
    tmout     = TimeoutWrapper(CALL_TIMEOUT_MS)
    wrapper   = ResilienceWrapper(primary, secondary, cb_p, cb_s, tmout)
    reporter  = SLOReporter([], cb_p, cb_s)

    print("=" * 60)
    print(" Day 12 — Resilience Wrapper: Workload Run")
    print("=" * 60)
    print(f"\nPrimary provider config : failure_rate={PRIMARY_FAILURE_RATE}, "
          f"latency_ms={PRIMARY_LATENCY_MS}, timeout_ms={CALL_TIMEOUT_MS}")
    print(f"Secondary provider config: failure_rate={SECONDARY_FAILURE_RATE}, "
          f"latency_ms={SECONDARY_LATENCY_MS}, timeout_ms={CALL_TIMEOUT_MS}")
    print(f"Circuit breaker         : threshold={CB_FAILURE_THRESHOLD}, "
          f"recovery={CB_RECOVERY_TIMEOUT_S}s")
    print(f"Retry policy            : max_attempts={RETRY_MAX_ATTEMPTS}, "
          f"base={RETRY_BASE_S}s, cap={RETRY_CAP_S}s")
    print(f"\nRunning {len(WORKLOAD)} requests...\n")

    for i, question in enumerate(WORKLOAD, start=1):
        rec = wrapper.call(question)
        reporter.records.append(rec)
        status = "DEGRADED" if rec.degraded else "SUCCESS "
        print(
            f"  R{i:02d}  {status}  {rec.provider:<10}  "
            f"retries={rec.retries}  lat={rec.latency_ms:5.0f}ms  "
            f'"{question[:50]}"'
        )

    print()
    reporter.report()


if __name__ == "__main__":
    run_workload()
