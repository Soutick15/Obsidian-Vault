# Day 12 — Reliability & Resilience for LLM Systems

**Track:** DevOps | **Day:** 12 of 15 | **Prerequisites:** Days 6–11

---

## 1. Objectives

By the end of this day you will be able to:

- Explain why LLM provider APIs fail differently from databases or internal microservices, and why standard retry logic is insufficient without jitter.
- Implement **exponential backoff with jitter** to handle 429 (rate-limit) and 5xx errors without creating thundering-herd storms.
- Configure **per-request timeouts** to prevent slow providers from blocking your event loop and exhausting connection pools.
- Model a **circuit breaker** with its three states (Closed → Open → Half-Open) and explain the transition conditions for each.
- Build a **multi-provider failover chain** (primary → secondary) and a **graceful degradation** final layer (cached answer or canned response).
- Define **idempotency** for LLM calls and explain why it matters for safe retries.
- Write **SLO/SLI** specifications for an LLM service (availability, latency), compute error budgets, and explain how those budgets drive on-call and alerting thresholds.

---

## 2. Concept Reading

### 2.1 Why LLM APIs Fail Differently

Traditional backend services (databases, internal APIs) fail in familiar ways: network partition, overload, or crash. LLM provider APIs introduce a distinct failure class: **quota-scarcity errors**. Because inference is GPU-expensive, providers aggressively throttle:

| HTTP Status | Meaning | Correct Response |
|---|---|---|
| `429 Too Many Requests` | Rate limit or quota exhausted | Exponential backoff; honour `Retry-After` header |
| `503 Service Unavailable` | Provider overloaded | Retry with backoff; consider failover |
| `504 Gateway Timeout` | Provider inference took too long | Retry or failover; do not keep blocking |
| `400 Bad Request` | Malformed payload / token-limit exceeded | Fix the request; do **not** retry |
| `401/403` | Auth error | Fix credentials; do **not** retry |

The critical DevOps rule: **retry only on transient errors (429, 5xx, timeout).** Retrying a 400 or 401 just multiplies a bad request.

**Why "thundering herd" happens:** If all workers that hit a 429 retry at the same fixed interval (e.g., exactly 1 s), they all arrive at the provider simultaneously and generate a second 429 wave. The total time to clear the backlog grows linearly with retry count instead of dissipating. Exponential backoff + jitter breaks the synchronisation.

---

### 2.2 Exponential Backoff with Jitter

The canonical retry formula uses **full jitter** (preferred when many workers retry concurrently, as is typical with shared LLM provider rate limits):

```
wait = random.uniform(0, min(cap, base * 2^attempt))
```

| Parameter | Typical value | Role |
|---|---|---|
| `base` | 0.5 s | Initial wait floor |
| `2^attempt` | grows: 1, 2, 4, 8… | Exponential growth |
| `cap` | 30 s | Maximum wait ceiling |
| `max_attempts` | 3–5 | Hard stop to prevent infinite loops |

Full jitter picks a random value anywhere between 0 and the exponential cap, spreading load uniformly across time and preventing workers from synchronising on the same retry moment.

```python
import random, time

def backoff_wait(attempt: int, base: float = 0.5, cap: float = 30.0) -> float:
    """Full-jitter exponential backoff (recommended for concurrent workers)."""
    return random.uniform(0, min(cap, base * (2 ** attempt)))

for attempt in range(max_attempts):
    try:
        result = call_provider()
        break
    except RateLimitError:
        if attempt == max_attempts - 1:
            raise
        time.sleep(backoff_wait(attempt))
```

**Additive jitter variant** (simpler, acceptable for low-concurrency scenarios): add a fixed random fraction to the deterministic wait — `wait = min(cap, base * 2^attempt) + random.uniform(0, wait * 0.25)`. This still desynchronises retries but provides a higher average wait floor than full jitter.

**Honour the `Retry-After` header:** When a 429 response includes a `Retry-After` header, use `max(Retry-After, backoff_wait(attempt))` so you never retry before the provider says it's ready.

---

### 2.3 Timeouts

Every network call to an LLM provider must have two timeout layers:

| Timeout type | What it guards | Typical value |
|---|---|---|
| **Connect timeout** | Time to establish TCP + TLS | 5 s |
| **Read timeout** | Time from request sent to first byte of response | 30–60 s |
| **Total / wall-clock timeout** | End-to-end deadline including all retries | 90–120 s |

Without a read timeout, a slow provider holds your thread open indefinitely. Under load, this exhausts your connection pool and cascades into a full service outage.

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds: float):
    def _handler(signum, frame):
        raise TimeoutError(f"Call exceeded {seconds}s deadline")
    old = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)
```

> **Lab note:** The lab uses `threading.Timer` for portability across platforms (SIGALRM is Unix-only). In production Python async services, use `asyncio.wait_for`.

---

### 2.4 Circuit Breaker Pattern

A circuit breaker wraps a potentially-failing call and **stops sending requests** when the downstream is clearly unhealthy — rather than hammering it with retries and compounding the failure.

```
         ┌──────────────────────────────────────────┐
         │              CLOSED (normal)             │
         │  All calls pass through.                 │
         │  Failure counter increments on error.   │
         └────────────┬─────────────────────────────┘
                      │  failures ≥ threshold
                      ▼
         ┌──────────────────────────────────────────┐
         │               OPEN (tripped)             │
         │  All calls fail fast (no network call).  │
         │  Recovery timer starts.                  │
         └────────────┬─────────────────────────────┘
                      │  recovery_timeout expires
                      ▼
         ┌──────────────────────────────────────────┐
         │            HALF-OPEN (probing)           │
         │  One probe call is allowed through.      │
         │  Success → CLOSED. Failure → OPEN again. │
         └──────────────────────────────────────────┘
```

**State transitions:**

| From | To | Condition |
|---|---|---|
| Closed | Open | `failure_count >= failure_threshold` within the window |
| Open | Half-Open | `time.time() - opened_at >= recovery_timeout` |
| Half-Open | Closed | Probe call succeeds |
| Half-Open | Open | Probe call fails |

**Tuning parameters:**

| Parameter | Typical value | Effect of getting it wrong |
|---|---|---|
| `failure_threshold` | 3–5 | Too low → false trips; too high → stays closed during real outage |
| `recovery_timeout` | 30–60 s | Too short → yo-yo between Open/Half-Open; too long → slow recovery |
| Window type | Rolling 60 s | A cumulative window can trip on historical errors long past |

```python
import time

class CircuitBreaker:
    CLOSED, OPEN, HALF_OPEN = "closed", "open", "half-open"

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.state = self.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._opened_at: float = 0.0

    def call(self, fn, *args, **kwargs):
        if self.state == self.OPEN:
            if time.time() - self._opened_at >= self.recovery_timeout:
                self.state = self.HALF_OPEN
            else:
                raise CircuitOpenError("Circuit is OPEN — call rejected")

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = self.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold or self.state == self.HALF_OPEN:
            self.state = self.OPEN
            self._opened_at = time.time()
```

---

### 2.5 Multi-Provider Failover and Load Balancing

A single-provider dependency is a single point of failure. The standard pattern is a **failover chain**:

```
Request → Primary Provider (e.g., Anthropic)
              │ 429 / 5xx / timeout after retries exhausted
              ▼
         Secondary Provider (e.g., OpenAI / Azure)
              │ also fails
              ▼
         Graceful Degradation (cache, smaller model, canned response)
```

**Failover vs. load balancing:**

| Strategy | Description | When to use |
|---|---|---|
| **Active-passive failover** | All traffic → primary; switch to secondary on failure | Cost-optimal; secondary is cold |
| **Active-active load balancing** | Traffic split across providers simultaneously | Eliminates cold-start; higher cost |
| **Latency-based routing** | Route to whichever provider has lower current p50 | Best for interactive workloads |
| **Cost-based routing** | Route cheapest-first; fall back on quota exhaustion | FinOps-optimised |

**Provider client abstraction (interface pattern):**

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, question: str) -> str: ...

class PrimaryProvider(LLMProvider):
    def generate(self, question: str) -> str:
        # calls Anthropic / OpenAI / etc.
        ...

class SecondaryProvider(LLMProvider):
    def generate(self, question: str) -> str:
        # calls fallback provider
        ...
```

Abstracting behind an interface means your failover orchestrator is provider-neutral.

---

### 2.6 Graceful Degradation

When all providers are unavailable, a useful response is better than a 500 error. The degradation hierarchy (from most to least useful):

1. **Stale cache hit** — return the last valid answer for this question, with a staleness warning.
2. **Smaller/local model** — route to a much cheaper, lower-quality model that is less likely to be rate-limited.
3. **Canned response** — return a pre-written "our LLM is temporarily unavailable; here is a general answer or contact HR" message.
4. **Transparent failure** — return an HTTP 503 with `Retry-After` so the client knows when to try again.

The key principle: **degrade gracefully, never silently.** Always include a `degraded: true` flag in the response so downstream systems and dashboards can distinguish degraded answers from normal ones.

---

### 2.7 Idempotency for Safe Retries

A retry is only safe if re-sending the same request produces the same observable outcome (or is a no-op for side effects). For LLM read-only Q&A, retries are naturally idempotent — asking the same question twice produces a similar answer. For LLM calls that **trigger actions** (send email, create ticket), retries are dangerous without an idempotency key.

**Idempotency key pattern:**

```python
import hashlib

def make_idempotency_key(user_id: str, question: str, timestamp_bucket: int) -> str:
    """Bucket by minute so the same question in the same minute gets one key."""
    payload = f"{user_id}:{question}:{timestamp_bucket}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]
```

Store idempotency keys in Redis with a TTL matching your retry window. Before executing an action, check if the key exists; if so, return the cached result instead of re-executing.

---

### 2.8 SLOs, SLIs, and Error Budgets for LLM Services

**Service Level Terminology:**

| Term | Definition | Example |
|---|---|---|
| **SLI** (Service Level Indicator) | A measurable metric of service behaviour | P99 latency of `/chat` endpoint |
| **SLO** (Service Level Objective) | A target value for an SLI | P99 latency ≤ 4 s, measured over 30 days |
| **SLA** (Service Level Agreement) | A contractual commitment based on one or more SLOs | "99.5% availability; penalty if breached" |
| **Error Budget** | `1 - SLO` expressed as allowable bad minutes/requests | 99.5% availability = 0.5% budget = ~216 min/month bad |

**LLM-specific SLIs (recommended set):**

| SLI | Measurement | Suggested target |
|---|---|---|
| **Availability** | Fraction of requests returning a non-5xx response | ≥ 99.5% |
| **P50 latency** | Median response time (including retries) | ≤ 1.5 s |
| **P99 latency** | 99th percentile response time | ≤ 4 s |
| **Degraded-answer rate** | Fraction of responses flagged `degraded: true` | ≤ 2% |
| **Retry rate** | Fraction of requests that required ≥ 1 retry | ≤ 5% |
| **Circuit-breaker trip rate** | Trips per hour | Alert at > 1/hr |

**Error budget calculation:**

```
monthly_minutes  = 30 * 24 * 60 = 43,200 min
availability_SLO = 99.5%
error_budget_min = 43,200 * (1 - 0.995) = 216 min
```

If you have consumed 80% of your error budget with 15 days remaining, you freeze non-critical deployments and increase on-call sensitivity.

**How error budgets drive operations:**

| Budget consumed | Action |
|---|---|
| < 50% | Normal operations; feature work proceeds |
| 50–80% | Increased monitoring cadence; reduce deploy frequency |
| 80–100% | Freeze non-critical changes; focus on reliability improvements |
| > 100% (breach) | Incident retrospective required; SLA penalties may apply |

**Alerting tie-in:** Set your alert threshold below the budget boundary. If the SLO is 99.5% availability, alert at 99.6% so you have time to act before the SLO is breached. Use burn-rate alerts (e.g., "consuming error budget at 5× the normal rate") rather than absolute-threshold alerts to catch fast-burning incidents early.

---

## 3. Hands-On Lab

**Location:** `labs/devops/day-12/`

**Goal:** Build a **resilience wrapper** around the shared `answer()` function that implements retry-with-backoff, a timeout, a circuit breaker, and multi-provider failover with graceful degradation. Run a workload against deterministic mock providers (configurable failure rate and latency injection) and report SLO attainment.

**Files:**
```
labs/devops/day-12/
├── README.md
├── requirements.txt
├── starter.py      ← work through TODO markers
└── solution.py     ← reference implementation (run to verify)
```

**Run (no API key needed):**
```bash
python labs/devops/day-12/solution.py
```

See `labs/devops/day-12/README.md` for full instructions and expected output.

---

## 4. Self-Check Quiz

**Q1.** A 429 response arrives with a `Retry-After: 8` header. Your exponential backoff formula computes a wait of 3 s for this attempt. What wait time should you actually use?

<details>
<summary>Show answer</summary>

8 seconds. The `Retry-After` header is a hard minimum set by the provider — the provider is telling you it will not accept your request before that time. Retrying at 3 s will produce another 429 immediately. The correct approach is `max(Retry-After_value, backoff_formula_value)` = max(8, 3) = 8 s. If the header value is very large (e.g., 3600 s), that is your cue to fail over to a secondary provider rather than waiting.

</details>

---

**Q2.** A circuit breaker is in the **Half-Open** state. Two threads both receive the go-ahead to probe simultaneously. The probe from thread A succeeds; the probe from thread B also succeeds. What should happen?

<details>
<summary>Show answer</summary>

The circuit breaker should transition to **Closed** after the first successful probe. The second success is redundant but harmless — it should confirm the Closed state rather than increment any counter or re-open. The important requirement is that a Half-Open circuit only allows **one** probe at a time. The classic implementation uses a lock or atomic compare-and-swap so that once thread A sends the probe, thread B falls back to the "fail fast" path until A's result is known. Allowing two simultaneous probes risks allowing two full calls through before deciding the circuit is healthy, which may be acceptable for read-only calls but dangerous for rate-limited providers.

</details>

---

**Q3.** What is the difference between a **timeout** and a **circuit breaker**, and why do you need both?

<details>
<summary>Show answer</summary>

A **timeout** is a per-call deadline: it aborts a single slow call after N seconds and returns an error to the caller. It solves the problem of an individual call hanging indefinitely. A **circuit breaker** is a stateful pattern that observes the history of calls: after enough failures accumulate, it stops sending calls to the downstream entirely (fail-fast) without even attempting the network call. You need both because: (1) a timeout without a circuit breaker means you still attempt every call and wait N seconds for each one during a sustained outage — your system is responsive but burning resources and latency on doomed calls; (2) a circuit breaker without a timeout means a single slow call can hold the breaker in an ambiguous state for a long time. Together they give you: fast individual call termination (timeout) and fast bulk rejection during outages (circuit breaker).

</details>

---

**Q4.** Your LLM service has an availability SLO of 99.5% per 30-day window. It is day 20, and you have had 180 minutes of downtime. Should you freeze deployments?

<details>
<summary>Show answer</summary>

Yes. The full 30-day error budget is 216 minutes (43,200 × 0.005). After 20 days, the time-proportional budget consumed should be (20/30) × 216 = 144 minutes. You have consumed 180 minutes — you are already over your prorated budget with 10 days remaining. Only 36 minutes remain in the total budget for the rest of the month, and at the current burn rate (180/20 = 9 min/day) you will breach the SLO in approximately 4 more days. Freezing non-critical deployments (which are a leading cause of incidents) is the correct response.

</details>

---

**Q5.** You are designing graceful degradation for an HR Q&A assistant. Rank these fallback options from most to least preferred, and justify the order: (a) return a stale cached answer with a warning, (b) return an HTTP 503 with no body, (c) return a canned "contact HR directly" message, (d) route to a local small model.

<details>
<summary>Show answer</summary>

Best to worst: **(a) stale cache → (d) local small model → (c) canned message → (b) 503 with no body.** Rationale: (a) A stale cache answer is usually still correct (HR policy changes infrequently) and maximally useful — include a `degraded: true` flag and a staleness timestamp so the user can judge whether to trust it. (d) A local small model (e.g., a quantised 7B model running on CPU) gives a real generated answer, though lower quality; it remains available when cloud providers are down. (c) A canned "contact HR" message tells the user what to do — it is helpful even though it is not specific. (b) A bare 503 with no body leaves the user with no course of action and no information — it is the worst option and should only be the fallback when the service is so broken that it cannot compose a response body.

</details>

---

**Q6.** Explain the "thundering herd" problem in the context of LLM API retries, and describe how full jitter solves it.

<details>
<summary>Show answer</summary>

When many workers (threads, processes, or pods) all receive a 429 simultaneously and all retry after the same fixed interval, they all arrive at the provider at the same moment — generating a second synchronised wave of 429s. This repeats with each retry, so recovery time grows linearly with the retry count rather than declining. Full jitter solves this by making each worker pick its wait time uniformly at random from [0, min(cap, base × 2^attempt)]. Workers now arrive at the provider at uniformly random times spread across the window rather than at one synchronised point. The provider sees a smooth ramp of traffic rather than a burst, and its per-second rate limit is never collectively exceeded. The cost is a higher *average* wait compared to the deterministic formula, but a far lower probability of a second 429 wave.

</details>

---

**Q7.** What makes an LLM call **not** idempotent, and what mechanism do you add to make retries safe in that case?

<details>
<summary>Show answer</summary>

An LLM call is not idempotent when it triggers a side effect that should happen exactly once: sending an email, creating a JIRA ticket, posting a Slack message, or charging a payment. If the call succeeds but the acknowledgement is lost (network failure after provider responds), the client retries and the action executes twice. The mechanism: assign an **idempotency key** to each logical operation before the first attempt. On retry, send the same key. The provider (or your own middleware) checks whether it has already executed and recorded a result for that key; if so, it returns the cached result without re-executing. Idempotency keys should be scoped to a unique user-action combination (e.g., SHA-256 of user_id + action_type + timestamp_bucket) with a TTL long enough to cover the full retry window (e.g., 10 minutes).

</details>

---

**Q8.** Your circuit breaker has `failure_threshold = 3` and `recovery_timeout = 30 s`. A provider recovers after 25 s but your circuit is still Open. What happens to calls during the 5-second gap, and how would you reduce that gap without lowering the threshold?

<details>
<summary>Show answer</summary>

During the 5-second gap between provider recovery (at 25 s) and circuit transition to Half-Open (at 30 s), all calls **fail fast** — the circuit rejects them without contacting the provider. This wastes 5 s of available provider capacity. To reduce the gap without lowering `failure_threshold` (which would increase false-trip risk): (1) Lower `recovery_timeout` — but this increases the risk of probing too soon and re-tripping the circuit. (2) Use a **progressive probe schedule**: instead of one fixed timeout, probe at 30 s, 15 s, 10 s for subsequent trips in the same session (the provider history suggests the outage is short). (3) Add a **health-check side channel** — a lightweight `/ping` or `/health` call on a separate timer that can transition the circuit to Half-Open proactively when it starts returning 200s. (4) Use a **success-rate window** rather than time-based recovery: once the circuit is Open, allow one probe every 5 s; transition to Closed after 2 consecutive successes.

</details>

---

## 5. Concept Deep-Dive Q&A

---

**Q1. A colleague argues that retrying on 429s is harmful because it increases load on an already-overloaded provider. How do you counter this, and what is the actual mechanism that makes retries safe?**

<details>
<summary>Show answer</summary>

The argument conflates two different problems. Without retries, the client abandons the request and the user sees an immediate error — the provider's capacity is not relieved, but your service fails visibly. Retries are safe when two conditions hold: (1) they are bounded (max 3–5 attempts), and (2) they use exponential backoff with jitter. The jitter is the key safety mechanism: it desynchronises workers so they do not all retry simultaneously. A single worker's three retries over ~8 s represents a tiny fraction of one second of provider quota. The harm comes from *synchronised* retries across thousands of workers — which jitter prevents. The practical counter: measure your retry volume in production. If retries total < 5% of requests and use jitter, they add negligible load; they also self-regulate because each retry waits progressively longer, giving the provider more recovery time.

</details>

---

**Q2. How do you decide where to place the circuit breaker — per-host, per-provider, or per-endpoint — and why does placement matter?**

<details>
<summary>Show answer</summary>

Placement determines what failures trip the breaker and what traffic is blocked. Per-endpoint placement is the most granular: a failure on `/v1/messages` does not block `/v1/embeddings`. This is the right choice when different endpoints have different reliability profiles (which is common — chat endpoints are often more loaded than embedding endpoints). Per-provider placement is coarser: any failure on the Anthropic provider trips a single breaker for all Anthropic traffic. Use this when you have a single provider with one failure domain (one API key, one region). Per-host is useful in multi-region setups: `us-east.provider.com` and `eu-west.provider.com` get separate breakers so a regional outage does not block global traffic. The practical recommendation: start with per-provider circuit breakers, then add per-endpoint breakers only when you have evidence that endpoint reliability diverges significantly.

</details>

---

**Q3. In a multi-provider failover setup, how do you handle the case where the secondary provider returns a semantically different answer from what the primary would have returned?**

<details>
<summary>Show answer</summary>

This is the "answer consistency" problem and it is largely unavoidable at the infrastructure level. Three mitigation strategies: (1) **Model equivalence pairing** — select primary and secondary models with similar capability tiers and prompt compatibility (e.g., both are instruction-following models trained on similar data). Accept that answers will differ slightly, as they also differ between runs of the same model. (2) **Response flagging** — include `{"provider": "secondary", "degraded": true}` in the response. Downstream logging can then analyse whether secondary answers diverge more from gold answers than primary answers do. (3) **Prompt normalisation** — if your primary uses Anthropic-specific system prompt features (e.g., XML tags), maintain a secondary prompt version formatted for OpenAI's instruction style. The key insight: in most Q&A use cases, a slightly different but correct answer is far better than a 503 error. Reserve consistency enforcement for high-stakes actions (legal filings, financial transactions) where you would not failover silently anyway.

</details>

---

**Q4. What is the relationship between your circuit breaker's `recovery_timeout` and your SLO's error budget, and how do you tune one given the other?**

<details>
<summary>Show answer</summary>

The `recovery_timeout` determines how long the circuit stays Open after tripping — during which all calls fail fast (counting against your error budget). If `recovery_timeout` is 60 s and the circuit trips 3 times in an hour, you lose at minimum 3 minutes of availability per hour, or 36 min/day, which at scale will burn through a 99.5% monthly availability budget in ~6 days. The tuning relationship: (1) Calculate the maximum allowable outage minutes per day from your SLO: `daily_budget_min = monthly_budget_min / 30`. (2) Estimate expected circuit trips per day from historical data. (3) Set `recovery_timeout ≤ daily_budget_min / expected_trips_per_day`. For a 99.5% SLO (216 min/month = 7.2 min/day) and 5 expected trips/day, `recovery_timeout ≤ 7.2 / 5 = 86 s`. Use a lower value (e.g., 30 s) to preserve budget margin, and compensate with a health-check side channel so the circuit doesn't stay Open longer than necessary.

</details>

---

**Q5. Describe three cases where graceful degradation is the wrong choice and a hard failure is better.**

<details>
<summary>Show answer</summary>

(1) **High-stakes one-way actions.** If the LLM output will be executed without human review (auto-send email, execute trade, update patient record), a wrong degraded answer is worse than no answer. A hard 503 forces the caller to retry later with a real model; a canned or stale response might execute an incorrect action. (2) **Security-sensitive responses.** If the LLM is performing access-control decisions ("does this user have permission to view this document?"), a stale cache answer could return an outdated permission. A hard failure is safer than a silently wrong permission grant. (3) **Compliance logging requirements.** In regulated industries, every response may need to be logged with the exact model version and retrieval context. A canned response that bypasses the retrieval pipeline may fail audit requirements. In these cases, the service should return a structured error with `{"error": "llm_unavailable", "retry_after": N}` and let the calling system decide whether to queue, abort, or escalate.

</details>

---

**Q6. Why is a latency SLO (P99 ≤ 4 s) often harder to maintain for LLM services than for traditional APIs, and what operational levers reduce P99?**

<details>
<summary>Show answer</summary>

Traditional APIs (database reads, cache lookups) have sub-millisecond to low-millisecond latency with tight distributions. LLM inference has high absolute latency (1–30 s) and high variance: first-token latency, generation length, and provider queue depth all add wide tails. Sources of P99 inflation in LLM services: (1) Long prompts take longer to process — P99 tracks the longest prompt in the 99th percentile of requests. (2) Provider queue depth spikes at peak load, adding variable queue-wait time. (3) Network retries add multiples of provider latency to the tail. Operational levers: (a) **Input token caps** — reject or truncate prompts above a limit, which bounds the generation time. (b) **Streaming responses** — return first token quickly and stream the rest; P99 of time-to-first-token is far lower than P99 of time-to-last-token. (c) **Separate fast/slow pools** — route short queries to a fast model with low queue depth; route long complex queries to a separate pool with its own latency budget. (d) **Aggressive client-side timeouts** — cut off the tail at 4 s and fail over; accept the degradation rather than let a slow call inflate your P99. (e) **Predictive load shifting** — use historical traffic patterns to pre-warm secondary providers before expected peaks.

</details>

---

**Q7. An on-call engineer wakes up at 3 AM to a "circuit breaker tripped" alert. Walk through the first five minutes of the incident response using the SLI/SLO framework.**

<details>
<summary>Show answer</summary>

Minute 0–1: **Triage the signal.** Confirm the alert is real: check the circuit breaker dashboard for trip time and affected provider. Determine which SLIs are breached: is availability below the SLO threshold? Is P99 latency spiking? How much of the error budget has been consumed this month? Minute 1–2: **Assess scope.** Is this a single-provider failure (primary only) or has the failover chain also degraded? Check secondary provider health dashboards and the degraded-answer rate SLI. If failover is working and the degraded-answer rate is within SLO, this may be a sev-3 (auto-resolving) not a sev-1. Minute 2–3: **Check provider status.** Visit the provider's status page (Anthropic, OpenAI, etc.) — most large-scale incidents are provider-side and self-resolve. If the provider confirms an incident, set a watch on their updates and do not attempt to force traffic back early. Minute 3–4: **Protect the budget.** Calculate current burn rate: minutes of downtime / elapsed time. If burn rate projects a budget breach before the provider resolves, consider activating the full degradation path (canned responses) to preserve budget for a more damaging outage later. Minute 4–5: **Communicate and document.** Post an internal status update ("LLM service degraded; failover active; degraded-answer rate = X%; monitoring"). Open an incident channel. Confirm that the circuit breaker's `recovery_timeout` is set appropriately — if it is too long, manually reset after confirming provider health.

</details>

---

**Q8. How would you write an SLO for the *quality* of LLM answers (not just availability/latency), and how would you measure it in production without human raters?**

<details>
<summary>Show answer</summary>

Quality SLOs are the frontier of LLM observability. A practical production approach uses proxy metrics rather than human judgement on every call: (1) **Retrieval coverage SLI** — what fraction of answers are backed by at least one retrieved context chunk with a relevance score above threshold? Target: ≥ 95% of answers reference at least one chunk with score ≥ 0.4. (2) **Answer length SLI** — very short answers (< 20 tokens) often indicate refusal or hallucination. Target: < 2% of answers below the minimum length threshold. (3) **Faithfulness spot-check SLI** — sample 1% of responses and run an automated faithfulness checker (a secondary LLM or a keyword-assertion rule) that verifies the answer contains at least one phrase from the retrieved context. Target: ≥ 97% pass rate. (4) **User-signal SLI** — if you have a feedback UI (thumbs up/down), track the negative-feedback rate. Target: < 5% negative per day. The SLO then combines: `quality_SLO = retrieval_coverage ≥ 0.95 AND faithfulness ≥ 0.97`. Alert when the quality SLO burns at > 2× the normal rate, indicating a regression in the retrieval pipeline or prompt template.

</details>

---

## 6. Further Reading

| Resource | Why read it |
|---|---|
| Google SRE Book — "Embracing Risk" and "Service Level Objectives" chapters | Foundational SLO/SLI/error budget concepts from the team that coined them |
| AWS Well-Architected Framework — Reliability Pillar | Cloud-native reliability patterns including circuit breakers and retries |
| Netflix Tech Blog — "Making the Netflix API More Resilient" | Original circuit breaker and bulkhead pattern writeup; Hystrix background |
| AWS re:Post — "Exponential Backoff and Jitter" by Marc Brooker | Rigorous mathematical analysis of why full jitter beats truncated exponential backoff |
| Anthropic API documentation — Error codes and rate limits | Provider-specific retry guidance, `Retry-After` header semantics, quota increase paths |
| "Release It!" by Michael Nygard | The book that popularised the circuit breaker, bulkhead, and timeout stability patterns |
| OpenTelemetry Semantic Conventions for LLMs | Standardised attribute names for LLM traces — enables cross-vendor SLI dashboards |

---

## 7. Key Takeaways

- **Retry only transient errors** (429, 5xx, timeout). Never retry 400 or 401 — you will multiply a bad request.
- **Exponential backoff with full jitter** desynchronises workers and prevents thundering herds; honour `Retry-After` headers as a hard minimum.
- **Every outbound call needs a timeout** — connect timeout (5 s) and read timeout (30–60 s). Without them, a slow provider can hold threads open and cascade into a full service outage.
- **The circuit breaker has three states** (Closed → Open → Half-Open) and prevents wasting resources on a known-bad downstream. Tune `failure_threshold` and `recovery_timeout` against your SLO error budget.
- **Failover chains** (primary → secondary → degraded) eliminate single-provider dependencies. Abstract providers behind a common interface so the orchestrator is provider-neutral.
- **Graceful degradation** (stale cache → smaller model → canned response) keeps the service useful even when all LLM providers are down. Always include `degraded: true` in the response.
- **SLOs drive operations** — your error budget tells you when to freeze deployments, when to increase on-call sensitivity, and when to accept the cost of aggressive degradation to preserve remaining budget.
- **Measure everything:** retry rate, circuit-breaker trip rate, failover rate, and degraded-answer rate are the four operational metrics that make resilience visible.
