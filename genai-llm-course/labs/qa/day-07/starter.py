"""
Day 7 Lab — Testing Non-Deterministic Systems
starter.py: Work through the TODO markers in order.

Run with:
    python -m pytest labs/qa/day-07/starter.py -v
    python -m pytest labs/qa/day-07/starter.py -q    # quick summary

No API key required — the SUT is a deterministic mock pipeline.
"""

# ---------------------------------------------------------------------------
# TODO 1: Import the shared SUT using the standard path-insertion pattern.
#         The _shared/ directory is one level up from this file's parent
#         (i.e., parents[1] relative to this file's resolved path).
#         After the import, `answer` should be callable.
#
# Skeleton (fill in the blanks):
#
#   import sys, pathlib
#   sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[???] / "???"))
#   from hr_assistant import answer
#
# ---------------------------------------------------------------------------
import sys
import pathlib
# TODO 1 — uncomment and complete the lines below:
# sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[???] / "???"))
# from hr_assistant import answer

import difflib
import re
import pytest


# ---------------------------------------------------------------------------
# Helpers (provided — do not modify)
# ---------------------------------------------------------------------------

def token_overlap_ratio(a: str, b: str) -> float:
    """
    Lightweight semantic-similarity proxy using difflib SequenceMatcher
    on lowercased strings.

    Returns a float in [0.0, 1.0].  Values >= 0.40 indicate substantial
    lexical overlap for typical short RAG answers.

    Production upgrade: replace with sentence-transformers cosine similarity
    (sentence_transformers.util.cos_sim) for true semantic comparison.
    """
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ---------------------------------------------------------------------------
# TODO 2 — Schema Assertion
# ---------------------------------------------------------------------------

def test_schema_assertion():
    """
    Assert that the SUT return value has the expected schema:
      - result is a dict
      - "answer" key exists and its value is a str
      - "contexts" key exists and its value is a list
      - "sources" key exists and its value is a list

    This is a schema / structural assertion — the cheapest and most
    universally applicable assertion style. Run it on every SUT call.
    """
    # TODO 2a: Call answer() with a sample HR question.
    # result = answer("What is the remote work policy?")

    # TODO 2b: Assert result is a dict.

    # TODO 2c: Assert "answer" key is present and is a str.

    # TODO 2d: Assert "contexts" key is present and is a list.

    # TODO 2e: Assert "sources" key is present and is a list.

    pass  # remove this line when you implement the assertions


# ---------------------------------------------------------------------------
# TODO 3 — Property-Based / Invariant Tests (parametrized)
# ---------------------------------------------------------------------------

# A diverse set of questions — the invariants must hold for ALL of them.
SAMPLE_QUESTIONS = [
    "What is the remote work policy?",
    "How many PTO days do new employees get?",
    "What is the parental leave policy?",
]


@pytest.mark.parametrize("question", SAMPLE_QUESTIONS)
def test_property_invariants(question):
    """
    Invariant (property-based) assertions that must hold for EVERY response,
    regardless of input:

      (i)   answer is a non-empty string (len > 0 after strip)
      (ii)  sources list has at least 1 entry
      (iii) contexts list has at least 1 entry
      (iv)  No internal error strings leak into the answer
              ("traceback", "error", "exception" must NOT appear)

    Property-based tests are the highest-value / lowest-cost layer.
    A violation here is always a defect.
    """
    # TODO 3a: Call answer(question).
    # result = answer(question)

    # TODO 3b: Assert non-empty answer.

    # TODO 3c: Assert sources has >= 1 entry.

    # TODO 3d: Assert contexts has >= 1 entry.

    # TODO 3e: Assert no internal error strings appear in the answer.
    #           Check for "traceback", "exception", "attributeerror" (case-insensitive).

    pass  # remove this line when you implement the assertions


# ---------------------------------------------------------------------------
# TODO 4 — Contains & Regex Structural Assertion
# ---------------------------------------------------------------------------

def test_contains_and_regex():
    """
    Check that the answer to a remote-work question:
      (a) Contains at least one of the words: "remote", "work", "days"
          (case-insensitive substring check)
      (b) Matches a regex that looks for a digit OR a spelled-out number:
              \b(\d+|one|two|three|four|five)\b

    Structural/pattern assertions are more robust than exact match
    but less powerful than semantic similarity.
    """
    # TODO 4a: Call answer("What is the remote work policy?").
    # result = answer("What is the remote work policy?")
    # ans_lower = result["answer"].lower()

    # TODO 4b: Contains check — assert at least one of the key terms appears.

    # TODO 4c: Regex check — assert a number (digit or word) appears.

    pass  # remove this line


# ---------------------------------------------------------------------------
# TODO 5 — Semantic Similarity Assertion (snapshot / regression pattern)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def remote_work_golden():
    """
    Provided fixture — do not modify.
    Captures the SUT answer once per test module to use as the golden reference.
    Because the shared SUT is a deterministic mock, calling it a second time
    returns an identical answer, so the similarity score will be ~1.0 when the
    system is working correctly.
    """
    # TODO 5-fixture: uncomment the lines below to make the fixture work.
    # result = answer("What is the remote work policy?")
    # return result["answer"]
    return ""   # replace with the two lines above


def test_semantic_similarity(remote_work_golden):
    """
    Compare the SUT answer on a second call to the golden answer captured
    by the fixture above.  This demonstrates the snapshot/approval pattern:

      - Golden reference = first-call output (captured by fixture).
      - Current answer   = second-call output.
      - Assert similarity >= SIMILARITY_THRESHOLD.

    WHY compare against the golden (not a hand-written reference)?
        difflib.SequenceMatcher ratio is suppressed by length differences.
        A 600-char answer vs. a 90-char reference sentence scores ~0.16
        even if the sentence perfectly summarises the answer.
        Comparing two same-length outputs avoids this bias.

    PRODUCTION NOTE: Upgrade to sentence-transformers for length-invariant
    semantic similarity (no threshold calibration needed for length):
        from sentence_transformers import SentenceTransformer, util
        model = SentenceTransformer("all-MiniLM-L6-v2")
        score = util.cos_sim(model.encode(a), model.encode(b)).item()
        assert score >= 0.70
    """
    SIMILARITY_THRESHOLD = 0.85  # tight: SUT is deterministic, expect ~1.0

    # TODO 5a: Call answer("What is the remote work policy?") for the current answer.
    # result = answer("What is the remote work policy?")

    # TODO 5b: Compute similarity between result["answer"] and remote_work_golden.
    # score = token_overlap_ratio(result["answer"], remote_work_golden)

    # TODO 5c: Assert score >= SIMILARITY_THRESHOLD with an informative message.

    pass  # remove this line


# ---------------------------------------------------------------------------
# TODO 6 — Exact-Match Is Brittle (intentional xfail demonstration)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    reason=(
        "Exact-match on natural language output is intentionally brittle. "
        "This test demonstrates WHY exact-match fails even when the SUT is "
        "working correctly. The string below was captured from one run; the "
        "SUT may phrase the answer differently while remaining semantically "
        "correct. See Day 7 curriculum §3.1 for explanation."
    ),
    strict=False,  # XFAIL (expected fail) — does not block the suite
)
def test_exact_match_is_brittle():
    """
    INTENTIONALLY BRITTLE — marked xfail.

    This test uses an exact string captured from a single run. It illustrates
    that even a correct answer can fail an exact-match assertion due to
    paraphrase, punctuation, or whitespace differences.

    DO NOT fix this test by updating the string. Its purpose is to demonstrate
    the brittleness — not to become a passing test.
    """
    # TODO 6a: Call answer("What is the remote work policy?").
    # result = answer("What is the remote work policy?")

    # TODO 6b: Capture the SUT's answer to "What is the remote work policy?"
    #           on a fresh call, then assert equality against it using ==.
    #           (Hint: even comparing the answer to itself at temperature=0
    #           will pass here — but try a hand-written string and observe
    #           why it fails. See solution.py for the reference string.)
    #
    # EXACT_STRING = "..."   # fill in the string you captured — or copy from solution.py
    # assert result["answer"] == EXACT_STRING

    pass  # remove this pass and uncomment the assert above to complete the demo


# ---------------------------------------------------------------------------
# Optional bonus exploration (not graded)
# ---------------------------------------------------------------------------

def test_bonus_sources_are_strings():
    """
    BONUS: Assert that every entry in the sources list is a non-empty string.
    This is an element-level invariant — verifying not just that the list
    exists, but that its contents are well-formed.
    """
    # result = answer("What is the parental leave policy?")
    # for src in result["sources"]:
    #     assert isinstance(src, str) and len(src.strip()) > 0
    pass
