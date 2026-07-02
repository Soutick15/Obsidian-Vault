"""
Day 10 — Cost Management & FinOps: Caching + Cost Accounting
DevOps Track | Starter file — work through the TODO markers in order.

Run:
    python labs/devops/day-10/starter.py

No API key required. All LLM calls use the deterministic mock in the shared
service. Set ANTHROPIC_API_KEY or OPENAI_API_KEY to use a real provider.

Shared service import (do not modify):
    sys.path.insert(...) wires labs/devops/_shared/ onto the path so that
    `from service import answer` works regardless of your cwd.
"""

from __future__ import annotations

import pathlib
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Shared service import — do not modify
# ---------------------------------------------------------------------------
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from service import answer  # noqa: E402  (import after sys.path manipulation)

# ---------------------------------------------------------------------------
# Pricing table (illustrative — provider-flexible)
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
# LiteLLM Router Config — documented reference (no key required to study)
# ---------------------------------------------------------------------------
LITELLM_ROUTER_CONFIG = """
# litellm_router_config.yaml
# -----------------------------------------------------------------
# Production router: cheap-first routing with quality fallback.
# Install: pip install litellm
# Usage:   router = Router(model_list=..., routing_strategy="cost-based")
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
  routing_strategy: "least-busy"   # options: least-busy | cost-based | latency-based
                                    # NOTE: the curriculum teaches "cost-based" as the
                                    # recommended default; "least-busy" is shown here for
                                    # illustration — change to "cost-based" in production.
  num_retries: 2
  timeout: 30                       # seconds per attempt
  retry_after: 1                    # seconds between retries
  fallbacks:
    # If fast-answerer fails (5xx / 429 / timeout), escalate to quality-answerer.
    # Note: fallback triggers on PROVIDER ERROR, not on semantic quality.
    - {"fast-answerer": ["quality-answerer"]}
  allowed_fails: 1                  # allowed failures before marking model unhealthy
  cooldown_time: 60                 # seconds to wait before retrying unhealthy model
"""

# ---------------------------------------------------------------------------
# Helper: approximate token count (word-split, ~1.3 tokens/word)
# ---------------------------------------------------------------------------


def approx_tokens(text: str) -> int:
    """Approximate token count: word count × 1.3 (rough GPT/Claude heuristic)."""
    words = len(text.split())
    return max(1, int(words * 1.3))


# ===========================================================================
# TODO-1: ExactCache
# ===========================================================================
# Implement an in-memory exact-match cache.
#
# Requirements:
#   - Normalise the query before storing/looking up (lowercase + strip).
#   - `get(query)` returns the cached dict (as returned by `answer()`) or None.
#   - `put(query, result)` stores the result under the normalised key.
#   - `size` property returns the number of cached entries.
#
# Hint: a plain dict is all you need.
# ===========================================================================


class ExactCache:
    """In-memory exact-match cache keyed on normalised query string."""

    def __init__(self) -> None:
        # TODO-1a: initialise your cache storage here
        raise NotImplementedError("TODO-1a: initialise storage")

    @staticmethod
    def _normalise(query: str) -> str:
        """Lowercase and strip leading/trailing whitespace."""
        # TODO-1b: return a normalised key
        raise NotImplementedError("TODO-1b: normalise key")

    def get(self, query: str) -> dict[str, Any] | None:
        """Return cached result or None."""
        # TODO-1c: look up normalised key; return result or None
        raise NotImplementedError("TODO-1c: cache get")

    def put(self, query: str, result: dict[str, Any]) -> None:
        """Store result under normalised key."""
        # TODO-1d: store result
        raise NotImplementedError("TODO-1d: cache put")

    @property
    def size(self) -> int:
        # TODO-1e: return number of entries
        raise NotImplementedError("TODO-1e: cache size")


# ===========================================================================
# TODO-2: SemanticCache
# ===========================================================================
# Implement a semantic cache using lexical normalisation + Jaccard similarity.
#
# Normalisation steps (in order):
#   1. Lowercase.
#   2. Remove punctuation (keep letters, digits, spaces).
#   3. Split into tokens.
#   4. Remove stopwords (use STOPWORDS set below).
#   5. Sort tokens alphabetically (order-independent matching).
#
# Similarity: Jaccard(A, B) = |A ∩ B| / |A ∪ B|  where A, B are token sets.
#
# `get(query, threshold=0.55)`:
#   - Normalise the incoming query.
#   - Compute Jaccard similarity against every cached entry's normalised tokens.
#   - If the best match >= threshold, return its cached result.
#   - Otherwise return None.
#
# `put(query, result)`:
#   - Normalise query to token set.
#   - Store (token_set, result) in the cache list.
#
# Hint: store a list of (frozenset_of_tokens, result) tuples.
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
    """Lexical-normalisation semantic cache with Jaccard similarity matching."""

    def __init__(self) -> None:
        # TODO-2a: initialise cache storage as a list of (frozenset, result) pairs
        raise NotImplementedError("TODO-2a: initialise storage")

    @staticmethod
    def _normalise(query: str) -> frozenset[str]:
        """
        Return a frozenset of significant tokens.
        Steps: lowercase → remove punctuation → split → remove stopwords.
        """
        # TODO-2b: implement normalisation and return frozenset
        raise NotImplementedError("TODO-2b: normalise to token set")

    @staticmethod
    def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
        """Jaccard similarity: |A ∩ B| / |A ∪ B|. Returns 0.0 if both empty."""
        # TODO-2c: implement Jaccard similarity
        raise NotImplementedError("TODO-2c: Jaccard similarity")

    def get(self, query: str, threshold: float = 0.30) -> dict[str, Any] | None:
        """Return best-match cached result if Jaccard >= threshold, else None."""
        # TODO-2d: normalise query, iterate cache, find best Jaccard match
        raise NotImplementedError("TODO-2d: semantic cache get")

    def put(self, query: str, result: dict[str, Any]) -> None:
        """Add (normalised_tokens, result) to the cache."""
        # TODO-2e: normalise and store
        raise NotImplementedError("TODO-2e: semantic cache put")

    @property
    def size(self) -> int:
        # TODO-2f: return number of entries
        raise NotImplementedError("TODO-2f: cache size")


# ===========================================================================
# TODO-3: CostEstimator
# ===========================================================================
# Implement a token-cost estimator and per-request cost record.
#
# Requirements:
#   - `estimate(question, result, model_tier)` returns a CostRecord.
#     - `input_tokens`  = approx_tokens(question)
#     - `output_tokens` = approx_tokens(result["answer"])
#     - `cost_usd`      = computed from PRICE_TABLE[model_tier]
#   - For cache hits, cost_usd must be 0.0 and cache_hit must be True.
#
# The CostRecord dataclass is provided below — do not modify it.
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

    def estimate(
        self,
        question: str,
        result: dict[str, Any],
        cache_hit: bool = False,
        cache_type: str = "none",
    ) -> CostRecord:
        """
        Return a CostRecord for this request.
        If cache_hit is True, cost_usd must be 0.0.
        """
        # TODO-3: compute input_tokens, output_tokens, cost_usd
        # Remember: cost = 0.0 if cache_hit
        # PRICE_TABLE values are per 1,000 tokens
        raise NotImplementedError("TODO-3: implement CostEstimator.estimate")


# ===========================================================================
# TODO-4: CachedAnswerService
# ===========================================================================
# Orchestrate the full cache → LLM pipeline.
#
# `ask(question)` must:
#   1. Check ExactCache → if hit, return (result, CostRecord(cache_hit=True, cache_type="exact"))
#   2. Check SemanticCache → if hit, return (result, CostRecord(cache_hit=True, cache_type="semantic"))
#   3. Call `answer(question)` from the shared service.
#   4. Store result in BOTH caches.
#   5. Return (result, CostRecord(cache_hit=False, cache_type="none"))
#
# Also maintain:
#   - `self.records: list[CostRecord]` — one per call to `ask()`
#   - `self.exact_hits: int`
#   - `self.semantic_hits: int`
#   - `self.llm_calls: int`
# ===========================================================================


class CachedAnswerService:
    """Cache + cost-accounting wrapper around the shared `answer()` function."""

    def __init__(self, model_tier: str = DEFAULT_MODEL_TIER) -> None:
        # TODO-4a: initialise ExactCache, SemanticCache, CostEstimator, counters
        raise NotImplementedError("TODO-4a: initialise caches and estimator")

    def ask(self, question: str) -> tuple[dict[str, Any], CostRecord]:
        """
        Return (answer_result, cost_record).
        Check caches first; fall through to LLM only on full miss.
        """
        # TODO-4b: implement exact → semantic → LLM pipeline
        raise NotImplementedError("TODO-4b: implement ask()")

    def report(self) -> dict[str, Any]:
        """Return summary statistics over all recorded requests."""
        # TODO-4c: compute and return the report dict
        # Keys to include:
        #   total_queries, exact_hits, semantic_hits, combined_hits,
        #   exact_hit_rate, semantic_hit_rate, combined_hit_rate,
        #   llm_calls, total_cost_usd, simulated_no_cache_cost_usd,
        #   simulated_savings_usd, simulated_savings_pct
        raise NotImplementedError("TODO-4c: implement report()")


# ===========================================================================
# TODO-5: run_workload
# ===========================================================================
# Drive a workload of 20 queries through CachedAnswerService and print
# a formatted report.
#
# The WORKLOAD list below contains repeated and paraphrased queries.
# For each query:
#   - Call service.ask(query)
#   - Print a one-liner showing query number, cache status, cost, and query text
#     (truncated to 55 chars).
# After all queries, call service.report() and print the summary table.
# Finally, print LITELLM_ROUTER_CONFIG.
#
# Format hint (match README expected output):
#   "  Q{n:02d} [EXACT-{HIT/MISS}] [SEM-{HIT/MISS/--}] → {status} | ${cost:.6f} | {query[:55]}"
#   where status = "CACHE HIT" or "LLM call  "
#   Use "[      -- ]" for SEM column when exact hit (skip semantic check).
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
    """Run the query workload and print results."""
    # TODO-5: implement the workload runner
    raise NotImplementedError("TODO-5: implement run_workload()")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_workload()
