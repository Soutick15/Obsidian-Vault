"""
Day 10 — Cost Management & FinOps: Caching + Cost Accounting
DevOps Track | Complete reference implementation.

Run:
    python labs/devops/day-10/solution.py

No API key required. Set ANTHROPIC_API_KEY or OPENAI_API_KEY to use a real
provider instead of the deterministic mock.

What this script demonstrates:
    (a) Exact-match in-memory cache
    (b) Semantic cache using lexical normalisation + Jaccard similarity
    (c) Token-cost estimator + per-request CostRecord
    (d) Cache hit-rate and simulated $ savings over a 20-query workload
    (e) LiteLLM-style router config as a documented reference
"""

from __future__ import annotations

import pathlib
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Shared service import
# ---------------------------------------------------------------------------
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from service import answer  # noqa: E402

# ---------------------------------------------------------------------------
# Pricing table (illustrative — verify with your provider)
# Prices in USD per 1,000 tokens.
# ---------------------------------------------------------------------------
PRICE_TABLE: dict[str, dict[str, float]] = {
    "mock": {"input": 0.0, "output": 0.0},
    "haiku-class": {"input": 0.00025, "output": 0.00125},
    "sonnet-class": {"input": 0.003, "output": 0.015},
    "frontier-class": {"input": 0.015, "output": 0.075},
}

DEFAULT_MODEL_TIER = "haiku-class"

# ---------------------------------------------------------------------------
# LiteLLM Router Config — documented reference (no installation required)
# ---------------------------------------------------------------------------
LITELLM_ROUTER_CONFIG = """
# litellm_router_config.yaml
# -----------------------------------------------------------------
# Production router: cheap-first routing with quality fallback.
# Install: pip install litellm
# Usage:
#   from litellm import Router
#   router = Router(model_list=model_list, routing_strategy="least-busy")
#   response = router.completion(model="fast-answerer", messages=[...])
# -----------------------------------------------------------------

model_list:
  # --- PRIMARY: smallest / fastest / cheapest ---
  - model_name: "fast-answerer"
    litellm_params:
      model: "claude-haiku-4-5"
      api_key: os.environ/ANTHROPIC_API_KEY
    rpm: 500          # requests-per-minute cap for this entry
    tpm: 100000       # tokens-per-minute cap

  - model_name: "fast-answerer"   # same alias = load-balanced fallback entry
    litellm_params:
      model: "gpt-5-mini"
      api_key: os.environ/OPENAI_API_KEY
    rpm: 500
    tpm: 200000

  # --- SECONDARY: higher quality, higher cost ---
  - model_name: "quality-answerer"
    litellm_params:
      model: "claude-sonnet-4-5"
      api_key: os.environ/ANTHROPIC_API_KEY
    rpm: 100
    tpm: 40000

router_settings:
  routing_strategy: "cost-based"   # curriculum default; options: least-busy | cost-based | latency-based
  num_retries: 2
  timeout: 30                       # seconds per attempt
  retry_after: 1                    # seconds between retries
  fallbacks:
    # Trigger: provider HTTP error (5xx, 429, timeout).
    # Does NOT trigger on semantically poor answer quality.
    - {"fast-answerer": ["quality-answerer"]}
  allowed_fails: 1                  # failures before marking model unhealthy
  cooldown_time: 60                 # seconds before retrying an unhealthy model
"""

# ---------------------------------------------------------------------------
# Helper: approximate token count
# ---------------------------------------------------------------------------


def approx_tokens(text: str) -> int:
    """Approximate token count: word count × 1.3 (rough GPT/Claude heuristic)."""
    words = len(text.split())
    return max(1, int(words * 1.3))


# ===========================================================================
# ExactCache
# ===========================================================================


class ExactCache:
    """In-memory exact-match cache keyed on normalised query string."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _normalise(query: str) -> str:
        return query.lower().strip()

    def get(self, query: str) -> dict[str, Any] | None:
        return self._store.get(self._normalise(query))

    def put(self, query: str, result: dict[str, Any]) -> None:
        self._store[self._normalise(query)] = result

    @property
    def size(self) -> int:
        return len(self._store)


# ===========================================================================
# SemanticCache
# ===========================================================================

STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "need",
    "dare",
    "ought",
    "used",
    "to",
    "of",
    "in",
    "on",
    "at",
    "for",
    "with",
    "about",
    "by",
    "from",
    "as",
    "into",
    "through",
    "during",
    "i",
    "you",
    "we",
    "they",
    "he",
    "she",
    "it",
    "what",
    "how",
    "when",
    "where",
    "who",
    "which",
    "get",
    "my",
    "our",
    "your",
    "their",
    "and",
    "or",
    "but",
    "if",
    "not",
    "there",
    "here",
    "this",
    "that",
    "these",
    "those",
    "me",
    "him",
    "her",
}


class SemanticCache:
    """
    Lexical-normalisation semantic cache with Jaccard similarity matching.

    Normalisation: lowercase → strip punctuation → tokenise → remove stopwords
    Similarity: Jaccard(A, B) = |A ∩ B| / |A ∪ B|
    """

    def __init__(self) -> None:
        # List of (frozenset_of_significant_tokens, cached_result)
        self._entries: list[tuple[frozenset[str], dict[str, Any]]] = []

    @staticmethod
    def _normalise(query: str) -> frozenset[str]:
        lowered = query.lower()
        stripped = re.sub(r"[^a-z0-9\s]", " ", lowered)
        tokens = stripped.split()
        significant = {t for t in tokens if t not in STOPWORDS and len(t) > 1}
        return frozenset(significant)

    @staticmethod
    def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
        if not a and not b:
            return 0.0
        intersection = len(a & b)
        union = len(a | b)
        return intersection / union if union > 0 else 0.0

    def get(self, query: str, threshold: float = 0.30) -> dict[str, Any] | None:
        tokens = self._normalise(query)
        best_score = 0.0
        best_result: dict[str, Any] | None = None
        for cached_tokens, cached_result in self._entries:
            score = self._jaccard(tokens, cached_tokens)
            if score > best_score:
                best_score = score
                best_result = cached_result
        if best_score >= threshold:
            return best_result
        return None

    def put(self, query: str, result: dict[str, Any]) -> None:
        tokens = self._normalise(query)
        self._entries.append((tokens, result))

    @property
    def size(self) -> int:
        return len(self._entries)


# ===========================================================================
# CostRecord + CostEstimator
# ===========================================================================


@dataclass
class CostRecord:
    query: str
    model_tier: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    cache_hit: bool
    cache_type: str  # "exact", "semantic", or "none"
    timestamp: float = field(default_factory=time.time)


class CostEstimator:
    """Estimates token cost for an LLM request."""

    def __init__(self, model_tier: str = DEFAULT_MODEL_TIER) -> None:
        self.model_tier = model_tier
        prices = PRICE_TABLE.get(model_tier, PRICE_TABLE["haiku-class"])
        self._price_in = prices["input"]  # USD per 1,000 input tokens
        self._price_out = prices["output"]  # USD per 1,000 output tokens

    def estimate(
        self,
        question: str,
        result: dict[str, Any],
        cache_hit: bool = False,
        cache_type: str = "none",
    ) -> CostRecord:
        input_tokens = approx_tokens(question)
        output_tokens = approx_tokens(result.get("answer", ""))
        if cache_hit:
            cost_usd = 0.0
        else:
            cost_usd = (input_tokens * self._price_in / 1000.0) + (
                output_tokens * self._price_out / 1000.0
            )
        return CostRecord(
            query=question,
            model_tier=self.model_tier,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            cache_hit=cache_hit,
            cache_type=cache_type,
        )

    def hypothetical_cost(self, question: str, result: dict[str, Any]) -> float:
        """Cost that *would* have been incurred if there were no cache."""
        input_tokens = approx_tokens(question)
        output_tokens = approx_tokens(result.get("answer", ""))
        return (input_tokens * self._price_in / 1000.0) + (
            output_tokens * self._price_out / 1000.0
        )


# ===========================================================================
# CachedAnswerService
# ===========================================================================


class CachedAnswerService:
    """
    Cache + cost-accounting wrapper around the shared `answer()` function.

    Pipeline per request:
      1. Exact cache check → hit: return immediately, cost = $0
      2. Semantic cache check → hit: return immediately, cost = $0
      3. Call `answer()` from shared service
      4. Store in both caches
      5. Return result + CostRecord
    """

    def __init__(self, model_tier: str = DEFAULT_MODEL_TIER) -> None:
        self._exact = ExactCache()
        self._semantic = SemanticCache()
        self._estimator = CostEstimator(model_tier=model_tier)
        self.records: list[CostRecord] = []
        self.exact_hits = 0
        self.semantic_hits = 0
        self.llm_calls = 0

    def ask(self, question: str) -> tuple[dict[str, Any], CostRecord]:
        """
        Return (answer_result, cost_record).
        Check caches first; fall through to LLM only on full miss.
        """
        # 1. Exact cache
        cached = self._exact.get(question)
        if cached is not None:
            record = self._estimator.estimate(
                question, cached, cache_hit=True, cache_type="exact"
            )
            self.records.append(record)
            self.exact_hits += 1
            return cached, record

        # 2. Semantic cache
        cached = self._semantic.get(question)
        if cached is not None:
            record = self._estimator.estimate(
                question, cached, cache_hit=True, cache_type="semantic"
            )
            self.records.append(record)
            self.semantic_hits += 1
            return cached, record

        # 3. LLM call (shared service mock or real provider)
        result = answer(question)
        record = self._estimator.estimate(
            question, result, cache_hit=False, cache_type="none"
        )
        self.records.append(record)
        self.llm_calls += 1

        # 4. Populate both caches
        self._exact.put(question, result)
        self._semantic.put(question, result)

        return result, record

    def report(self) -> dict[str, Any]:
        """Return summary statistics over all recorded requests."""
        total = len(self.records)
        combined_hits = self.exact_hits + self.semantic_hits
        combined_hit_rate = combined_hits / total if total > 0 else 0.0

        actual_cost = sum(r.cost_usd for r in self.records)

        # Simulated no-cache cost: what would every call have cost as an LLM call?
        no_cache_cost = sum(
            self._estimator.hypothetical_cost(r.query, {"answer": ""})
            for r in self.records
        )
        # Better estimate: use actual LLM-call costs as the per-query baseline
        # For cache hits, compute what the LLM call would have cost using the
        # tokens that were estimated at record time.
        prices = PRICE_TABLE.get(self._estimator.model_tier, PRICE_TABLE["haiku-class"])
        p_in = prices["input"]
        p_out = prices["output"]
        no_cache_cost_v2 = sum(
            (r.input_tokens * p_in / 1000.0) + (r.output_tokens * p_out / 1000.0)
            for r in self.records
        )

        savings = no_cache_cost_v2 - actual_cost
        savings_pct = (
            (savings / no_cache_cost_v2 * 100.0) if no_cache_cost_v2 > 0 else 0.0
        )

        return {
            "total_queries": total,
            "exact_hits": self.exact_hits,
            "semantic_hits": self.semantic_hits,
            "combined_hits": combined_hits,
            "exact_hit_rate": self.exact_hits / total if total > 0 else 0.0,
            "semantic_hit_rate": self.semantic_hits / total if total > 0 else 0.0,
            "combined_hit_rate": combined_hit_rate,
            "llm_calls": self.llm_calls,
            "total_cost_usd": actual_cost,
            "simulated_no_cache_cost_usd": no_cache_cost_v2,
            "simulated_savings_usd": savings,
            "simulated_savings_pct": savings_pct,
        }


# ===========================================================================
# Workload
# ===========================================================================

WORKLOAD = [
    # Group 1 — PTO / leave questions (exact repeats + paraphrases)
    "How many PTO days do employees get?",
    "How many PTO days do new employees get?",  # semantic (Jaccard ~0.67)
    "How many PTO days do employees get?",  # exact repeat
    "How many PTO days per year do employees receive?",  # semantic (Jaccard ~0.57)
    "What is the PTO days policy for employees?",  # semantic (Jaccard ~0.44)
    # Group 2 — Health insurance
    "What health insurance plans are available for employees?",
    "What health insurance options are available?",  # semantic (Jaccard ~0.57)
    "What health insurance plans are available for employees?",  # exact repeat
    "What health insurance plans does Acme offer?",  # semantic (Jaccard ~0.50)
    # Group 3 — Onboarding process
    "What is the onboarding process for new hires?",
    "What is the onboarding process for new employees?",  # semantic (Jaccard ~0.67)
    "What is the onboarding process for new hires?",  # exact repeat
    "What is the new hire onboarding process?",  # semantic (Jaccard ~0.67)
    # Group 4 — Remote work
    "Can employees work remotely at Acme?",
    "Can employees work remotely from home?",  # semantic (Jaccard ~0.60)
    "Can employees work remotely at Acme?",  # exact repeat
    "Can Acme employees work remotely part time?",  # semantic (Jaccard ~0.56)
    # Group 5 — Compensation
    "How is employee compensation determined at Acme?",
    "How is employee compensation calculated at Acme?",  # semantic (Jaccard ~0.67)
    "How is employee compensation determined at Acme?",  # exact repeat
]


def run_workload() -> None:
    """Run the query workload and print formatted results."""
    print("=" * 60)
    print("  Day 10 — LLM Cost & FinOps: Caching + Cost Accounting")
    print("=" * 60)
    print()
    print(f"[WORKLOAD] Running {len(WORKLOAD)} queries (repeated + paraphrased)...")
    print()

    service = CachedAnswerService(model_tier=DEFAULT_MODEL_TIER)

    for i, query in enumerate(WORKLOAD, start=1):
        result, record = service.ask(query)

        # Determine display labels
        if record.cache_type == "exact":
            exact_label = "EXACT-HIT "
            sem_label = "      -- "
            status = "CACHE HIT"
        elif record.cache_type == "semantic":
            exact_label = "EXACT-MISS"
            sem_label = "SEM-HIT  "
            status = "CACHE HIT"
        else:
            exact_label = "EXACT-MISS"
            sem_label = "SEM-MISS "
            status = "LLM call "

        truncated_q = query[:55] + ("…" if len(query) > 55 else "")
        print(
            f"  Q{i:02d} [{exact_label}] [{sem_label}] → {status} "
            f'| ${record.cost_usd:.6f} | "{truncated_q}"'
        )

    # Summary report
    stats = service.report()
    print()
    print("=" * 60)
    print("  COST & CACHE REPORT")
    print("=" * 60)
    print()
    print(f"  Total queries          : {stats['total_queries']}")
    print(
        f"  Exact-match cache hits : {stats['exact_hits']}"
        f"   ({stats['exact_hit_rate'] * 100:.1f}%)"
    )
    print(
        f"  Semantic cache hits    : {stats['semantic_hits']}"
        f"   ({stats['semantic_hit_rate'] * 100:.1f}%)"
    )
    print(f"  Combined cache hit rate: {stats['combined_hit_rate'] * 100:.1f}%")
    print(
        f"  LLM calls made         : {stats['llm_calls']}"
        f"   ({(stats['llm_calls'] / stats['total_queries']) * 100:.1f}%)"
    )
    print()
    print(
        f"  Simulated LLM cost (no cache) : ${stats['simulated_no_cache_cost_usd']:.6f}"
    )
    print(f"  Actual cost (with cache)      : ${stats['total_cost_usd']:.6f}")
    print(
        f"  Simulated $ saved             : ${stats['simulated_savings_usd']:.6f}"
        f"  ({stats['simulated_savings_pct']:.1f}% savings)"
    )
    print()

    # LiteLLM router config reference
    print("=" * 60)
    print("  LITELLM ROUTER CONFIG (reference — no key required)")
    print("=" * 60)
    for line in LITELLM_ROUTER_CONFIG.strip().splitlines():
        print(f"  {line}")
    print("=" * 60)
    print()
    print("[DONE] solution.py completed successfully.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_workload()
