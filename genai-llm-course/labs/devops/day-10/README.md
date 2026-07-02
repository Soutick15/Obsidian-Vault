# Day 10 Lab — Cost Management & FinOps: Caching + Cost Accounting

**Track:** DevOps | **Prerequisites:** Days 6–9, shared service running

---

## Objectives

1. Implement an **exact-match in-memory cache** in front of `service.answer()`.
2. Implement a **semantic cache** using lexical normalisation so paraphrased queries hit the cache.
3. Build a **token-cost estimator** and per-request cost accounting dataclass.
4. Run a **realistic query workload** (repeated + paraphrased queries) and report hit rates and simulated cost savings.
5. Study a **LiteLLM router config** (documented reference — no key required) and explain the routing logic.

---

## Files

```
labs/devops/day-10/
├── README.md           ← you are here
├── requirements.txt    ← stdlib only; scikit-learn optional for bonus
├── starter.py          ← work through TODO markers (5 tasks)
└── solution.py         ← reference implementation; run to verify
```

---

## Setup

No API key required. All computation is local and deterministic.

```bash
# From the repo root
pip install -r labs/devops/day-10/requirements.txt

# Optional: install scikit-learn for TF-IDF similarity in semantic cache bonus
pip install scikit-learn
# Note: using a real LLM provider (Anthropic, OpenAI) also requires installing
# the provider SDK listed under the optional packages comment in requirements.txt.
```

---

## Run the solution

```bash
# From the repo root
python labs/devops/day-10/solution.py
```

---

## Expected output (approximate)

```
============================================================
  Day 10 — LLM Cost & FinOps: Caching + Cost Accounting
============================================================

[WORKLOAD] Running 20 queries (repeated + paraphrased)...

  Q01 [EXACT-MISS] [SEM-MISS] → LLM call  | $0.000420 | "How many PTO days do employees get?"
  Q02 [EXACT-MISS] [SEM-HIT ] → CACHE HIT | $0.000000 | "What is the number of PTO days?"
  Q03 [EXACT-HIT ] [      -- ] → CACHE HIT | $0.000000 | "How many PTO days do employees get?"
  ...

============================================================
  COST & CACHE REPORT
============================================================

  Total queries          : 20
  Exact-match cache hits : 7   (35.0%)
  Semantic cache hits    : 5   (25.0%)
  Combined cache hit rate: 60.0%
  LLM calls made         : 8   (40.0%)

  Simulated LLM cost (no cache) : $0.008400
  Actual cost (with cache)      : $0.003360
  Simulated $ saved             : $0.005040  (60.0% savings)

============================================================
  LITELLM ROUTER CONFIG (reference — no key required)
============================================================
  [router config printed as documented YAML reference]
============================================================
```

---

## Tasks

| # | TODO label | What to implement |
|---|---|---|
| 1 | `TODO-1: ExactCache` | In-memory dict cache keyed on normalised query string |
| 2 | `TODO-2: SemanticCache` | Lexical-normalise query; Jaccard similarity match |
| 3 | `TODO-3: CostEstimator` | Count tokens (word-split approximation); compute cost in USD |
| 4 | `TODO-4: CachedAnswerService` | Orchestrate exact → semantic → LLM pipeline; record costs |
| 5 | `TODO-5: run_workload` | Drive 20 queries, print per-query status, print final report |

---

## Grading yourself

- [ ] Exact-match cache correctly returns hits for identical queries.
- [ ] Semantic cache returns hits for paraphrased queries that share significant tokens.
- [ ] `cost_usd` is 0.0 for cache hits and > 0 for LLM calls.
- [ ] Final report shows combined hit rate >= 50% on the provided workload.
- [ ] Script exits 0 with no API key set.

---

## LiteLLM router reference

`solution.py` includes a `LITELLM_ROUTER_CONFIG` constant — a documented YAML string showing a production router configuration. You do not need LiteLLM installed; study the config and the inline comments explaining each field.
