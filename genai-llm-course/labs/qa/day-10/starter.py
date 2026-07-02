"""
Day 10 Lab — RAG & Agent Evaluation: starter.py
================================================
Track: QA  |  SUT: Acme HR Knowledge Assistant

Work through each TODO in order. Run from the repo root:

    python labs/qa/day-10/starter.py

No API key is required. All metrics are computed locally.

Ragas reference: see solution.py (marked "RAGAS REFERENCE — requires API key").
"""

import re
import sys
import pathlib

import numpy as np

# ---------------------------------------------------------------------------
# SUT import — do not modify
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
# TODO-1  Define the labeled relevance set
# ===========================================================================
# A labeled relevance set maps each evaluation query to ground-truth metadata.
#
# Each entry is a dict with:
#   "query"                 : str  — the question to send to the SUT
#   "relevant_sources"      : set  — source basenames that SHOULD be retrieved
#                                    (e.g., "leave-and-pto-policy.md")
#   "top_chunk_must_contain": str | None
#                                  — keyword that MUST appear in the top
#                                    retrieved chunk for the retrieval to be
#                                    correct. Set to None for clean-path queries.
#                                    This catches Bug #2: the source filename
#                                    is correct but the chunk content is wrong
#                                    (parental leave injected for bereavement).
#
# Required queries:
#   1. "What is the bereavement leave policy?"
#      relevant_sources={"leave-and-pto-policy.md"}, top_chunk_must_contain="bereavement"
#      → This triggers Bug #2: parental-leave chunk injected as rank-1 result.
#
#   2. "How does sick leave work?"
#      relevant_sources={"leave-and-pto-policy.md"}, top_chunk_must_contain="sick"
#      → Also triggers Bug #2.
#
#   3. "How many PTO days do new employees get?"
#      relevant_sources={"leave-and-pto-policy.md"}, top_chunk_must_contain=None
#      Also add: "faithfulness_claim" (see TODO-5 for how this is used)
#      → Triggers Bug #1: answer states 20 days; corpus says 15 days.
#
#   4-6. At least three more queries covering other HR topics (clean paths).
#
# Tip: run `python3 labs/qa/_shared/hr_assistant.py` to see available sources.

LABELED_SET = [
    # TODO-1: fill in the labeled relevance set
    # Example structure (uncomment and complete):
    # {
    #     "query": "What is the bereavement leave policy?",
    #     "relevant_sources": {"leave-and-pto-policy.md"},
    #     "top_chunk_must_contain": "bereavement",
    # },
]


# ===========================================================================
# TODO-2  Call the SUT and collect results
# ===========================================================================
# For each entry in LABELED_SET, call answer(query, k=3) and build an
# enriched result dict:
#   {
#       "query":                  str,
#       "relevant_sources":       set,
#       "top_chunk_must_contain": str | None,
#       "faithfulness_claim":     dict | None,   # pass through from labeled set
#       "sources":                list[str],     # basenames (normalise with pathlib)
#       "answer":                 str,
#       "contexts":               list[str],
#   }
#
# Normalise sources to basenames: pathlib.Path(s).name for s in result["sources"]

def run_sut(labeled_set: list, k: int = 3) -> list:
    """Call the SUT for every query and return enriched result dicts."""
    results = []
    for entry in labeled_set:
        query = entry["query"]
        # TODO-2: call answer(query, k=k), normalise sources, build result dict
        raise NotImplementedError("TODO-2: call the SUT and collect results")
    return results


# ===========================================================================
# TODO-3  Compute Context Precision@k
# ===========================================================================
# context_precision@k = (number of retrieved source slots that are relevant) / k
#
# Each slot in retrieved_sources is assessed independently. Duplicates count
# separately (e.g., if the SUT returns the same doc 3 times, each counts).
#
# Return a float in [0.0, 1.0].

def context_precision(retrieved_sources: list, relevant: set) -> float:
    """Compute Context Precision@k for one query."""
    # TODO-3: implement
    raise NotImplementedError("TODO-3: implement context_precision")


# ===========================================================================
# TODO-4  Compute Context Recall@k
# ===========================================================================
# context_recall@k = |relevant ∩ set(retrieved)| / |relevant|
#
# IMPORTANT: deduplicate retrieved_sources before computing intersection
# so that returning the same doc 3 times does not inflate recall above 1.0.
#
# If relevant is empty, return 1.0.

def context_recall(retrieved_sources: list, relevant: set) -> float:
    """Compute Context Recall@k for one query."""
    # TODO-4: implement (remember to deduplicate retrieved_sources)
    raise NotImplementedError("TODO-4: implement context_recall")


# ===========================================================================
# TODO-5  Content precision check (detects Bug #2)
# ===========================================================================
# The SUT injects a parental-leave chunk as rank-1 for any "leave" query.
# The source filename (leave-and-pto-policy.md) is correct, so source-based
# precision is 1.0 — but the content is wrong.
#
# Implement content_precision_ok(top_chunk, must_contain):
#   - If must_contain is None: return True (no constraint)
#   - Otherwise: return True iff must_contain appears (case-insensitive)
#     in top_chunk.
#
# Call this with:
#   top_chunk = result["contexts"][0]  (the first/highest-ranked chunk)
#   must_contain = result["top_chunk_must_contain"]

def content_precision_ok(top_chunk: str, must_contain) -> bool:
    """Return True if the top retrieved chunk contains the required keyword."""
    # TODO-5: implement
    raise NotImplementedError("TODO-5: implement content_precision_ok")


# ===========================================================================
# TODO-6  Faithfulness heuristic (detects Bug #1)
# ===========================================================================
# Implement two tiers:
#
# Tier 1 — General heuristic (for all queries without a claim_spec):
#   Extract numeric tokens from the answer with re.findall(r"\b\d+\b", answer).
#   Check how many appear in a lowercased join of all context strings.
#   Return grounded_count / total_count  (1.0 if no numeric tokens found).
#
# Tier 2 — Claim-specific check (for queries with faithfulness_claim dict):
#   The dict has keys:
#     "answer_pattern"  : regex with one capture group to extract the claimed value
#     "context_pattern" : regex with one capture group to extract the expected value
#   Extract both values and compare. If they differ → return (0.0, "MISMATCH: ...").
#   If either pattern doesn't match → fall back to Tier 1.
#
# Return a tuple: (score: float, explanation: str)
#
# Bug #1 trigger:
#   answer_pattern  = r"employees receive \*{0,2}(\d+) days"
#   context_pattern = r"0.2 years\D+(\d+) days"
#   The answer captures "20"; the context captures "15" → score = 0.0.

def faithfulness_heuristic(
    answer_text: str,
    contexts: list,
    claim_spec=None,
) -> tuple:
    """Return (faithfulness_score: float, explanation: str)."""
    # TODO-6: implement both tiers
    raise NotImplementedError("TODO-6: implement faithfulness_heuristic")


# ===========================================================================
# TODO-7  Bug flag detection
# ===========================================================================
# Implement detect_bug_flags(query, faithfulness, content_ok) returning a list
# of flag strings:
#
# [BUG #2 RETRIEVAL]    — if content_ok is False AND query contains
#                         "bereavement" or "sick leave"
# [BUG #1 FAITHFULNESS] — if faithfulness == 0.0 AND query matches
#                         r"\bpto\b|\bvacation\s+days?\b|new employees get"
#
# Return an empty list if no bugs detected.

def detect_bug_flags(query: str, faithfulness: float, content_ok: bool) -> list:
    """Return a list of bug flag strings for a given query/metrics."""
    # TODO-7: implement
    raise NotImplementedError("TODO-7: implement detect_bug_flags")


# ===========================================================================
# TODO-8  Agent trajectory correctness
# ===========================================================================
# An agent trajectory is the ordered list of tool names the agent called.
# Implement trajectory_correctness(expected, actual) returning:
#   {
#       "expected":      list[str],
#       "actual":        list[str],
#       "missing":       list[str],   # in expected but not in actual
#       "extra":         list[str],   # in actual but not in expected
#       "trajectory_ok": bool,        # True only if actual == expected (order-sensitive)
#   }

def trajectory_correctness(expected: list, actual: list) -> dict:
    """Evaluate agent trajectory against expected tool-call sequence."""
    # TODO-8: implement
    raise NotImplementedError("TODO-8: implement trajectory_correctness")


# Illustrative agent scenario: an HR agent should look up the policy document
# before composing a response. The buggy trajectory skips the lookup step.
ILLUSTRATIVE_TRAJECTORY = {
    "task": "Answer a leave policy question using policy-lookup then response tools",
    "expected_tools": ["lookup_policy", "compose_response"],
    "actual_tools": ["compose_response"],  # BUG: skipped lookup_policy
}


# ===========================================================================
# Main — do not modify the structure below; implement the TODOs above
# ===========================================================================
def main() -> None:
    K = 3
    col_q = 42

    header("DAY 10 — RAG EVALUATION: RETRIEVAL + FAITHFULNESS")

    subheader("Labeled Relevance Set")
    if not LABELED_SET:
        print("  [!] LABELED_SET is empty — complete TODO-1 first.")
        return
    print(f"  {len(LABELED_SET)} queries loaded")

    results = run_sut(LABELED_SET, k=K)

    # ----- Retrieval metrics -----
    subheader(f"Retrieval Evaluation (k={K})")
    print(f"  {'Query':<{col_q}} {'Prec@'+str(K):<10} {'Rec@'+str(K):<10} {'Content OK':<12} {'Bug?'}")
    print("  " + "-" * 86)

    precisions, recalls, content_oks = [], [], []
    row_data = []

    for r in results:
        p   = context_precision(r["sources"], r["relevant_sources"])
        rc  = context_recall(r["sources"], r["relevant_sources"])
        top = r["contexts"][0] if r["contexts"] else ""
        cok = content_precision_ok(top, r["top_chunk_must_contain"])
        f, _ = faithfulness_heuristic(r["answer"], r["contexts"], r.get("faithfulness_claim"))
        flags = detect_bug_flags(r["query"], f, cok)
        ret_flags = [fl for fl in flags if "RETRIEVAL" in fl]

        q_short = r["query"][:col_q - 1] + ("…" if len(r["query"]) >= col_q else "")
        cok_str = "YES" if cok else "NO  <--"
        print(f"  {q_short:<{col_q}} {p:<10.2f} {rc:<10.2f} {cok_str:<12} {'  '.join(ret_flags)}")

        precisions.append(p)
        recalls.append(rc)
        content_oks.append(cok)
        row_data.append((r, p, rc, cok, f, flags))

    print(f"\n  Mean Context Precision@{K}: {np.mean(precisions):.2f}")
    print(f"  Mean Context Recall@{K}:    {np.mean(recalls):.2f}")
    print(f"  Content-precision failures: {sum(1 for c in content_oks if not c)}")

    # ----- Faithfulness -----
    subheader("Faithfulness Heuristic")
    print(f"  {'Query':<{col_q}} {'Score':<8} {'Bug?'}")
    print("  " + "-" * 70)

    faith_scores = []
    for r, p, rc, cok, f, flags in row_data:
        faith_flags = [fl for fl in flags if "FAITHFULNESS" in fl]
        q_short = r["query"][:col_q - 1] + ("…" if len(r["query"]) >= col_q else "")
        print(f"  {q_short:<{col_q}} {f:<8.2f} {'  '.join(faith_flags)}")
        if r.get("faithfulness_claim"):
            _, expl = faithfulness_heuristic(r["answer"], r["contexts"], r.get("faithfulness_claim"))
            print(f"    Detail: {expl}")
        faith_scores.append(f)

    print(f"\n  Mean Faithfulness: {np.mean(faith_scores):.2f}")

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
    print(f"  Context Precision@{K}      : {np.mean(precisions):.2f}")
    print(f"  Context Recall@{K}         : {np.mean(recalls):.2f}")
    print(f"  Content-precision failures : {sum(1 for c in content_oks if not c)}")
    print(f"  Mean Faithfulness          : {np.mean(faith_scores):.2f}")
    print(f"  Trajectory correct         : {tc['trajectory_ok']}")
    print()
    print("  Seeded bugs detected:")

    all_bugs: set = set()
    for _, _, _, _, _, flags in row_data:
        all_bugs.update(flags)

    if all_bugs:
        for b in sorted(all_bugs):
            print(f"    {b}")
    else:
        print("    None detected")

    print("=" * 60)


if __name__ == "__main__":
    main()
