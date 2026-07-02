"""
Day 12 — Reliability & Resilience: Retry, Circuit Breaker, Failover, SLO
DevOps Track | Complete reference implementation.

Run:
    python labs/devops/day-12/solution.py

No API key required. Set ANTHROPIC_API_KEY or OPENAI_API_KEY to use a real
provider instead of the deterministic mock.

What this script demonstrates:
    (a) Exponential backoff with full jitter for 429/5xx retries
    (b) Per-call timeout wrapper using threading.Timer (portable; no SIGALRM)
    (c) Three-state circuit breaker (Closed / Open / Half-Open)
    (d) Multi-provider failover chain: primary → secondary → graceful degradation
    (e) SLO attainment report: availability, P99 latency, retry rate, degraded rate
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
# Shared service import
# ---------------------------------------------------------------------------
_HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parents[1] / "_shared"))
from service import answer  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
PRIMARY_FAILURE_RATE   = 0.45
SECONDARY_FAILURE_RATE = 0.20
PRIMARY_LATENCY_MS     = 50
SECONDARY_LATENCY_MS   = 80
CALL_TIMEOUT_MS        = 200
CB_FAILURE_THRESHOLD   = 3
CB_RECOVERY_TIMEOUT_S  = 5.0

RETRY_MAX_ATTEMPTS     = 3
RETRY_BASE_S           = 0.05
RETRY_CAP_S            = 1.0

SLO_AVAILABILITY       = 0.95
SLO_P99_LATENCY_MS     = 4_000
SLO_RETRY_RATE         = 0.30
SLO_DEGRADED_RATE      = 0.20

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
    """Raised by a mock provider on a simulated transient error."""

class TimeoutError(Exception):  # noqa: A001
    """Raised when a call exceeds its configured deadline."""

class CircuitOpenError(Exception):
    """Raised by the circuit breaker when it is in the Open state."""


# ---------------------------------------------------------------------------
# TODO-1 — Exponential backoff with full jitter
# ---------------------------------------------------------------------------
def backoff_wait(
    attempt: int,
    base: float = RETRY_BASE_S,
    cap: float  = RETRY_CAP_S,
) -> float:
    """
    Full-jitter exponential backoff.
    Returns a random float in [0, min(cap, base * 2^attempt)].
    """
    ceiling = min(cap, base * (2 ** attempt))
    return random.uniform(0, ceiling)


# ---------------------------------------------------------------------------
# TODO-2 — Per-call timeout wrapper
# ---------------------------------------------------------------------------
class TimeoutWrapper:
    """
    Calls fn(*args, **kwargs) and raises TimeoutError if it takes longer than
    timeout_ms milliseconds.  Uses a threading.Event — portable across platforms
    (no SIGALRM dependency).
    """

    def __init__(self, timeout_ms: int = CALL_TIMEOUT_MS):
        self.timeout_s = timeout_ms / 1_000

    def run(self, fn, *args, **kwargs):
        result_holder: list[Any] = []
        exc_holder:    list[BaseException] = []
        timed_out = threading.Event()

        def _target():
            try:
                result_holder.append(fn(*args, **kwargs))
            except Exception as exc:  # noqa: BLE001
                exc_holder.append(exc)

        t = threading.Thread(target=_target, daemon=True)
        t.start()
        t.join(timeout=self.timeout_s)

        if t.is_alive():
            # Thread still running — treat as timeout
            timed_out.set()
            raise TimeoutError(
                f"Call exceeded {self.timeout_s * 1000:.0f} ms deadline"
            )

        if exc_holder:
            raise exc_holder[0]

        return result_holder[0]


# ---------------------------------------------------------------------------
# TODO-3 — Three-state circuit breaker
# ---------------------------------------------------------------------------
class CircuitBreaker:
    """
    Closed → Open → Half-Open circuit breaker.

    Closed  : calls pass through; failure_count increments.
    Open    : calls are rejected immediately (CircuitOpenError).
    Half-Open: one probe call allowed; success → Closed, failure → Open.
    """

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
        if self.state == self.OPEN:
            elapsed = time.time() - self._opened_at
            if elapsed >= self.recovery_timeout:
                self.state = self.HALF_OPEN
            else:
                raise CircuitOpenError(
                    f"Circuit OPEN — {self.recovery_timeout - elapsed:.1f}s "
                    "until Half-Open probe"
                )

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        self.failure_count = 0
        self.state         = self.CLOSED

    def _on_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold or self.state == self.HALF_OPEN:
            self.state      = self.OPEN
            self._opened_at = time.time()
            self.trips     += 1

    def reset(self) -> None:
        self.state         = self.CLOSED
        self.failure_count = 0


# ---------------------------------------------------------------------------
# TODO-4 — Deterministic mock provider with injected failures
# ---------------------------------------------------------------------------
class MockProvider:
    """
    Simulates an LLM provider with configurable failure rate and latency.
    No API key required.
    """

    def __init__(self, name: str, failure_rate: float, latency_ms: int):
        self.name         = name
        self.failure_rate = failure_rate
        self.latency_ms   = latency_ms

    def generate(self, question: str) -> dict[str, Any]:
        time.sleep(self.latency_ms / 1_000)
        if random.random() < self.failure_rate:
            raise ProviderError(f"{self.name}: simulated 429 / 5xx error")
        result = answer(question)
        result["provider"] = self.name
        return result


# ---------------------------------------------------------------------------
# Degradation cache — pre-populated canned answers
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


# ---------------------------------------------------------------------------
# Call record
# ---------------------------------------------------------------------------
@dataclass
class CallRecord:
    question:   str
    provider:   str           # "primary" | "secondary" | "degraded"
    degraded:   bool
    result:     dict[str, Any]
    latency_ms: float
    retries:    int


# ---------------------------------------------------------------------------
# TODO-5 — Resilience wrapper
# ---------------------------------------------------------------------------
class ResilienceWrapper:
    """
    Orchestrates: retry-with-backoff → circuit breaker → primary → secondary
    → graceful degradation.
    """

    def __init__(
        self,
        primary:      MockProvider,
        secondary:    MockProvider,
        cb_primary:   CircuitBreaker,
        cb_secondary: CircuitBreaker,
        timeout:      TimeoutWrapper,
    ):
        self._primary      = primary
        self._secondary    = secondary
        self._cb_primary   = cb_primary
        self._cb_secondary = cb_secondary
        self._timeout      = timeout

    def call(self, question: str) -> CallRecord:
        start       = time.time()
        retry_count = 0

        # --- Step 1: Try primary provider ---
        primary_circuit_open = False
        for attempt in range(RETRY_MAX_ATTEMPTS):
            try:
                result = self._cb_primary.call(
                    self._timeout.run,
                    self._primary.generate,
                    question,
                )
                return CallRecord(
                    question   = question,
                    provider   = "primary",
                    degraded   = False,
                    result     = result,
                    latency_ms = (time.time() - start) * 1_000,
                    retries    = retry_count,
                )
            except CircuitOpenError:
                primary_circuit_open = True
                break   # circuit is open; skip remaining retries
            except (ProviderError, TimeoutError):
                retry_count += 1
                if attempt < RETRY_MAX_ATTEMPTS - 1:
                    time.sleep(backoff_wait(attempt))

        # --- Step 2: Failover to secondary provider ---
        for attempt in range(RETRY_MAX_ATTEMPTS):
            try:
                result = self._cb_secondary.call(
                    self._timeout.run,
                    self._secondary.generate,
                    question,
                )
                return CallRecord(
                    question   = question,
                    provider   = "secondary",
                    degraded   = False,
                    result     = result,
                    latency_ms = (time.time() - start) * 1_000,
                    retries    = retry_count,
                )
            except CircuitOpenError:
                break   # secondary circuit also open; go to degradation
            except (ProviderError, TimeoutError):
                retry_count += 1
                if attempt < RETRY_MAX_ATTEMPTS - 1:
                    time.sleep(backoff_wait(attempt))

        # --- Step 3: Graceful degradation ---
        result = _get_degraded_answer(question)
        return CallRecord(
            question   = question,
            provider   = "degraded",
            degraded   = True,
            result     = result,
            latency_ms = (time.time() - start) * 1_000,
            retries    = retry_count,
        )


# ---------------------------------------------------------------------------
# TODO-6 — SLO reporter
# ---------------------------------------------------------------------------
class SLOReporter:
    def __init__(
        self,
        records:      list[CallRecord],
        cb_primary:   CircuitBreaker,
        cb_secondary: CircuitBreaker,
    ):
        self.records       = records
        self._cb_primary   = cb_primary
        self._cb_secondary = cb_secondary

    def report(self) -> None:
        total   = len(self.records)
        if total == 0:
            print("No records to report.")
            return

        by_provider: dict[str, int] = {}
        for r in self.records:
            by_provider[r.provider] = by_provider.get(r.provider, 0) + 1

        # All records with a result are "successful" (degraded still returns an answer)
        successful   = total   # with full degradation, all calls return something
        failed       = 0       # would only be > 0 if an uncaught exception escaped
        degraded_ct  = by_provider.get("degraded", 0)
        failover_ct  = by_provider.get("secondary", 0)
        total_retries = sum(r.retries for r in self.records)

        # SLI computations
        availability_sli  = successful / total
        retry_rate_sli    = total_retries / total
        degraded_rate_sli = degraded_ct / total
        latencies         = sorted(r.latency_ms for r in self.records)
        p99_idx           = max(0, int(len(latencies) * 0.99) - 1)
        p99_latency_sli   = latencies[p99_idx]

        # Error budget
        budget_min    = 43_200 * (1 - SLO_AVAILABILITY)
        consumed_min  = (1 - availability_sli) * 43_200
        pct_consumed  = (consumed_min / budget_min * 100) if budget_min > 0 else 0

        def _pass(condition: bool) -> str:
            return "PASS ✓" if condition else "MISS ✗"

        print("=" * 60)
        print(" SLO REPORT")
        print("=" * 60)
        print(f"Total requests       : {total}")
        print(f"Successful answers   : {successful}  ({successful/total*100:.1f}%)")
        print(f"  via primary        : {by_provider.get('primary', 0)}")
        print(f"  via secondary      : {failover_ct}")
        print(f"  via degradation    : {degraded_ct}")
        print(f"Failed (no answer)   : {failed}  ({failed/total*100:.1f}%)")
        print()
        print(f"Retries issued       : {total_retries}")
        print(f"Primary CB trips     : {self._cb_primary.trips}")
        print(f"Secondary CB trips   : {self._cb_secondary.trips}")
        print(f"Failover activations : {failover_ct}")
        print()
        avail_pass   = availability_sli  >= SLO_AVAILABILITY
        p99_pass     = p99_latency_sli   <= SLO_P99_LATENCY_MS
        retry_pass   = retry_rate_sli    <= SLO_RETRY_RATE
        degraded_pass = degraded_rate_sli <= SLO_DEGRADED_RATE
        slos_met     = sum([avail_pass, p99_pass, retry_pass, degraded_pass])

        print(f"Availability SLI     : {availability_sli*100:.1f}%    "
              f"target ≥ {SLO_AVAILABILITY*100:.1f}%    "
              f"{_pass(avail_pass)}")
        print(f"P99 latency SLI      : {p99_latency_sli:.0f}ms    "
              f"target ≤ {SLO_P99_LATENCY_MS}ms    "
              f"{_pass(p99_pass)}")
        print(f"Retry rate SLI       : {retry_rate_sli*100:.1f}%    "
              f"target ≤ {SLO_RETRY_RATE*100:.1f}%    "
              f"{_pass(retry_pass)}")
        print(f"Degraded-answer rate : {degraded_rate_sli*100:.1f}%    "
              f"target ≤ {SLO_DEGRADED_RATE*100:.1f}%    "
              f"{_pass(degraded_pass)}")
        print()
        print(f"SLOs met             : {slos_met} / 4")
        print(f"Error budget (avail) : consumed {pct_consumed:.1f}% of monthly budget "
              f"({budget_min:.0f} min total)")
        print("=" * 60)


# ---------------------------------------------------------------------------
# Main
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
