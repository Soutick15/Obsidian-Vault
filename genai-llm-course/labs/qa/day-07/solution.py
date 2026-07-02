"""
Day 7 Lab — Testing Non-Deterministic Systems
solution.py: Complete reference implementation.

Run with:
    python -m pytest labs/qa/day-07/solution.py -v
    python -m pytest labs/qa/day-07/solution.py -q

No API key required. No third-party ML libraries required.
"""

# ---------------------------------------------------------------------------
# SUT import — standard path-insertion pattern used across all QA labs
# ---------------------------------------------------------------------------
import sys
import pathlib

sys.path.insert(
    0,
    str(pathlib.Path(__file__).resolve().parents[1] / "_shared"),
)
from hr_assistant import answer  # noqa: E402

# ---------------------------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------------------------
import difflib
import re
import pytest


# ===========================================================================
# Helpers
# ===========================================================================

def token_overlap_ratio(a: str, b: str) -> float:
    """
    Lightweight semantic-similarity proxy: difflib SequenceMatcher ratio
    on lowercased strings.

    Returns float in [0.0, 1.0].  Best used to compare two strings of
    similar length (e.g., a current answer vs. a captured golden answer).

    IMPORTANT — length sensitivity:
        SequenceMatcher ratio is dominated by length differences when
        comparing strings of very different sizes (e.g., a 600-char answer
        vs. a 90-char reference sentence gives a low ratio even if the
        short string is a perfect summary of the long one).
        For short-reference vs. long-answer comparisons, prefer key-phrase
        containment checks (see test_contains_and_regex).

    Production upgrade path:
        from sentence_transformers import SentenceTransformer, util
        model = SentenceTransformer("all-MiniLM-L6-v2")
        score = util.cos_sim(model.encode(a), model.encode(b)).item()
        # Threshold for sentence embeddings: >= 0.70 is typical.
        # Sentence embeddings are length-invariant and capture paraphrase.
    """
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture(scope="module")
def remote_work_golden():
    """
    Capture the SUT answer for the remote-work question once per test module.
    Used as the golden reference for regression / similarity checks.

    Because the shared SUT is a deterministic mock (TF-IDF + template
    generator, no sampling), calling it twice returns identical output.
    This fixture captures that output, making the golden reference
    self-consistent and independent of any hard-coded string.

    In a live-LLM pipeline (temperature=0, stable model):
        1. Run once; serialise the golden answer to a JSON file.
        2. In CI, load the file and compare with token_overlap_ratio >= 0.85.
        3. Re-capture (update the file) only after a deliberate pipeline change.
    """
    result = answer("What is the remote work policy?")
    return result["answer"]


# ===========================================================================
# (c) Structural / Schema Assertion
# ===========================================================================

def test_schema_assertion():
    """
    Assert that the SUT return value conforms to the expected schema:
      - result is a dict
      - "answer"   → str
      - "contexts" → list
      - "sources"  → list

    Schema assertions are cheap, always correct, and should be the first
    check run on every SUT call.
    """
    result = answer("What is the remote work policy?")

    assert isinstance(result, dict), "result must be a dict"
    assert "answer" in result, "result must have 'answer' key"
    assert isinstance(result["answer"], str), "'answer' must be a str"
    assert "contexts" in result, "result must have 'contexts' key"
    assert isinstance(result["contexts"], list), "'contexts' must be a list"
    assert "sources" in result, "result must have 'sources' key"
    assert isinstance(result["sources"], list), "'sources' must be a list"


# ===========================================================================
# (a) Property-Based / Invariant Tests (parametrized)
# ===========================================================================

SAMPLE_QUESTIONS = [
    "What is the remote work policy?",
    "How many PTO days do new employees get?",
    "What is the parental leave policy?",
]


@pytest.mark.parametrize("question", SAMPLE_QUESTIONS)
def test_property_invariants(question):
    """
    Invariants that must hold for EVERY response, regardless of input:

      (i)   answer is a non-empty string after stripping whitespace
      (ii)  sources list has >= 1 entry (RAG must cite a source)
      (iii) contexts list has >= 1 entry (retrieval must return something)
      (iv)  No internal error strings leak into the answer text

    These are the highest-value / lowest-cost checks in the test suite.
    A violation here is always a system defect, not a threshold issue.
    """
    result = answer(question)

    # (i) Non-empty answer
    assert len(result["answer"].strip()) > 0, (
        f"Expected non-empty answer for question: {question!r}"
    )

    # (ii) At least one source cited
    assert len(result["sources"]) >= 1, (
        f"Expected >= 1 source for question: {question!r}, got {result['sources']}"
    )

    # (iii) At least one retrieved context
    assert len(result["contexts"]) >= 1, (
        f"Expected >= 1 context for question: {question!r}"
    )

    # (iv) No internal error strings leaked into user-facing answer
    ans_lower = result["answer"].lower()
    forbidden = ["traceback", "exception", "attributeerror", "keyerror"]
    for term in forbidden:
        assert term not in ans_lower, (
            f"Internal error term {term!r} leaked into answer for: {question!r}"
        )


# ===========================================================================
# (d) Contains & Regex Structural Assertion
# ===========================================================================

def test_contains_and_regex():
    """
    For a remote-work question, assert:
      (a) At least one of ["remote", "work", "policy"] appears in the answer
          (case-insensitive substring check).
      (b) A number — digit or spelled-out word — appears in the answer.

    Key-phrase containment works well for long answers where difflib
    ratio is suppressed by length differences.  It does not require ML.
    """
    result = answer("What is the remote work policy?")
    ans_lower = result["answer"].lower()

    # (a) Key-term presence — at least one must appear
    key_terms = ["remote", "work", "policy"]
    assert any(term in ans_lower for term in key_terms), (
        f"Expected at least one of {key_terms} in answer.\nGot: {result['answer']!r}"
    )

    # (b) Numeric reference — digit OR spelled-out number
    number_pattern = re.compile(
        r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b",
        re.IGNORECASE,
    )
    assert number_pattern.search(result["answer"]), (
        f"Expected a numeric reference in the answer.\nGot: {result['answer']!r}"
    )


# ===========================================================================
# (b) Semantic Similarity Assertion — regression / snapshot pattern
# ===========================================================================

def test_semantic_similarity(remote_work_golden):
    """
    Compare the SUT answer on a second call to the golden answer captured
    by the fixture.  This demonstrates the snapshot/approval pattern:

      - Golden reference = first-call output (captured once by fixture).
      - Current answer   = second-call output.
      - Assert similarity >= 0.85 (tight, since the SUT is deterministic).

    WHY NOT a hand-written reference string?
        difflib.SequenceMatcher ratio is strongly affected by length
        differences.  A 600-char answer compared to a 90-char reference
        sentence scores ~0.16, even if the sentence perfectly summarises
        the answer.  Comparing two same-length strings avoids this bias.

    PRODUCTION NOTE — two upgrade paths:
        1. Length-aware: compare answer[:N] to reference[:N] with difflib.
        2. Length-invariant: use sentence-transformers cosine similarity,
           which is independent of string length:
               model = SentenceTransformer("all-MiniLM-L6-v2")
               score = util.cos_sim(model.encode(a), model.encode(b)).item()
               assert score >= 0.70
    """
    SIMILARITY_THRESHOLD = 0.85  # tight: SUT is deterministic, expect near-1.0

    result = answer("What is the remote work policy?")
    current = result["answer"]

    score = token_overlap_ratio(current, remote_work_golden)

    assert score >= SIMILARITY_THRESHOLD, (
        f"Answer diverged from golden reference.\n"
        f"Similarity: {score:.3f} (threshold: {SIMILARITY_THRESHOLD})\n"
        f"Current (first 200): {current[:200]!r}\n"
        f"Golden  (first 200): {remote_work_golden[:200]!r}"
    )


# ===========================================================================
# (e) Exact-Match Is Brittle — intentional xfail demonstration
# ===========================================================================

@pytest.mark.xfail(
    reason=(
        "DEMONSTRATION: exact-match on natural language is brittle. "
        "The hard-coded string below does not match the actual SUT output — "
        "the SUT returns a longer, formatted document extract. "
        "This XFAIL illustrates why exact-match assertions fail even when "
        "the system is working correctly. See Day 7 curriculum §3.1."
    ),
    strict=False,
)
def test_exact_match_is_brittle():
    """
    INTENTIONALLY BRITTLE — marked xfail.

    The string below is a plausible-sounding but fabricated answer that
    does not match the SUT output.  Even if you updated it to match today,
    any corpus change, prompt change, or model update would break it again.

    The test is marked xfail(strict=False):
      - Assertion fails  → XFAIL  (expected; counts as green in CI)
      - Assertion passes → XPASS  (unexpected; also green with strict=False)

    DO NOT update the string to make it pass. The failure IS the lesson.
    """
    result = answer("What is the remote work policy?")

    EXACT_STRING = (
        "Employees may work remotely up to three days per week "
        "with prior manager approval. Remote work requires a stable "
        "internet connection and a dedicated workspace."
    )

    # Expected to XFAIL — this is the pedagogical demonstration.
    assert result["answer"] == EXACT_STRING


# ===========================================================================
# Bonus: element-level source invariant
# ===========================================================================

def test_bonus_sources_are_strings():
    """
    BONUS: Every entry in sources must be a non-empty string.
    Element-level invariants catch malformed entries that a list-length
    check alone would miss.
    """
    result = answer("What is the parental leave policy?")
    for i, src in enumerate(result["sources"]):
        assert isinstance(src, str), (
            f"sources[{i}] is {type(src).__name__}, expected str"
        )
        assert len(src.strip()) > 0, (
            f"sources[{i}] is an empty string"
        )


# ===========================================================================
# Entrypoint for direct execution (informational — use pytest to run tests)
# ===========================================================================

if __name__ == "__main__":
    import subprocess

    print("Running Day 7 solution via pytest...\n")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v"],
        cwd=str(pathlib.Path(__file__).resolve().parents[3]),
    )
    sys.exit(proc.returncode)
