#!/usr/bin/env python3
"""
Capstone Module 2: LLM-as-Judge Scorer (Mock)
Scores SUT answers on a 1-5 scale without requiring an API key.
Uses keyword heuristics as a proxy for LLM judgment.

Run standalone:
    python judge.py
"""
import sys
import pathlib
from dataclasses import dataclass
from typing import List

_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "labs" / "qa" / "_shared"))
from hr_assistant import answer


@dataclass
class JudgeScore:
    question: str
    answer_text: str
    helpfulness: int     # 1-5
    faithfulness: int    # 1-5
    explanation: str


# TODO 1: Implement the mock judge scorer.
#
# This function simulates what a real LLM judge would do, using simple heuristics instead
# of an API call. The goal is to produce a score that correlates with answer quality.
#
# Scoring rubric to implement:
#
#   helpfulness (1-5):
#     5 — answer is >= 80 characters AND contains at least one number or specific policy term
#         (look for digits, "days", "policy", "eligible", "required", "percent", etc.)
#     4 — answer is >= 50 characters
#     3 — answer is >= 20 characters but vague (no numbers or policy terms)
#     2 — answer is < 20 characters but non-empty
#     1 — answer is empty or contains only whitespace
#
#   faithfulness (1-5):
#     5 — >= 2 key terms from contexts appear in the answer
#     4 — 1 key term from contexts appears in the answer
#     3 — answer is non-empty but no context terms found (answer may be paraphrased)
#     2 — answer contains claims that appear to contradict a context
#         (hint: look for numbers in answer that differ from numbers in any context)
#     1 — answer is empty
#
#   explanation:
#     A single string summarizing both scores. Examples:
#       "Helpfulness 5: specific and detailed. Faithfulness 5: 3 context terms found."
#       "Helpfulness 3: answer present but vague. Faithfulness 2: answer says '20' but context says '15'."
#
# Implementation tips:
#   - To find "key terms from contexts", split each context into words, filter for words >= 4 chars,
#     and check if any appear in the answer (case-insensitive).
#   - To detect number contradictions, extract all integers from the answer and from contexts,
#     then check for mismatches.
#   - Keep the logic readable — a long if/elif chain is fine here.
def mock_judge(question: str, answer_text: str, contexts: List[str]) -> JudgeScore:
    raise NotImplementedError("TODO 1: Implement mock_judge")


# TODO 2: Run the judge over a list of (question, answer_text, contexts) tuples.
#
# For each tuple, call mock_judge() and collect the JudgeScore.
# Compute:
#   avg_helpfulness  = mean of all helpfulness scores
#   avg_faithfulness = mean of all faithfulness scores
# Return (scores: List[JudgeScore], avg_helpfulness: float, avg_faithfulness: float).
#
# Edge case: if test_cases is empty, return ([], 0.0, 0.0).
def run_judge_suite(test_cases: List[tuple]) -> tuple:
    raise NotImplementedError("TODO 2: Implement run_judge_suite")


# Default test cases for standalone run.
# None values for answer and contexts mean "call the SUT and fill in at runtime".
DEFAULT_CASES = [
    ("How many PTO days do new employees get?", None, None),
    ("What is the remote work policy?", None, None),
    ("What benefits are available?", None, None),
]

if __name__ == "__main__":
    print("=== JUDGE REPORT ===")
    # Resolve None cases by calling the SUT
    resolved = []
    for q, a, c in DEFAULT_CASES:
        if a is None:
            result = answer(q)
            a, c = result["answer"], result["contexts"]
        resolved.append((q, a, c))

    scores, avg_helpfulness, avg_faithfulness = run_judge_suite(resolved)
    for s in scores:
        print(f"\nQ: {s.question[:60]}")
        print(f"   Helpfulness: {s.helpfulness}/5  Faithfulness: {s.faithfulness}/5")
        print(f"   {s.explanation}")
    print(f"\nAvg helpfulness: {avg_helpfulness:.2f}/5  Avg faithfulness: {avg_faithfulness:.2f}/5")
