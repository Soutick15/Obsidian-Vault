# Day 10 — Cost Management & FinOps for LLM Systems

**Track:** DevOps | **Day:** 10 of 15 | **Prerequisites:** Days 6–9

---

## 1. Objectives

By the end of this day you will be able to:

- Identify the three primary cost drivers of LLM API usage (tokens, model tier, request volume) and explain how each compounds.
- Instrument a Python service to track per-request token counts and dollar costs with zero dependencies beyond the standard library.
- Implement an **exact-match in-memory cache** and a **semantic cache** (lexical-normalisation approach) and measure their combined hit rate over a realistic query workload.
- Explain the **hit-rate vs. staleness** tradeoff for each caching strategy and when each applies.
- Configure a **LiteLLM-style router** that routes cheap-model-first and falls back on failure or complexity.
- Define budget thresholds, per-user quotas, and rate-limit guards that prevent cost blow-up.
- Read a cost/latency/quality tradeoff matrix and make a reasoned model-selection decision.

---

## 2. Concept Reading

### 2.1 What Drives LLM Cost?

Every request to an LLM API is billed on three axes:

| Driver | Description | Lever |
|---|---|---|
| **Input tokens** | Prompt text, system instructions, retrieved context, chat history | Trim prompts; cache context; compress history |
| **Output tokens** | The generated completion | Limit `max_tokens`; request concise formats |
| **Model tier** | Pricing is non-linear (e.g., a frontier model costs 10–60× a small model per token) | Route simpler queries to cheaper models |

The interaction is multiplicative: a long system prompt sent on every request × high request volume × frontier model = the most expensive configuration possible. FinOps for LLM systems is fundamentally about decoupling these three drivers wherever possible.

**Token cost formula (per request):**

```
cost = (input_tokens × price_in) + (output_tokens × price_out)
```

Typical 2025 pricing reference points (illustrative — verify with your provider):

| Model tier | Input $/1M tokens | Output $/1M tokens |
|---|---|---|
| Small / fast (e.g., Haiku-class) | $0.25 | $1.25 |
| Mid-tier (e.g., Sonnet-class) | $3.00 | $15.00 |
| Frontier (e.g., Opus-class) | $15.00 | $75.00 |

A 1,000-token prompt answered with 500 tokens on a mid-tier model costs ~$0.0105 per call. At 100,000 calls/day that is $1,050/day — before considering input token growth from chat history accumulation.

---

### 2.2 Token-Cost Monitoring and Attribution

Reliable FinOps requires attribution: knowing *which feature, user, or team* is responsible for which cost. The minimal instrumentation pattern is:

```python
# Every LLM call should produce a CostRecord
@dataclass
class CostRecord:
    request_id: str
    user_id: str
    feature: str          # "hr-chat", "summarisation", etc.
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    cache_hit: bool       # True if served from cache (cost = 0)
    timestamp: float
```

Store records in a time-series store (Prometheus + Grafana, InfluxDB, or even a SQLite append-only table). Aggregate by `feature` and `user_id` daily to detect cost regressions early — a new prompt template that adds 200 tokens to every request will appear as a step-change in the daily cost-per-request metric.

**Key metrics to track:**

| Metric | Alert threshold (example) |
|---|---|
| `cost_per_request_usd` | > 2× rolling 7-day average |
| `daily_spend_usd` | > budget cap (hard stop) |
| `p99_input_tokens` | > 8,000 (risk of exceeding context window) |
| `cache_hit_rate` | < 20% (caching not paying off; review query diversity) |
| `fallback_rate` | > 10% (primary model unreliable) |

---

### 2.3 Prompt Caching

**Prompt caching** (provider-side) is a feature offered by some API providers where a long, repeated prefix (system prompt + static context) is cached server-side across requests. The provider charges a reduced rate — typically 10–25% of normal input-token price — for cache-hit tokens.

**How it works:**
1. You send a request with a large, stable prefix (e.g., a 4,000-token system prompt).
2. The provider stores the KV-cache for that prefix.
3. The next request with the identical prefix pays only the "cache read" price, not the full input price.
4. The cache is typically invalidated after a TTL (e.g., 5 minutes of inactivity).

**Enabling (Anthropic example):**
```python
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": long_system_context,
                "cache_control": {"type": "ephemeral"}  # Mark as cacheable prefix
            },
            {"type": "text", "text": user_question}
        ]
    }
]
```

**Tradeoffs:**

| | Prompt Caching |
|---|---|
| **Hit rate** | High if system prompt is stable; drops immediately on any prefix change |
| **Staleness** | Not a concern — cache is keyed on exact content |
| **Savings** | Up to 90% reduction on prefix tokens |
| **Complexity** | Low — provider handles it; you only mark the boundary |
| **Limitation** | Provider-specific API; cache is per-provider, not cross-provider |

---

### 2.4 Semantic Caching (Application-Side)

**Semantic caching** is an application-layer technique: you cache the LLM's response keyed on the *meaning* of the query rather than its exact text. When a new query arrives, you compute its similarity to previously cached queries. If similarity exceeds a threshold, you return the cached answer without calling the LLM.

**Two implementation approaches:**

**a) Embedding-based semantic cache** (high accuracy):
1. Embed the incoming query with a sentence-transformer model.
2. Store `(embedding_vector, cached_answer)` pairs.
3. On new query: embed it, run ANN search (e.g., ChromaDB, FAISS, or a simple cosine loop).
4. If top-1 similarity > threshold (e.g., 0.92), return cached answer.

**b) Lexical normalisation cache** (zero dependencies):
1. Normalise query: lowercase, strip punctuation, remove stopwords, sort tokens.
2. Key the cache on the normalised form.
3. Paraphrases that share the same significant tokens — "How many PTO days?" vs "What is the PTO day count?" — produce the same key.

The lab uses approach (b) so it runs with no external dependencies. Both approaches share the same tradeoff structure:

| | Semantic Cache |
|---|---|
| **Hit rate** | Depends on query diversity; 20–60% in HR Q&A workloads |
| **Staleness** | Paraphrases of an old question return a stale answer — TTL or cache invalidation is required |
| **Savings** | Full token cost avoided on hit (input + output) |
| **Complexity** | Medium — embedding approach needs a vector store; lexical approach needs normalisation |
| **False-positive risk** | Similar-but-different questions ("salary of junior dev" vs "salary of senior dev") can collide if normalisation is too aggressive |

**Staleness mitigation strategies:**
- Set a TTL per cache entry (e.g., 1 hour for HR policy answers).
- Trigger cache invalidation when underlying documents change.
- Tag cache entries with a `corpus_version` hash; invalidate on hash change.

---

### 2.5 Model Routing and Fallback via an LLM Gateway

An **LLM gateway** sits between your application and the upstream provider APIs. It handles:
- **Routing:** send request to model A, B, or C based on rules (complexity score, cost budget, feature flag).
- **Fallback:** if model A returns an error or times out, retry on model B.
- **Load balancing:** distribute requests across multiple provider accounts or regions.
- **Unified interface:** one SDK call regardless of provider (OpenAI, Anthropic, Azure, Bedrock, …).

**LiteLLM** is the most widely used open-source gateway for Python teams. It exposes an OpenAI-compatible interface over 100+ models.

**Router configuration (YAML/dict pattern):**

```yaml
# litellm_router_config.yaml
model_list:
  - model_name: "fast-answerer"          # alias used by your app
    litellm_params:
      model: "claude-haiku-4-5"
      api_key: os.environ/ANTHROPIC_API_KEY
    rpm: 500                             # requests-per-minute limit

  - model_name: "fast-answerer"          # same alias — fallback entry
    litellm_params:
      model: "gpt-5-mini"
      api_key: os.environ/OPENAI_API_KEY
    rpm: 500

  - model_name: "quality-answerer"
    litellm_params:
      model: "claude-sonnet-4-5"
      api_key: os.environ/ANTHROPIC_API_KEY
    rpm: 100

router_settings:
  routing_strategy: "least-busy"
  num_retries: 2
  timeout: 30
  fallbacks:
    - {"fast-answerer": ["quality-answerer"]}  # on failure, escalate
```

**Python usage:**

```python
import litellm
from litellm import Router

router = Router(model_list=model_list)

# Your app always calls the alias; the router decides which model
response = router.completion(
    model="fast-answerer",
    messages=[{"role": "user", "content": question}]
)
```

**Routing strategies:**

| Strategy | When to use |
|---|---|
| **Cheapest model first** | Default for non-latency-sensitive batch work |
| **Complexity routing** | Route short/simple queries to haiku-class; long/complex to sonnet-class |
| **Latency-based** | Route to whichever model has lowest p50 latency in the rolling window |
| **Budget-aware** | Block requests when daily spend > threshold; degrade to mock or queued |

---

### 2.6 Budgets, Quotas, and Rate Limiting

LLM cost control requires **three complementary layers:**

**Layer 1 — Per-request guards** (synchronous, in-process):
- Validate `len(prompt_tokens) < max_input_tokens` before calling.
- Cap `max_tokens` in the request to prevent runaway generation.

**Layer 2 — Per-user / per-feature quotas** (stateful):
- Maintain a rolling counter of tokens or spend per `(user_id, feature, day)`.
- Reject or queue requests once quota is exhausted.
- Store in Redis or an in-process `defaultdict` for a single-instance service.

**Layer 3 — Global budget circuit breaker** (async, operator-facing):
- Subscribe to provider spend webhooks (or poll the billing API every hour).
- If projected daily spend > threshold, flip a feature flag that routes all requests to the mock or a cheaper model.

```python
class BudgetGuard:
    def __init__(self, daily_limit_usd: float):
        self.limit = daily_limit_usd
        self._spent = 0.0

    def record(self, cost: float) -> None:
        self._spent += cost

    def check(self) -> None:
        if self._spent >= self.limit:
            raise BudgetExceededError(
                f"Daily limit ${self.limit:.2f} reached "
                f"(spent ${self._spent:.4f})"
            )
```

---

### 2.7 Cost / Latency / Quality Tradeoffs

There is no free lunch. Every FinOps decision moves you on a three-way tradeoff surface:

```
                Quality (accuracy, groundedness)
                        ▲
                        │         Frontier model
                        │        ◆
                        │      ◆
                        │   ◆  Mid-tier
                        │ ◆
                        │◆ Small model
                        └─────────────────────► Speed (low latency)
                       (Cost decreases as you move toward small + fast)
```

**Decision heuristics for DevOps engineers:**

| Query type | Recommended approach |
|---|---|
| FAQ / known-question lookup | Exact-match cache → zero LLM cost |
| Paraphrase of known question | Semantic cache → zero LLM cost |
| New simple factual question | Small model (haiku-class) |
| Complex multi-hop reasoning | Mid-tier or frontier model |
| Bulk batch (non-interactive) | Batch API (50% discount on some providers) |
| Exploratory / creative | Frontier model, user-initiated, cost visible to user |

**Cache-first architecture (recommended default):**
```
Request → Exact cache? → hit: return cached answer (cost: $0)
                       → miss: Semantic cache? → hit: return (cost: $0)
                                               → miss: Route to cheapest model
                                                        → success: cache + return
                                                        → fail: fallback to next tier
```

---

### 2.8 Cost Dashboards and Alerts

A minimal production cost dashboard should show:

| Panel | Source |
|---|---|
| Daily spend (bar chart) | Billing API poll or provider webhook |
| Cost per request by feature | Application-level `CostRecord` aggregation |
| Cache hit rate (exact + semantic) | In-process counters exported to Prometheus |
| Model distribution | Count of requests routed to each model tier |
| Token size distribution (p50/p99) | Histogram from `CostRecord.input_tokens` |
| Budget burn rate vs. forecast | Rolling 7-day spend extrapolated to month-end |

Recommended alerting thresholds: page on-call if daily spend exceeds 150% of the 7-day rolling average, or if the cache hit rate drops below 15% for more than 30 minutes.

---

## 3. Hands-On Lab

**Location:** `labs/devops/day-10/`

**Goal:** Add a **caching and cost-accounting layer** in front of the shared `answer()` function. Run a workload of repeated and paraphrased queries, then report cache hit rates and simulated cost savings.

**Files:**
```
labs/devops/day-10/
├── README.md
├── requirements.txt
├── starter.py      ← work through TODO markers
└── solution.py     ← reference implementation (run to verify)
```

**Run (no API key needed):**
```bash
python labs/devops/day-10/solution.py
```

See `labs/devops/day-10/README.md` for full instructions and expected output.

---

## 4. Self-Check Quiz

Answer each question before revealing the answer.

**Q1.** A team sends a 3,000-token system prompt on every request, at 10,000 requests/day, using a mid-tier model priced at $3.00/1M input tokens. What is the daily cost from the system prompt alone, and what is the most direct lever to reduce it?

<details>
<summary>Show answer</summary>

3,000 tokens × 10,000 requests = 30,000,000 tokens/day × ($3.00 / 1,000,000) = **$90/day** from the system prompt alone. The most direct lever is **provider-side prompt caching**: mark the stable prefix with `cache_control`, so subsequent requests pay only the cache-read rate (~10–25% of normal). If the prompt is truly static, this can cut that line item by ~75–90%.

</details>

---

**Q2.** What is the difference between **exact-match caching** and **semantic caching**, and when does each fail to produce a cache hit?

<details>
<summary>Show answer</summary>

**Exact-match caching** keys on the literal query string (after normalisation like lowercasing). It fails when the user rephrases the question even slightly — "how many PTO days" vs "what is the PTO entitlement" are different keys. **Semantic caching** keys on the *meaning* of the query, using embedding similarity or lexical normalisation. It fails when two queries are semantically similar but require different answers (e.g., "salary of junior engineer" vs "salary of senior engineer"), or when no previously cached query is similar enough to exceed the threshold.

</details>

---

**Q3.** A semantic cache returns a stale answer because the underlying HR policy document was updated last week. Name two mitigation strategies.

<details>
<summary>Show answer</summary>

1. **TTL (time-to-live):** expire cache entries after a fixed duration (e.g., 1 hour or 1 day) so stale answers are eventually flushed. 2. **Corpus-version invalidation:** hash the corpus content at startup; if the hash changes (document updated), flush the entire semantic cache. Other valid answers: event-driven invalidation on document write, per-document cache tagging so only affected entries are cleared.

</details>

---

**Q4.** Describe the "cheapest model first, fall back on failure" routing pattern in LiteLLM. What triggers the fallback?

<details>
<summary>Show answer</summary>

The router sends every request to the cheapest configured model alias first (e.g., `claude-haiku-4-5`). If the primary model returns an HTTP error (5xx, 429 rate-limit, timeout), the router automatically retries on the next model in the fallback chain (e.g., `claude-sonnet-4-5`). The fallback does **not** trigger on a semantically poor answer — quality-based routing requires a separate evaluation step or complexity classifier before the call. The trigger is purely a provider/network error or rate-limit response.

</details>

---

**Q5.** Why is output-token cost often *higher per token* than input-token cost, and what is the practical implication?

<details>
<summary>Show answer</summary>

Output tokens require the model to perform autoregressive generation — each token is sampled sequentially, which is GPU-compute-intensive. Input tokens are processed in parallel via attention, making them cheaper per unit. Practically: if your use case returns long structured outputs (e.g., full policy documents), capping `max_tokens` or requesting only a summary has a disproportionately large cost impact. Switching from "return the full policy section" to "return a 3-bullet summary" can reduce output cost by 5–10× per call.

</details>

---

**Q6.** What is the purpose of a **budget circuit breaker**, and how does it differ from a per-user quota?

<details>
<summary>Show answer</summary>

A **budget circuit breaker** is a global operator-level guard: if the service's total daily spend exceeds a threshold, it trips and routes all requests to a mock or cheaper model, or rejects them entirely. It protects the entire system from runaway cost. A **per-user quota** is a per-identity guard: it limits how many tokens or dollars a single user or feature consumes in a rolling window, allowing other users to continue normally. They are complementary — per-user quotas prevent any single actor from exhausting the budget; the circuit breaker is the last-resort safety net for the aggregate.

</details>

---

## 5. Concept Deep-Dive Q&A

---

**Q1. In a production LLM service, why is it important to log `cache_hit: bool` on every request, even when you already track hit rate as an aggregate counter?**

<details>
<summary>Show answer</summary>

Aggregate hit-rate counters tell you the system-level average, but per-request `cache_hit` flags enable much richer analysis: (1) you can join cache hits to user IDs to see which users ask repetitive questions (candidates for a dedicated FAQ UI), (2) you can join to latency to quantify the p99 latency improvement from cache hits vs. misses, (3) you can detect time-of-day patterns — cache hit rate often drops at session start when each user's first query is unique. Without per-request granularity, these insights are invisible in aggregates.

</details>

---

**Q2. What is the "false positive" problem in semantic caching and how do you detect it in production?**

<details>
<summary>Show answer</summary>

A false positive occurs when the cache returns an answer for query B because B is semantically similar to cached query A, but the correct answers differ. Example: "What is the dental benefit for dependants?" and "What is the vision benefit for dependants?" share many tokens and may cluster near each other in embedding space. If the similarity threshold is too low (too permissive), the dental answer is returned for the vision question — silently wrong. Detection: log the original query and the matched cached query side by side. Sample 1% of cache hits and run a secondary faithfulness check (or a simple keyword assertion). Alert if the matched-vs-requested query pair share fewer than N significant content words.

</details>

---

**Q3. LiteLLM supports a `routing_strategy: "cost-based"` mode. What information must LiteLLM have at routing time to make a cost-optimal decision, and what is the risk of routing purely on per-token price?**

<details>
<summary>Show answer</summary>

Cost-based routing needs: the per-token input/output price for each model in the pool, and an estimate of the expected output length (which is unknown before generation). LiteLLM typically uses the configured price table and assumes a default output length. The risk of routing purely on per-token price: (1) cheaper models may have lower quality, requiring retry or human escalation — the retry costs can exceed the initial savings; (2) cheaper models often have lower rate limits and stricter context windows, so they may be unavailable or truncate inputs at peak load; (3) cost per token ignores latency — a cheap model with 8-second p99 may be unacceptable for interactive use even if it costs 1/10th as much.

</details>

---

**Q4. Explain why prompt caching (provider-side) and semantic caching (application-side) are *complementary*, not alternatives. Give a scenario where you need both.**

<details>
<summary>Show answer</summary>

Prompt caching reduces the cost of the *prefix* portion of repeated requests — it saves money on the static system prompt tokens when the same user sends many different questions. Semantic caching skips the LLM call entirely when the *question* matches a previously answered one — it saves money on both input and output tokens for the full request. They operate on different axes: prompt caching applies when the prefix is stable and the questions vary; semantic caching applies when the questions repeat or paraphrase each other. Scenario where both help: an HR chatbot with a 4,000-token policy context (prompt caching saves ~75% of that prefix cost for unique questions) that also receives the same 50 FAQ questions thousands of times per day (semantic caching eliminates the LLM call entirely for those 50 patterns). Removing either layer leaves significant cost on the table.

</details>

---

**Q5. A DevOps engineer proposes setting the semantic cache similarity threshold at 0.99 (very strict) to avoid false positives. What is the tradeoff, and how would you find the right threshold empirically?**

<details>
<summary>Show answer</summary>

At 0.99 threshold, only near-identical queries hit the cache — most paraphrases will miss, keeping the hit rate very low (potentially as low as exact-match). The cost saving is minimal. To find the right threshold empirically: (1) Collect a sample of real query pairs that you manually judge as "should return same answer" vs "should return different answer". (2) Compute their similarity scores using your chosen method (cosine similarity of embeddings, or Jaccard of normalised token sets). (3) Plot the score distribution for "same-answer" and "different-answer" pairs. (4) Choose the threshold at the point that maximises true-positive rate while keeping false-positive rate below an acceptable level (e.g., 1%). For HR Q&A workloads using embedding-based similarity, 0.92 is a common starting point; for lexical methods, Jaccard >= 0.6 on significant tokens works well.

</details>

---

**Q6. Why should `cost_usd` be computed *application-side* rather than relying solely on the provider's monthly invoice for cost attribution?**

<details>
<summary>Show answer</summary>

Provider invoices aggregate all usage into a single bill — they do not break down cost by feature, user, team, or request type. Application-side cost computation (using the known token count from the API response and the published price table) gives per-request cost attribution that can be joined to your business data: which product feature is most expensive, which user tier consumes disproportionate tokens, which prompt template caused a cost spike. This attribution is necessary for: (1) chargeback / showback to internal teams, (2) catching regressions in prompt length before the monthly bill arrives, (3) enforcing per-user quotas in real time. The provider invoice validates totals; application-side accounting enables operational control.

</details>

---

**Q7. Describe a scenario where adding caching *increases* cost rather than reducing it.**

<details>
<summary>Show answer</summary>

If the cache implementation uses an embedding model that costs significant compute per query (e.g., a GPU-hosted sentence-transformer with a per-call fee), and the workload is highly diverse (very low cache hit rate), then every request pays both the embedding cost and the LLM cost. If the embedding cost is, say, $0.001/call and the cache hit rate is 2%, you spend $0.001 × 1,000 = $1 on embeddings to save 0.02 × 1,000 × $0.01 = $0.20 in LLM cost — a net loss of $0.80. The fix: use a cheap or local embedding model (the lab uses a zero-cost lexical approach), only enable semantic caching when the expected hit rate exceeds the embedding overhead, or restrict caching to high-frequency query patterns.

</details>

---

**Q8. What operational metrics would you add to a Grafana dashboard specifically to detect a caching *regression* — i.e., a deployment that accidentally broke caching?**

<details>
<summary>Show answer</summary>

A caching regression can look identical to a cost spike if you only watch spend. The metrics that specifically detect it: (1) `exact_cache_hit_rate` — a sudden drop from e.g. 45% to near 0% after a deployment flags that the cache key computation changed or the cache was not persisted across restart. (2) `semantic_cache_hit_rate` — a drop here suggests the normalisation function or similarity threshold changed. (3) `cache_size` (number of entries) — if it drops to 0 after deploy, the cache was not warmed or was accidentally cleared. (4) `llm_calls_per_minute` — a step-change upward after deploy with no increase in user traffic is a strong signal. Alert rule: if `llm_calls_per_minute` increases by > 50% within 5 minutes of a deployment marker with no corresponding increase in `active_users`, page the on-call engineer.

</details>

---

## 6. Further Reading

| Resource | Why read it |
|---|---|
| LiteLLM documentation — Router & Fallbacks | Production router config, routing strategies, budget limits |
| Anthropic Prompt Caching guide | Provider-specific implementation details and cache TTL rules |
| "Patterns for LLM Cost Optimization" (various authors, 2024) | Survey of caching, batching, distillation, and routing strategies |
| OpenAI Prompt Caching documentation | Comparison point; how OpenAI's implementation differs |
| `tiktoken` library (OpenAI) | Accurate token counting for GPT-family models before calling the API |
| FinOps Foundation — Cloud FinOps Practitioner materials | General FinOps principles that apply directly to LLM spend management |
| Redis documentation — `EXPIRE` command | TTL-based cache invalidation implementation reference |

---

## 7. Key Takeaways

- **Three cost levers:** tokens (trim prompts, cap output), model tier (route cheap-first), and volume (cache aggressively to eliminate calls entirely).
- **Exact-match cache is free** (in-memory dict) and should always be the first layer — it eliminates duplicate and repeated queries at zero compute cost.
- **Semantic cache** handles paraphrases but introduces a staleness risk; always pair it with a TTL or corpus-version invalidation strategy.
- **Prompt caching** (provider-side) is complementary to semantic caching: it reduces per-token cost for prefix tokens; semantic caching eliminates the call entirely.
- **LiteLLM** provides a single interface over 100+ models with built-in fallback, retries, and routing strategies — it is the standard DevOps tool for multi-provider LLM routing.
- **Budgets require three layers:** per-request guards, per-user quotas, and a global circuit breaker. Each layer catches a different failure mode.
- **Instrument first.** A `CostRecord` on every request — including cache hits (cost: $0) — is the foundation for all FinOps decisions. You cannot optimise what you do not measure.
