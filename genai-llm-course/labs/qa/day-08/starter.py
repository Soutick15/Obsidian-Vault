"""
Day 8 Lab — Build a Local Evaluation Harness
=============================================
Work through the TODO markers in order (1 → 6).
Run with: python labs/qa/day-08/starter.py

No API key required.
"""

import sys
import pathlib
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# SUT import — do not modify
# ---------------------------------------------------------------------------
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from hr_assistant import answer  # noqa: E402


# ---------------------------------------------------------------------------
# Data structures — do not modify
# ---------------------------------------------------------------------------

@dataclass
class GoldenItem:
    """One entry in the golden evaluation dataset."""
    id: str                                  # short identifier
    question: str                            # input to the SUT
    expected_contains: list[str]             # ALL of these must appear in the generated claim
    faithfulness_claims: list[str]           # each must appear in at least one retrieved context
    forbidden_in_claim: list[str] = field(default_factory=list)  # must NOT appear in the claim
    source_doc: str = ""                     # corpus document (for reference)
    tags: list[str] = field(default_factory=list)


@dataclass
class EvalResult:
    """Scored result for one golden item."""
    item: GoldenItem
    answer: str
    claim: str                       # generated claim extracted from answer (pre-context block)
    contexts: list[str]
    contains_pass: bool
    faithfulness_pass: bool
    contains_failures: list[str]     # which required strings were missing / forbidden found
    faithfulness_failures: list[str] # which claims were unsupported by context

    @property
    def passed(self) -> bool:
        return self.contains_pass and self.faithfulness_pass


# ---------------------------------------------------------------------------
# Helper: extract just the generated claim (before appended context block)
# ---------------------------------------------------------------------------

def extract_claim(answer_text: str) -> str:
    """
    Extract the generated claim portion of the answer.

    The SUT appends raw context chunks after a "Supporting context:" separator.
    Checking the entire answer string would find correct facts in the appended
    context and mask bugs in the actual claim. Split on the separator and return
    only what the model stated as its conclusion.
    """
    separator = "Supporting context:"
    if separator in answer_text:
        return answer_text.split(separator)[0].strip()
    return answer_text.strip()


# ---------------------------------------------------------------------------
# TODO 1 — Build the golden dataset
# ---------------------------------------------------------------------------

def build_golden_set() -> list[GoldenItem]:
    """
    Return a list of GoldenItem covering at least 5 questions from the HR corpus.
    Requirements:
      - Include the PTO regression question (Q1 in the HR corpus README).
        * expected_contains=["15"] — the claim must contain "15" (it won't — SUT says "20 days")
        * forbidden_in_claim=["20 days"] — the hallucinated value must not appear in the claim
        * faithfulness_claims=["15 days"] — this correct fact must appear in retrieved contexts
      - Include at least 4 other questions from the corpus example list.
      - Each item must have realistic expected_contains and faithfulness_claims.

    Hint: refer to data/hr-corpus/README.md for the 10 example questions and
    their source documents.
    """
    # TODO 1: replace the empty list with a populated golden dataset
    golden: list[GoldenItem] = []
    return golden


# ---------------------------------------------------------------------------
# TODO 2 — Contains check (operates on the generated claim, not full answer)
# ---------------------------------------------------------------------------

def run_contains_check(
    claim: str,
    expected_contains: list[str],
    forbidden: list[str],
) -> tuple[bool, list[str]]:
    """
    Two-part check on the generated claim text only (use extract_claim first):
      1. Every string in expected_contains must appear (case-insensitive).
      2. Every string in forbidden must NOT appear (case-insensitive).

    Returns:
        (all_passed: bool, failures: list[str])
        failures is a list of human-readable failure descriptions.
    """
    # TODO 2: implement contains check on the claim
    failures: list[str] = []
    # ... check expected_contains ...
    # ... check forbidden ...
    all_passed = len(failures) == 0
    return all_passed, failures


# ---------------------------------------------------------------------------
# TODO 3 — Faithfulness check
# ---------------------------------------------------------------------------

def run_faithfulness_check(claims: list[str], contexts: list[str]) -> tuple[bool, list[str]]:
    """
    For each reference claim, verify it appears (case-insensitive) in at least
    one retrieved context string. This confirms the retrieval step found the
    right information.

    If a claim is IN the context but NOT in the generated claim, that is the
    signature of a faithfulness bug: correct source, wrong conclusion.

    Returns:
        (all_passed: bool, unsupported: list[str])
    """
    # TODO 3: implement faithfulness check
    unsupported: list[str] = []
    # ... your code here ...
    all_passed = len(unsupported) == 0
    return all_passed, unsupported


# ---------------------------------------------------------------------------
# TODO 4 — Score one item
# ---------------------------------------------------------------------------

def score_item(item: GoldenItem) -> EvalResult:
    """
    Call the SUT, run contains + faithfulness checks, return an EvalResult.

    Steps:
    1. Call answer(item.question) — returns {"answer": str, "contexts": [...], ...}
    2. Extract the claim using extract_claim(answer_text).
    3. Run run_contains_check(claim, item.expected_contains, item.forbidden_in_claim).
    4. Run run_faithfulness_check(item.faithfulness_claims, contexts).
    5. If contexts contain a faithfulness_claim but the claim does not, add a
       contradiction note to contains_failures and set contains_pass=False.
    6. Return a fully populated EvalResult.
    """
    # TODO 4: implement score_item
    result_dict = answer(item.question)
    answer_text = result_dict["answer"]
    contexts = result_dict.get("contexts", [])
    claim = extract_claim(answer_text)

    # ... your code here (run checks and build EvalResult) ...
    raise NotImplementedError("TODO 4: implement score_item")


# ---------------------------------------------------------------------------
# TODO 5 — Run the harness
# ---------------------------------------------------------------------------

def run_harness(golden_set: list[GoldenItem]) -> list[EvalResult]:
    """
    Iterate over the golden set, score each item, collect and return results.
    Print a progress indicator as each item is scored (e.g. "Scoring Q1...").
    """
    # TODO 5: implement run_harness
    results: list[EvalResult] = []
    # ... your code here ...
    return results


# ---------------------------------------------------------------------------
# TODO 6 — Print the report
# ---------------------------------------------------------------------------

def print_report(results: list[EvalResult]) -> None:
    """
    Print a human-readable pass/fail report.

    Format requirements:
    - Header: "Acme HR Eval Harness — Day 8"
    - Per item: [PASS] or [FAIL] with the question text (truncated to 70 chars)
    - For failures: show which contains checks failed and which faithfulness
      claims were unsupported, with a short preview of the answer.
    - Summary: Passed N/M, Score X%, list of all failure IDs with reason.
    - The report MUST make the PTO faithfulness failure obvious.
    """
    # TODO 6: implement print_report
    pass


# ---------------------------------------------------------------------------
# Entry point — do not modify
# ---------------------------------------------------------------------------

def main() -> None:
    golden_set = build_golden_set()
    if not golden_set:
        print("ERROR: golden set is empty — complete TODO 1 first.")
        sys.exit(1)

    results = run_harness(golden_set)
    print_report(results)

    failed = [r for r in results if not r.passed]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
