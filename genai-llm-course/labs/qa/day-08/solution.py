"""
Day 8 Lab — Local Evaluation Harness (Solution)
================================================
Reference implementation. Run with:

    python labs/qa/day-08/solution.py

No API key required.

At the bottom of this file you will also find documented reference material
for promptfoo and deepeval — these sections are MARKED as requiring an API key
and are provided as educational reference, not executable code in this script.
"""

import pathlib
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# SUT import
# ---------------------------------------------------------------------------
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from hr_assistant import answer  # noqa: E402

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class GoldenItem:
    """One entry in the golden evaluation dataset."""

    id: str
    question: str
    expected_contains: list[str]  # must appear in the generated claim (pre-context)
    faithfulness_claims: list[str]  # must appear in at least one retrieved context
    forbidden_in_claim: list[str] = field(
        default_factory=list
    )  # must NOT appear in claim
    source_doc: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class EvalResult:
    """Scored result for one golden item."""

    item: GoldenItem
    answer: str
    claim: str  # generated claim extracted from answer
    contexts: list[str]
    contains_pass: bool
    faithfulness_pass: bool
    contains_failures: list[str]
    faithfulness_failures: list[str]

    @property
    def passed(self) -> bool:
        return self.contains_pass and self.faithfulness_pass


# ---------------------------------------------------------------------------
# Golden dataset
# ---------------------------------------------------------------------------


def extract_claim(answer_text: str) -> str:
    """
    Extract only the generated claim portion of the answer — the text before
    the 'Supporting context:' separator that the SUT appends.

    The SUT for the PTO question produces:
        "Based on Acme Corp policy, employees receive **20 days of PTO per year**
         starting from their first day of employment.

         Supporting context:
         [Vacation / PTO] Acme Corp uses an accrual-based PTO model: ... 15 days ..."

    Checking the whole answer string would find "15" in the appended context and
    incorrectly pass. We want to check only what the model *claimed*, not what
    context it pasted in.
    """
    separator = "Supporting context:"
    if separator in answer_text:
        return answer_text.split(separator)[0].strip()
    return answer_text.strip()


def build_golden_set() -> list[GoldenItem]:
    """
    Golden Q&A set grounded in the Acme HR corpus.

    Q1 is the regression item for Seeded Issue #1: the SUT states "20 days of
    PTO per year" in its generated claim, but the corpus says 15 days for
    employees with 0–2 years of service.

    Detection strategy:
      - expected_contains=["15"] checks the generated claim portion only.
        Because the claim says "20 days" and never mentions "15", this FAILS.
      - forbidden_in_claim=["20 days"] asserts the hallucinated value is absent
        from the claim — also FAILS.
      - faithfulness_claims=["15 days"] checks that the correct value appears
        in the retrieved contexts — this PASSES (context is correct), confirming
        the bug is in the generated claim, not the retrieval.
    """
    return [
        GoldenItem(
            id="Q1-pto",
            question="How many PTO days do new employees get in their first two years?",
            # "15" must appear in the generated claim (it does NOT — SUT says "20 days")
            expected_contains=["15"],
            # The correct fact must appear in at least one retrieved context
            faithfulness_claims=["15 days"],
            # Hallucinated value must NOT appear in the generated claim
            forbidden_in_claim=["20 days"],
            source_doc="leave-and-pto-policy.md",
            tags=["regression", "faithfulness", "pto"],
        ),
        GoldenItem(
            id="Q2-parental-leave",
            question="What is the parental leave policy for a non-birth parent?",
            expected_contains=["parental leave"],
            faithfulness_claims=["parental leave"],
            source_doc="leave-and-pto-policy.md",
            tags=["leave"],
        ),
        GoldenItem(
            id="Q3-hiring-stages",
            question="What are the stages of the hiring process at Acme Corp?",
            expected_contains=["hiring"],
            faithfulness_claims=["hiring"],
            source_doc="recruitment-and-hiring-process.md",
            tags=["recruitment"],
        ),
        GoldenItem(
            id="Q5-401k",
            question="How much does Acme Corp match on 401(k) contributions?",
            expected_contains=["401"],
            faithfulness_claims=["401"],
            source_doc="benefits-and-insurance.md",
            tags=["benefits"],
        ),
        GoldenItem(
            id="Q6-home-office",
            question="What is the home office setup stipend for new remote employees?",
            expected_contains=["stipend", "remote"],
            faithfulness_claims=["stipend"],
            source_doc="remote-work-policy.md",
            tags=["remote"],
        ),
    ]


# ---------------------------------------------------------------------------
# Metric: contains check (operates on the generated claim, not full answer)
# ---------------------------------------------------------------------------


def run_contains_check(
    claim: str,
    expected_contains: list[str],
    forbidden: list[str],
) -> tuple[bool, list[str]]:
    """
    Two-part check on the generated claim portion of the answer:
      1. Every string in expected_contains must appear (case-insensitive).
      2. Every string in forbidden must NOT appear (case-insensitive).

    Operating on the claim (not the full answer) prevents the appended
    "Supporting context:" block from masking missing or wrong values.

    Returns (all_passed, failure_descriptions).
    """
    claim_lower = claim.lower()
    failures: list[str] = []

    for req in expected_contains:
        if req.lower() not in claim_lower:
            failures.append(f"required {req!r} not found in claim")

    for forbidden_str in forbidden:
        if forbidden_str.lower() in claim_lower:
            failures.append(
                f"forbidden {forbidden_str!r} found in claim (hallucination)"
            )

    return len(failures) == 0, failures


# ---------------------------------------------------------------------------
# Metric: faithfulness check (local keyword proxy)
# ---------------------------------------------------------------------------


def run_faithfulness_check(
    claims: list[str], contexts: list[str]
) -> tuple[bool, list[str]]:
    """
    For each reference claim (i.e. a fact that SHOULD appear in the retrieved
    context), verify it appears in at least one context string (case-insensitive).

    This confirms the retrieval step found the right information. When a
    faithfulness_claim is present in context but ABSENT from the generated
    claim, that confirms a faithfulness bug: the model had the right source
    but stated a different (wrong) value.

    Returns (all_passed, unsupported_claims).
    """
    unsupported = []
    for claim in claims:
        claim_lower = claim.lower()
        supported = any(claim_lower in ctx.lower() for ctx in contexts)
        if not supported:
            unsupported.append(claim)
    return len(unsupported) == 0, unsupported


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_item(item: GoldenItem) -> EvalResult:
    """Call SUT, run both checks, return a scored EvalResult."""
    result_dict = answer(item.question)
    answer_text: str = result_dict["answer"]
    contexts: list[str] = result_dict.get("contexts", [])

    # Extract only the generated claim — before the "Supporting context:" block
    claim = extract_claim(answer_text)

    contains_pass, contains_failures = run_contains_check(
        claim, item.expected_contains, item.forbidden_in_claim
    )
    faith_pass, faith_failures = run_faithfulness_check(
        item.faithfulness_claims, contexts
    )

    # For faithfulness bug detection: if the claim does NOT contain a value
    # that IS in the contexts, surface this in the contains failures as well.
    # This makes the report explain the contradiction clearly.
    context_correct = all(
        any(fc.lower() in ctx.lower() for ctx in contexts)
        for fc in item.faithfulness_claims
    )
    claim_correct = all(fc.lower() in claim.lower() for fc in item.faithfulness_claims)

    if context_correct and not claim_correct:
        # Retrieval found the right facts; model stated different ones
        for fc in item.faithfulness_claims:
            if fc.lower() not in claim.lower() and not any(
                f"claim contradicts context" in cf for cf in contains_failures
            ):
                contains_failures.append(
                    f"claim contradicts context: context has {fc!r} but claim does not"
                )
        contains_pass = False

    return EvalResult(
        item=item,
        answer=answer_text,
        claim=claim,
        contexts=contexts,
        contains_pass=contains_pass,
        faithfulness_pass=faith_pass,
        contains_failures=contains_failures,
        faithfulness_failures=faith_failures,
    )


# ---------------------------------------------------------------------------
# Harness runner
# ---------------------------------------------------------------------------


def run_harness(golden_set: list[GoldenItem]) -> list[EvalResult]:
    """Score every golden item and return results."""
    results = []
    for item in golden_set:
        print(f"  Scoring {item.id}: {item.question[:60]}...")
        results.append(score_item(item))
    return results


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def print_report(results: list[EvalResult]) -> None:
    """Print a human-readable pass/fail report to stdout."""
    width = 62
    sep = "=" * width

    print()
    print(sep)
    print(" Acme HR Eval Harness — Day 8")
    print(sep)
    print()

    failed_results = []

    for r in results:
        q_short = r.item.question[:65] + ("…" if len(r.item.question) > 65 else "")
        status = "PASS" if r.passed else "FAIL"
        marker = "[PASS]" if r.passed else "[FAIL]"
        print(f"{marker} {r.item.id}: {q_short}")

        if not r.passed:
            failed_results.append(r)
            claim_preview = r.claim[:120].replace("\n", " ") + (
                "…" if len(r.claim) > 120 else ""
            )
            print(f"       Claim : {claim_preview}")

            if r.contains_failures:
                for detail in r.contains_failures:
                    print(f"       [contains FAIL] {detail}")

            if r.faithfulness_failures:
                for claim in r.faithfulness_failures:
                    print(
                        f"       [faithfulness FAIL] Claim not in retrieved contexts: {claim!r}"
                    )
                    print(f"       → This signals a hallucination or faithfulness bug.")

        print()

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    score = 100.0 * passed / total if total else 0.0

    print(sep)
    print(" SUMMARY")
    print(sep)
    print(f"  Passed : {passed} / {total}")
    print(f"  Failed : {failed} / {total}")
    print(f"  Score  : {score:.1f}%")
    print()

    if failed_results:
        print("  FAILURES:")
        for r in failed_results:
            print(f"    [{r.item.id}]")
            for detail in r.contains_failures:
                print(f"      - {detail}")
            for uf in r.faithfulness_failures:
                print(
                    f"      - faithfulness: reference fact {uf!r} absent from contexts"
                )
            # Highlight the seeded bug explicitly
            pto_bug = any("20 days" in cf for cf in r.contains_failures)
            if pto_bug:
                print(
                    "      *** Seeded Issue #1 detected: claim states '20 days PTO'; "
                    "corpus says 15 days for 0–2 yrs of service ***"
                )
        print()

    print(sep)
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    print("Building golden dataset...")
    golden_set = build_golden_set()
    print(f"Golden set: {len(golden_set)} items\n")

    print("Running eval harness...")
    results = run_harness(golden_set)

    print_report(results)

    failed = [r for r in results if not r.passed]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()


# =============================================================================
# REFERENCE MATERIAL — promptfoo (requires API key + Node.js)
# =============================================================================
#
# Save the content below as:  labs/qa/day-08/promptfooconfig.yaml
# Run with:
#   npm install -g promptfoo
#   export ANTHROPIC_API_KEY=sk-ant-...   (or OPENAI_API_KEY)
#   npx promptfoo eval --config labs/qa/day-08/promptfooconfig.yaml
#
# ---------------------------------------------------------------------------
PROMPTFOO_CONFIG_YAML = """\
# promptfooconfig.yaml
# Day 8 — HR Assistant eval suite
# Requires: API key (Anthropic or OpenAI) and Node.js / npm

prompts:
  - "{{question}}"

providers:
  # Swap to openai:gpt-5-mini or anthropic:claude-haiku-4-5 etc.
  - anthropic:claude-haiku-4-5

defaultTest:
  options:
    provider: anthropic:claude-haiku-4-5

tests:
  # Q1 — PTO regression (Seeded Issue #1)
  # The real HR assistant (not the mock) should say 15 days for new employees.
  - description: "PTO days for new employees"
    vars:
      question: "How many PTO days do new employees get in their first two years?"
    assert:
      - type: contains
        value: "15"
      - type: not-contains
        value: "20 days"

  # Q2 — Parental leave
  - description: "Non-birth parent parental leave"
    vars:
      question: "What is the parental leave policy for a non-birth parent?"
    assert:
      - type: contains
        value: "parental leave"

  # Q3 — Hiring stages
  - description: "Hiring process stages"
    vars:
      question: "What are the stages of the hiring process at Acme Corp?"
    assert:
      - type: contains
        value: "hiring"
      - type: llm-rubric
        value: "Response describes a multi-stage hiring process"

  # Q5 — 401k match
  - description: "401k contribution match"
    vars:
      question: "How much does Acme Corp match on 401(k) contributions?"
    assert:
      - type: contains
        value: "401"

  # Q6 — Home office stipend
  - description: "Remote home office stipend"
    vars:
      question: "What is the home office setup stipend for new remote employees?"
    assert:
      - type: contains
        value: "stipend"
"""


# =============================================================================
# REFERENCE MATERIAL — deepeval (requires API key)
# =============================================================================
#
# Save the content below as:  labs/qa/day-08/test_deepeval_example.py
# Install:   pip install deepeval
# Set key:   export OPENAI_API_KEY=sk-...   (deepeval uses OpenAI as judge by default)
# Run:       pytest labs/qa/day-08/test_deepeval_example.py -v
#
# ---------------------------------------------------------------------------
DEEPEVAL_EXAMPLE_PY = """\
# test_deepeval_example.py
# Day 8 — HR Assistant eval with deepeval
# =========================================
# REQUIRES: pip install deepeval
#           export OPENAI_API_KEY=sk-...
#
# deepeval uses an LLM as a judge for metrics like FaithfulnessMetric.
# The same logical checks as the local harness, but with richer NLU scoring.

import sys
import pathlib

import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

# Import the SUT
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from hr_assistant import answer


# ---------------------------------------------------------------------------
# Helper: run SUT and build a deepeval LLMTestCase
# ---------------------------------------------------------------------------

def make_test_case(question: str) -> tuple[LLMTestCase, list[str]]:
    result = answer(question)
    return (
        LLMTestCase(
            input=question,
            actual_output=result["answer"],
            retrieval_context=result.get("contexts", []),
        ),
        result.get("contexts", []),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_pto_faithfulness():
    \\"\\"\\"
    Seeded Issue #1: SUT states 20 days; corpus says 15 days.
    FaithfulnessMetric should score this low and fail the assertion.
    \\"\\"\\"
    metric = FaithfulnessMetric(threshold=0.7)
    test_case, _ = make_test_case(
        "How many PTO days do new employees get in their first two years?"
    )
    # This test is EXPECTED TO FAIL against the seeded SUT.
    # The SUT's answer (20 days) is not supported by the retrieved context (15 days).
    assert_test(test_case, [metric])


def test_parental_leave_relevancy():
    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case, _ = make_test_case(
        "What is the parental leave policy for a non-birth parent?"
    )
    assert_test(test_case, [metric])


def test_hiring_stages_faithfulness():
    metric = FaithfulnessMetric(threshold=0.6)
    test_case, _ = make_test_case(
        "What are the stages of the hiring process at Acme Corp?"
    )
    assert_test(test_case, [metric])
"""
