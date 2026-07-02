#!/usr/bin/env python3
"""
Capstone Module 1: Golden-Set Eval Harness
Build and run a golden-set evaluation harness over the Acme HR Assistant.

Run standalone:
    python eval_harness.py
"""
import sys
import pathlib
from dataclasses import dataclass, field
from typing import List, Optional

_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "labs" / "qa" / "_shared"))
from hr_assistant import answer


@dataclass
class GoldenItem:
    question: str
    expected_contains: List[str]
    faithfulness_claims: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class EvalResult:
    question: str
    passed: bool
    contains_ok: bool
    faithfulness_ok: bool
    failure_reason: Optional[str] = None


# TODO 1: Build a golden set of >= 8 GoldenItem instances.
#
# Cover the following topics and edge cases:
#   - PTO for new employees       → expected_contains=["15"]       (this WILL fail — the SUT has a bug)
#   - Remote work policy          → expected_contains=["remote"] or similar
#   - Onboarding process          → expected_contains=["onboard"] or similar
#   - Health/benefits             → expected_contains=["health", "insurance"] or similar
#   - At least one negative test  → question completely unrelated to HR; expected_contains should be
#                                   something unlikely to appear, so the test verifies the SUT does NOT
#                                   hallucinate an answer. Use tags=["negative"] to mark it.
#
# Include faithfulness_claims on at least 3 items. A faithfulness claim is a short phrase that
# MUST appear in one of the retrieved context chunks if the answer is to be considered grounded.
# Example: GoldenItem(
#     question="How many PTO days do new employees receive?",
#     expected_contains=["15"],
#     faithfulness_claims=["15 days", "vacation", "accrual"],
#     tags=["pto", "new_employee"],
# )
#
# Tip: call answer(question) in the Python REPL first to explore what the SUT returns.
def build_golden_set() -> List[GoldenItem]:
    raise NotImplementedError("TODO 1: Build the golden set")


# TODO 2: Contains check.
#
# Returns (ok: bool, failure_reason: Optional[str]).
#   - ok is True only when ALL strings in `expected` appear in `answer_text` (case-insensitive).
#   - If ok is False, failure_reason should list which expected strings were missing.
#   - If `expected` is empty, return (True, None) — no constraints means no failure.
#
# Example:
#   check_contains("You receive 20 days of PTO.", ["15"])
#   → (False, "Missing: ['15']")
#
#   check_contains("You receive 15 days of PTO.", ["15", "pto"])
#   → (True, None)
def check_contains(answer_text: str, expected: List[str]) -> tuple:
    raise NotImplementedError("TODO 2: Implement contains check")


# TODO 3: Faithfulness check.
#
# Returns (ok: bool, failure_reason: Optional[str]).
#   - For each claim in `claims`, check whether the claim appears (case-insensitive) in at least
#     one of the context strings.
#   - ok is True only when ALL claims are grounded in at least one context.
#   - If `claims` is empty, return (True, None).
#
# Why this matters: a faithful answer only makes statements that are supported by the retrieved
# contexts. If the answer contains a fact that isn't in any context, it is hallucinated.
#
# Example:
#   check_faithfulness(
#       contexts=["Employees receive 15 days of PTO per year."],
#       claims=["15 days", "PTO"],
#   )
#   → (True, None)
#
#   check_faithfulness(
#       contexts=["Employees enjoy a flexible schedule."],
#       claims=["15 days"],
#   )
#   → (False, "Claims not grounded in context: ['15 days']")
def check_faithfulness(contexts: List[str], claims: List[str]) -> tuple:
    raise NotImplementedError("TODO 3: Implement faithfulness check")


# TODO 4: Score one golden item.
#
# Steps:
#   1. Call answer(item.question) to get the SUT response.
#   2. Run check_contains() on result["answer"] with item.expected_contains.
#   3. Run check_faithfulness() on result["contexts"] with item.faithfulness_claims.
#   4. An item passes only if BOTH checks pass.
#   5. Build and return an EvalResult with all fields populated.
#      - failure_reason: combine both failure messages if both checks failed, or just the one that failed.
#
# Hint: you can join two failure strings with " | ".
def score_item(item: GoldenItem) -> EvalResult:
    raise NotImplementedError("TODO 4: Implement score_item")


# TODO 5: Run the full harness.
#
# If `golden` is None, call build_golden_set() to get the default set.
# Score every item using score_item().
# Compute pass_rate = (number of items that passed) / (total items).
# Return (results: List[EvalResult], pass_rate: float).
#
# AI-generated test cases note (Day 13 pattern):
#   In production, you would generate additional golden items by prompting an LLM with:
#     "Generate 10 realistic HR questions an employee might ask, with expected answer keywords."
#   For this capstone, build_golden_set() fills that role manually.
def run_harness(golden: List[GoldenItem] = None) -> tuple:
    raise NotImplementedError("TODO 5: Implement run_harness")


def print_report(results: List[EvalResult], pass_rate: float):
    """Print a formatted eval report."""
    print("\n=== EVAL HARNESS REPORT ===")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.question[:60]}")
        if r.failure_reason:
            print(f"         {r.failure_reason}")
    print(f"\nPass rate: {pass_rate:.2%} ({sum(r.passed for r in results)}/{len(results)})")


if __name__ == "__main__":
    golden = build_golden_set()
    results, rate = run_harness(golden)
    print_report(results, rate)
