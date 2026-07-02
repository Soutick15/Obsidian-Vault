"""
test_deepeval_example.py
Day 8 — HR Assistant eval with deepeval
========================================
REQUIRES AN API KEY — this file is documented reference material.

Install:  pip install deepeval
Set key:  export OPENAI_API_KEY=sk-...     (deepeval uses OpenAI as judge by default)
Run:      pytest labs/qa/day-08/test_deepeval_example.py -v

deepeval brings LLM evaluation into the pytest ecosystem. Metrics use an
LLM as a judge, so they are more semantically powerful than local keyword
checks — but require an API call per scored item.

The same logical assertions as the local harness (solution.py), expressed
in deepeval's LLMTestCase / assert_test pattern.
"""

import sys
import pathlib

import pytest

# ---------------------------------------------------------------------------
# SUT import
# ---------------------------------------------------------------------------
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from hr_assistant import answer  # noqa: E402

# ---------------------------------------------------------------------------
# deepeval imports — guarded so the file can be imported without the package
# ---------------------------------------------------------------------------
try:
    from deepeval import assert_test
    from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
    from deepeval.test_case import LLMTestCase
    _DEEPEVAL_AVAILABLE = True
except ImportError:
    _DEEPEVAL_AVAILABLE = False


def _skip_if_no_deepeval():
    if not _DEEPEVAL_AVAILABLE:
        pytest.skip("deepeval not installed — run: pip install deepeval")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_test_case(question: str) -> "LLMTestCase":
    """Call the SUT and wrap the result in a deepeval LLMTestCase."""
    result = answer(question)
    return LLMTestCase(
        input=question,
        actual_output=result["answer"],
        retrieval_context=result.get("contexts", []),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_pto_faithfulness():
    """
    Seeded Issue #1: SUT states '20 days of PTO per year'.
    The corpus says 15 days for employees with 0–2 years of service.

    FaithfulnessMetric checks whether every claim in the actual_output is
    supported by the retrieval_context. Because '20 days' does NOT appear
    in the retrieved corpus chunks, this test is EXPECTED TO FAIL against
    the seeded mock SUT.

    Against a fixed/real assistant it should PASS.
    """
    _skip_if_no_deepeval()
    metric = FaithfulnessMetric(threshold=0.7)
    test_case = make_test_case(
        "How many PTO days do new employees get in their first two years?"
    )
    assert_test(test_case, [metric])  # expected FAIL with seeded SUT


def test_parental_leave_relevancy():
    """Answer relevancy: the response must address parental leave."""
    _skip_if_no_deepeval()
    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = make_test_case(
        "What is the parental leave policy for a non-birth parent?"
    )
    assert_test(test_case, [metric])


def test_hiring_stages_faithfulness():
    """Response about hiring stages must be grounded in retrieved context."""
    _skip_if_no_deepeval()
    metric = FaithfulnessMetric(threshold=0.6)
    test_case = make_test_case(
        "What are the stages of the hiring process at Acme Corp?"
    )
    assert_test(test_case, [metric])


def test_home_office_stipend_relevancy():
    """Response about home office stipend must be on-topic."""
    _skip_if_no_deepeval()
    metric = AnswerRelevancyMetric(threshold=0.7)
    test_case = make_test_case(
        "What is the home office setup stipend for new remote employees?"
    )
    assert_test(test_case, [metric])
