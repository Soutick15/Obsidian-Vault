#!/usr/bin/env python3
"""
Capstone Module 3: RAG Retrieval Metrics
Compute Precision@k, Recall@k, and MRR for the HR assistant's retrieval.

Run standalone:
    python rag_metrics.py
"""
import sys
import pathlib
from dataclasses import dataclass
from typing import List

_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "labs" / "qa" / "_shared"))
from hr_assistant import answer


@dataclass
class RetrievalCase:
    question: str
    relevant_keywords: List[str]  # keywords that should appear in relevant contexts
    k: int = 3


@dataclass
class RetrievalMetrics:
    question: str
    precision_at_k: float
    recall_at_k: float    # approximate: fraction of keywords found in any retrieved context
    mrr: float            # mean reciprocal rank


# TODO 1: Compute Precision@k.
#
# A retrieved context is considered "relevant" if ANY keyword from `relevant_keywords`
# appears in it (case-insensitive substring match).
#
# precision@k = (number of relevant contexts in top-k) / k
#
# Parameters:
#   contexts         — the list of retrieved contexts (already limited to top-k by the SUT)
#   relevant_keywords — list of strings; a context is relevant if it contains any of them
#   k                — the cutoff (use min(k, len(contexts)) to be safe)
#
# Example:
#   contexts = ["PTO is 15 days.", "Health insurance info.", "Remote work allowed."]
#   relevant_keywords = ["15", "pto", "vacation"]
#   k = 3
#   → contexts[0] contains "15" and "pto" → relevant
#   → contexts[1] does not contain any keyword → not relevant
#   → contexts[2] does not contain any keyword → not relevant
#   → precision@3 = 1/3 ≈ 0.333
def precision_at_k(contexts: List[str], relevant_keywords: List[str], k: int) -> float:
    raise NotImplementedError("TODO 1: Implement precision@k")


# TODO 2: Compute approximate Recall@k.
#
# This is an approximation because we do not know the full set of relevant documents —
# only the keywords that should appear somewhere in the retrieved results.
#
# recall@k = (number of relevant_keywords found in ANY of the top-k contexts) / len(relevant_keywords)
#
# A keyword is "found" if it appears (case-insensitive) in at least one of the top-k contexts.
# If relevant_keywords is empty, return 1.0.
#
# Example:
#   contexts = ["PTO is 15 days.", "Health insurance info.", "Remote work allowed."]
#   relevant_keywords = ["15", "pto", "vacation"]
#   k = 3
#   → "15" found in contexts[0] ✓
#   → "pto" found in contexts[0] ✓
#   → "vacation" not found in any context ✗
#   → recall@3 = 2/3 ≈ 0.667
def recall_at_k(contexts: List[str], relevant_keywords: List[str], k: int) -> float:
    raise NotImplementedError("TODO 2: Implement recall@k")


# TODO 3: Compute MRR (Mean Reciprocal Rank).
#
# MRR measures how early the first relevant context appears in the ranked list.
# For a single query: MRR = 1 / rank_of_first_relevant_context
# If no relevant context is found, MRR = 0.0.
#
# Rank is 1-indexed: the first context has rank 1.
#
# Example:
#   contexts = ["Health insurance info.", "PTO is 15 days.", "Remote work allowed."]
#   relevant_keywords = ["15", "pto", "vacation"]
#   → contexts[0] ("Health insurance info.") is NOT relevant
#   → contexts[1] ("PTO is 15 days.") IS relevant → rank = 2
#   → MRR = 1/2 = 0.5
#
# Note: do NOT return 1.0 when no relevant context is found. Return 0.0.
def compute_mrr(contexts: List[str], relevant_keywords: List[str]) -> float:
    raise NotImplementedError("TODO 3: Implement MRR")


# TODO 4: Evaluate a list of RetrievalCase items.
#
# For each case:
#   1. Call answer(case.question, k=case.k) to get the SUT response.
#   2. Extract result["contexts"].
#   3. Compute precision_at_k, recall_at_k, and compute_mrr using the retrieved contexts.
#   4. Build and return a RetrievalMetrics dataclass.
# Return a list of RetrievalMetrics, one per case.
def evaluate_retrieval(cases: List[RetrievalCase]) -> List[RetrievalMetrics]:
    raise NotImplementedError("TODO 4: Implement evaluate_retrieval")


# Default evaluation cases.
# relevant_keywords are clues about what a "good" retrieval looks like for each question.
DEFAULT_CASES = [
    RetrievalCase(
        "How many PTO days do new employees get?",
        ["15", "pto", "vacation", "accrual"],
    ),
    RetrievalCase(
        "What is the remote work policy?",
        ["remote", "home", "work from"],
    ),
    RetrievalCase(
        "What health insurance benefits are offered?",
        ["health", "insurance", "medical"],
    ),
]

if __name__ == "__main__":
    print("=== RAG METRICS REPORT ===")
    results = evaluate_retrieval(DEFAULT_CASES)
    for r in results:
        print(f"\nQ: {r.question[:60]}")
        print(f"   Precision@k: {r.precision_at_k:.2f}  Recall@k: {r.recall_at_k:.2f}  MRR: {r.mrr:.2f}")
    avg_p = sum(r.precision_at_k for r in results) / len(results)
    avg_r = sum(r.recall_at_k for r in results) / len(results)
    avg_mrr = sum(r.mrr for r in results) / len(results)
    print(f"\nAverages — Precision@k: {avg_p:.2f}  Recall@k: {avg_r:.2f}  MRR: {avg_mrr:.2f}")
