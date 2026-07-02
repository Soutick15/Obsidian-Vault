"""
Day 10 Lab — RAG & Agent Evaluation: solution.py
=================================================
Track: QA  |  SUT: Acme HR Knowledge Assistant

Complete reference implementation. Run from the repo root:

    python labs/qa/day-10/solution.py

No API key required for the core lab.

The RAGAS REFERENCE block at the bottom is skipped unless RAGAS_DEMO=1 is set
AND the required packages (ragas, datasets) are installed.
"""

import os
import re
import sys
import pathlib

import numpy as np

# ---------------------------------------------------------------------------
# SUT import
# ---------------------------------------------------------------------------
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from hr_assistant import answer  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def header(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def subheader(title: str) -> None:
    print()
    print(f"--- {title} ---")


# ===========================================================================
# LABELED RELEVANCE SET
# ===========================================================================
# Each entry maps a query to:
#   "relevant_sources"  : set of source basenames the retriever SHOULD return
#   "relevant_keywords" : keywords that MUST appear in the top retrieved chunk
#                         for the retrieval to be considered correct (content check).
#                         Used to catch Bug #2: source filename is correct but the
#                         chunk content is about the wrong topic (parental leave
#                         injected for bereavement/sick-leave queries).
#   "faithfulness_facts": list of (claim_token, must_be_in_context bool) pairs
#                         used by the enhanced faithfulness check.
#                         For Bug #1: the answer states "20 days" for new employees
#                         but the corpus says "15 days".  We check whether the
#                         number in the answer's opening claim matches what the
#                         context supports.

LABELED_SET = [
    # ---- Bug #2 trigger: bereavement query ----
    # The SUT injects a parental-leave chunk as the top result for any "leave" query.
    # The top chunk will NOT contain "bereavement" — that's how we detect the bug.
    {
        "query": "What is the bereavement leave policy?",
        "relevant_sources": {"leave-and-pto-policy.md"},
        "top_chunk_must_contain": "bereavement",   # content precision check
    },
    # ---- Bug #2 trigger: sick-leave query ----
    {
        "query": "How does sick leave work?",
        "relevant_sources": {"leave-and-pto-policy.md"},
        "top_chunk_must_contain": "sick",
    },
    # ---- Bug #1 trigger: PTO for new employees ----
    # The SUT answer hard-codes "20 days" but the corpus says "15 days" for 0-2 yrs.
    # The faithfulness check extracts the first numeric claim from the answer
    # and verifies it is grounded in the context (15 is grounded; 20-as-baseline is not).
    {
        "query": "How many PTO days do new employees get?",
        "relevant_sources": {"leave-and-pto-policy.md"},
        "top_chunk_must_contain": None,            # no content precision issue here
        "faithfulness_claim": {
            "description": "Number of PTO days stated for new / first-day employees",
            # The answer's first standalone claim number should match the context's
            # value for 0-2 yr employees.  Context says 15; answer says 20.
            "answer_pattern": r"employees receive \*{0,2}(\d+) days",
            "context_pattern": r"0.2 years\D+(\d+) days",
        },
    },
    # ---- Clean paths ----
    {
        "query": "What health insurance options are available?",
        "relevant_sources": {"benefits-and-insurance.md"},
        "top_chunk_must_contain": None,
    },
    {
        "query": "What are the remote work and home office policies?",
        "relevant_sources": {"remote-work-policy.md"},
        "top_chunk_must_contain": None,
    },
    {
        "query": "What does the code of conduct say about conflicts of interest?",
        "relevant_sources": {"code-of-conduct.md"},
        "top_chunk_must_contain": None,
    },
    {
        "query": "How much parental leave do new parents get?",
        "relevant_sources": {"leave-and-pto-policy.md"},
        "top_chunk_must_contain": "parental",
    },
]


# ===========================================================================
# SUT RUNNER
# ===========================================================================
def run_sut(labeled_set: list, k: int = 3) -> list:
    """Call the SUT for every query; return enriched result dicts."""
    results = []
    for entry in labeled_set:
        query = entry["query"]
        result = answer(query, k=k)
        # Normalise sources to basenames; keep order (rank matters)
        sources = [pathlib.Path(s).name for s in result.get("sources", [])]
        results.append(
            {
                "query": query,
                "relevant_sources": entry.get("relevant_sources", set()),
                "top_chunk_must_contain": entry.get("top_chunk_must_contain"),
                "faithfulness_claim": entry.get("faithfulness_claim"),
                "sources": sources,
                "answer": result.get("answer", ""),
                "contexts": result.get("contexts", []),
            }
        )
    return results


# ===========================================================================
# CONTEXT PRECISION@k
# ===========================================================================
def context_precision(retrieved_sources: list, relevant: set) -> float:
    """
    Fraction of distinct retrieved source slots that are relevant.

    context_precision@k = |{s in top-k : s in relevant}| / k

    Duplicates in retrieved_sources count individually (each rank slot is
    assessed separately), but a source that appears multiple times in the
    retrieved list can only be relevant in each slot independently.
    """
    if not retrieved_sources:
        return 0.0
    hits = sum(1 for s in retrieved_sources if s in relevant)
    return hits / len(retrieved_sources)


# ===========================================================================
# CONTEXT RECALL@k
# ===========================================================================
def context_recall(retrieved_sources: list, relevant: set) -> float:
    """
    Fraction of ground-truth relevant documents covered by the top-k results.

    context_recall@k = |relevant ∩ set(retrieved)| / |relevant|

    Deduplicates retrieved_sources so that returning the same doc 3 times
    does not inflate recall beyond 1.0.
    """
    if not relevant:
        return 1.0  # nothing to recall
    retrieved_set = set(retrieved_sources)
    hits = len(relevant & retrieved_set)
    return hits / len(relevant)


# ===========================================================================
# CONTENT PRECISION CHECK (detects Bug #2)
# ===========================================================================
def content_precision_ok(top_chunk: str, must_contain: str | None) -> bool:
    """
    Return True if the top retrieved chunk contains `must_contain` keyword
    (case-insensitive), or if no constraint is specified.

    This catches Bug #2: the source filename is correct (leave-and-pto-policy.md)
    but the chunk content is about the wrong topic (parental leave injected as
    rank-1 result for bereavement / sick-leave queries).
    """
    if must_contain is None:
        return True
    if not top_chunk:
        return False
    return must_contain.lower() in top_chunk.lower()


# ===========================================================================
# FAITHFULNESS HEURISTIC (detects Bug #1)
# ===========================================================================
# Two-tier approach:
#
# Tier 1 — General heuristic (all queries):
#   Extract numeric tokens from the answer; check each appears in any context.
#   Returns a score in [0, 1].
#
# Tier 2 — Claim-specific check (queries with "faithfulness_claim"):
#   Extract the specific numeric claim from the answer using a regex, then
#   compare it to the expected value found in the context using a second regex.
#   If the numbers differ, faithfulness = 0.0 for that query.
#   This precisely targets Bug #1: answer says "20 days" for new employees
#   but the context says "15 days".

def _general_faithfulness(answer_text: str, contexts: list) -> float:
    """
    Heuristic: fraction of answer's numeric tokens that appear in any context.
    """
    numbers = re.findall(r"\b\d+\b", answer_text)
    if not numbers:
        return 1.0
    context_blob = " ".join(ctx.lower() for ctx in contexts)
    grounded = sum(1 for n in numbers if n in context_blob)
    return grounded / len(numbers)


def faithfulness_heuristic(
    answer_text: str,
    contexts: list,
    claim_spec: dict | None = None,
) -> tuple[float, str]:
    """
    Compute faithfulness score and a human-readable explanation.

    Returns (score: float, explanation: str).

    If claim_spec is provided, apply the claim-specific check (Tier 2) which
    catches Bug #1.  Otherwise fall back to the general heuristic (Tier 1).
    """
    # --- Tier 2: claim-specific check ---
    if claim_spec:
        answer_pat = claim_spec.get("answer_pattern", "")
        context_pat = claim_spec.get("context_pattern", "")

        m_ans = re.search(answer_pat, answer_text, re.IGNORECASE)
        if not m_ans:
            # Cannot extract the claim from the answer — treat as unverifiable
            score = _general_faithfulness(answer_text, contexts)
            return score, "claim not found in answer; using general heuristic"

        claimed_value = m_ans.group(1)

        # Search all context chunks for the expected value
        context_blob = " ".join(contexts)
        m_ctx = re.search(context_pat, context_blob, re.IGNORECASE)
        if not m_ctx:
            # Context doesn't contain the expected pattern either — fallback
            score = _general_faithfulness(answer_text, contexts)
            return score, "expected context pattern not found; using general heuristic"

        context_value = m_ctx.group(1)

        if claimed_value == context_value:
            return 1.0, f"claim '{claimed_value} days' matches context '{context_value} days'"
        else:
            return 0.0, (
                f"MISMATCH: answer claims '{claimed_value} days' for new employees "
                f"but context says '{context_value} days' — hallucinated value"
            )

    # --- Tier 1: general heuristic ---
    score = _general_faithfulness(answer_text, contexts)
    return score, "general numeric grounding check"


# ===========================================================================
# BUG FLAG DETECTION
# ===========================================================================
def detect_bug_flags(
    query: str,
    precision: float,
    faithfulness: float,
    content_ok: bool,
) -> list:
    """
    Return a list of bug flag strings.

    Bug #2 (retrieval content): bereavement or sick-leave queries where the
      top chunk does NOT contain the expected topic keyword.
    Bug #1 (faithfulness): PTO queries where faithfulness == 0.0.
    """
    flags = []
    q_lower = query.lower()

    # Bug #2 — wrong chunk content for leave queries
    if not content_ok and re.search(
        r"\b(bereavement|sick\s+leave)\b", q_lower
    ):
        flags.append("[BUG #2 RETRIEVAL]")

    # Bug #1 — faithfulness failure on PTO / vacation-days queries
    if faithfulness == 0.0 and re.search(
        r"\bpto\b|\bvacation\s+days?\b|new employees get", q_lower
    ):
        flags.append("[BUG #1 FAITHFULNESS]")

    return flags


# ===========================================================================
# AGENT TRAJECTORY CORRECTNESS
# ===========================================================================
def trajectory_correctness(expected: list, actual: list) -> dict:
    """
    Compare an agent's actual tool-call sequence to the expected sequence.

    Returns:
        expected      — the reference tool sequence
        actual        — the observed tool sequence
        missing       — tools in expected but absent from actual
        extra         — tools in actual but absent from expected
        trajectory_ok — True only if actual == expected (order-sensitive)
    """
    expected_set = set(expected)
    actual_set = set(actual)
    return {
        "expected": expected,
        "actual": actual,
        "missing": [t for t in expected if t not in actual_set],
        "extra": [t for t in actual if t not in expected_set],
        "trajectory_ok": actual == expected,
    }


# Illustrative trajectory scenario:
# An HR agent should look up the policy document BEFORE composing a response.
# The buggy trajectory skips the lookup step.
ILLUSTRATIVE_TRAJECTORY = {
    "task": "Answer a leave policy question using policy-lookup then response tools",
    "expected_tools": ["lookup_policy", "compose_response"],
    "actual_tools": ["compose_response"],  # BUG: skipped lookup_policy
}


# ===========================================================================
# MAIN
# ===========================================================================
def main() -> None:
    K = 3

    header("DAY 10 — RAG EVALUATION: RETRIEVAL + FAITHFULNESS")

    # ----- Labeled set -----
    subheader("Labeled Relevance Set")
    print(f"  {len(LABELED_SET)} queries loaded")

    # ----- Run SUT -----
    results = run_sut(LABELED_SET, k=K)

    # ----- Retrieval metrics -----
    subheader(f"Retrieval Evaluation (k={K})")
    col_q = 42
    print(f"  {'Query':<{col_q}} {'Prec@'+str(K):<10} {'Rec@'+str(K):<10} {'Content OK':<12} {'Bug?'}")
    print("  " + "-" * 86)

    precisions, recalls, content_oks = [], [], []
    row_data = []

    for r in results:
        p   = context_precision(r["sources"], r["relevant_sources"])
        rc  = context_recall(r["sources"], r["relevant_sources"])
        top = r["contexts"][0] if r["contexts"] else ""
        cok = content_precision_ok(top, r["top_chunk_must_contain"])

        # Compute faithfulness now so detect_bug_flags gets the right value
        f, _ = faithfulness_heuristic(r["answer"], r["contexts"], r["faithfulness_claim"])
        flags = detect_bug_flags(r["query"], p, f, cok)
        ret_flags = [fl for fl in flags if "RETRIEVAL" in fl]
        bug_str = "  ".join(ret_flags)

        q_short = r["query"][:col_q - 1] + ("…" if len(r["query"]) >= col_q else "")
        cok_str = "YES" if cok else "NO  <--"
        print(f"  {q_short:<{col_q}} {p:<10.2f} {rc:<10.2f} {cok_str:<12} {bug_str}")

        precisions.append(p)
        recalls.append(rc)
        content_oks.append(cok)
        row_data.append((r, p, rc, cok, f, flags))

    mean_p  = float(np.mean(precisions))
    mean_rc = float(np.mean(recalls))
    print(f"\n  Mean Context Precision@{K}: {mean_p:.2f}")
    print(f"  Mean Context Recall@{K}:    {mean_rc:.2f}")
    print(f"  Content-precision failures: {sum(1 for c in content_oks if not c)}")

    # ----- Faithfulness -----
    subheader("Faithfulness Heuristic")
    print(f"  {'Query':<{col_q}} {'Score':<8} {'Bug?'}")
    print("  " + "-" * 70)

    faith_scores = []
    for r, p, rc, cok, f, flags in row_data:
        faith_flags = [fl for fl in flags if "FAITHFULNESS" in fl]
        bug_str = "  ".join(faith_flags)
        q_short = r["query"][:col_q - 1] + ("…" if len(r["query"]) >= col_q else "")
        print(f"  {q_short:<{col_q}} {f:<8.2f} {bug_str}")
        if r.get("faithfulness_claim"):
            _, expl = faithfulness_heuristic(r["answer"], r["contexts"], r["faithfulness_claim"])
            print(f"    Detail: {expl}")
        faith_scores.append(f)

    mean_f = float(np.mean(faith_scores))
    print(f"\n  Mean Faithfulness: {mean_f:.2f}")

    # ----- Agent trajectory -----
    subheader("Agent Trajectory Correctness")
    t  = ILLUSTRATIVE_TRAJECTORY
    tc = trajectory_correctness(t["expected_tools"], t["actual_tools"])
    print(f"  Task: {t['task']}")
    print(f"    Expected tools : {tc['expected']}")
    print(f"    Actual tools   : {tc['actual']}")
    print(f"    Missing tools  : {tc['missing']}")
    print(f"    Extra tools    : {tc['extra']}")
    print(f"    Trajectory OK  : {tc['trajectory_ok']}")

    # ----- Summary -----
    header("SUMMARY")
    print(f"  Context Precision@{K}      : {mean_p:.2f}")
    print(f"  Context Recall@{K}         : {mean_rc:.2f}")
    print(f"  Content-precision failures : {sum(1 for c in content_oks if not c)}")
    print(f"  Mean Faithfulness          : {mean_f:.2f}")
    print(f"  Trajectory correct         : {tc['trajectory_ok']}")
    print()
    print("  Seeded bugs detected:")

    all_bugs: set[str] = set()
    for _, _, _, _, _, flags in row_data:
        all_bugs.update(flags)

    if all_bugs:
        for b in sorted(all_bugs):
            if "RETRIEVAL" in b:
                print(
                    f"    {b}  — bereavement/sick-leave query: parental-leave chunk "
                    "injected as rank-1 result (wrong topic in top context)"
                )
            elif "FAITHFULNESS" in b:
                print(
                    f"    {b}  — PTO query: answer states '20 days' for new employees; "
                    "corpus says '15 days' for 0-2 yr service"
                )
    else:
        print("    None detected")

    print("=" * 60)


# ===========================================================================
# RAGAS REFERENCE BLOCK
# ===========================================================================
# This block demonstrates the full Ragas evaluation suite.
# It is SKIPPED unless:
#   1. RAGAS_DEMO=1 is set in the environment, AND
#   2. `ragas` and `datasets` are installed (pip install ragas datasets)
#
# You also need either ANTHROPIC_API_KEY or OPENAI_API_KEY set.
# Use claude-haiku-4-5 as the judge model for cost efficiency.
#
# This is a DOCUMENTED REFERENCE — the core lab above runs without any key.

def _ragas_demo() -> None:
    """
    Minimal Ragas usage demonstration.
    Evaluates a single (question, contexts, answer, ground_truth) row
    that deliberately contains Bug #1 (faithfulness) from the SUT.
    """
    try:
        from datasets import Dataset  # type: ignore
        from ragas import evaluate  # type: ignore
        from ragas.metrics import (  # type: ignore
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        )
    except ImportError:
        print(
            "\n[RAGAS DEMO] ragas/datasets not installed.\n"
            "  Run: pip install ragas datasets\n"
            "  Then set RAGAS_DEMO=1 and re-run."
        )
        return

    # Single-row dataset that exposes Bug #1:
    # The SUT answer claims 20 days; the corpus says 15 for 0-2 yr employees.
    data = {
        "question": ["How many PTO days do new employees get?"],
        "contexts": [[
            "Acme Corp uses an accrual-based PTO model: "
            "0-2 years of service: 15 days (120 hours). "
            "3-5 years: 20 days (160 hours). "
            "6+ years: 25 days (200 hours). "
            "PTO accrues each pay period (bi-weekly)."
        ]],
        "answer": [
            "Based on Acme Corp policy, employees receive 20 days of PTO per year "
            "starting from their first day of employment."
        ],
        "ground_truth": [
            "New employees (0-2 years of service) receive 15 days of PTO per year "
            "under Acme Corp's tiered accrual schedule."
        ],
    }
    dataset = Dataset.from_dict(data)

    print("\n[RAGAS DEMO] Running evaluation (requires API key)...")
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )
    print("[RAGAS DEMO] Results:")
    print(f"  faithfulness      : {result['faithfulness']:.3f}   (expected ~0.0 — hallucinated claim)")
    print(f"  answer_relevancy  : {result['answer_relevancy']:.3f}")
    print(f"  context_precision : {result['context_precision']:.3f}")
    print(f"  context_recall    : {result['context_recall']:.3f}")
    print(
        "\n  Interpretation: faithfulness ~0 confirms the SUT answer is not grounded "
        "in the retrieved context (Bug #1). context_precision ~1 shows the right "
        "document was retrieved — the failure is in generation, not retrieval."
    )


if __name__ == "__main__":
    main()

    if os.getenv("RAGAS_DEMO") == "1":
        header("RAGAS REFERENCE DEMO (requires API key + ragas install)")
        _ragas_demo()
