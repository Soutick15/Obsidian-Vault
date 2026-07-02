# Day 10 Lab — RAG & Agent Evaluation: Metrics, Ragas, and Trajectory Testing

**Track:** QA | **SUT:** Acme HR Knowledge Assistant (`labs/qa/_shared/hr_assistant.py`)

---

## What You'll Build

A local evaluation harness that measures **retrieval quality** and **answer faithfulness** against a small labeled relevance set, then surfaces two seeded bugs in the SUT:

- **Bug #2 — Retrieval content failure:** A bereavement-leave query returns a parental-leave chunk as rank-1 result. The source filename is technically correct (`leave-and-pto-policy.md`) but the *content* is wrong. A content-precision check catches this.
- **Bug #1 — Faithfulness failure:** A PTO query for new employees produces an answer claiming "20 days" which is not grounded in the retrieved context (which says "15 days" for 0-2 yr employees). A claim-specific faithfulness check catches this.

You will also implement an illustrative **agent trajectory correctness** check and see a documented **Ragas reference snippet** for when an API key is available.

---

## Files

| File | Purpose |
|---|---|
| `README.md` | This file |
| `requirements.txt` | Python dependencies (stdlib + numpy; ragas optional) |
| `starter.py` | Skeleton with TODO-1 through TODO-8 — your starting point |
| `solution.py` | Complete reference implementation |

---

## Setup

From the repo root:

```bash
pip install -r labs/qa/day-10/requirements.txt
```

No API key required for the core lab. The Ragas reference block in `solution.py` is clearly marked and is skipped unless `RAGAS_DEMO=1` is set.

---

## Running

```bash
# Attempt the lab yourself:
python3 labs/qa/day-10/starter.py

# Check against the full solution:
python3 labs/qa/day-10/solution.py
```

Run from the **repo root** so the SUT's relative paths to `data/hr-corpus/` resolve correctly.

---

## Expected Output (solution.py)

```
============================================================
  DAY 10 — RAG EVALUATION: RETRIEVAL + FAITHFULNESS
============================================================

--- Labeled Relevance Set ---
  7 queries loaded

--- Retrieval Evaluation (k=3) ---
  Query                                      Prec@3     Rec@3      Content OK   Bug?
  --------------------------------------------------------------------------------------
  What is the bereavement leave policy?      1.00       1.00       NO  <--      [BUG #2 RETRIEVAL]
  How does sick leave work?                  0.67       1.00       NO  <--      [BUG #2 RETRIEVAL]
  How many PTO days do new employees get?    1.00       1.00       YES
  What health insurance options are availab… 1.00       1.00       YES
  ...

  Mean Context Precision@3: 0.95
  Mean Context Recall@3:    1.00
  Content-precision failures: 2

--- Faithfulness Heuristic ---
  Query                                      Score    Bug?
  How many PTO days do new employees get?    0.00     [BUG #1 FAITHFULNESS]
    Detail: MISMATCH: answer claims '20 days' for new employees but context says '15 days'
  ...

  Mean Faithfulness: 0.86

--- Agent Trajectory Correctness ---
  Task: Answer a leave policy question using policy-lookup then response tools
    Expected tools : ['lookup_policy', 'compose_response']
    Actual tools   : ['compose_response']
    Missing tools  : ['lookup_policy']
    Trajectory OK  : False

============================================================
  SUMMARY
============================================================
  Context Precision@3      : 0.95
  Context Recall@3         : 1.00
  Content-precision failures : 2
  Mean Faithfulness          : 0.86
  Trajectory correct         : False

  Seeded bugs detected:
    [BUG #1 FAITHFULNESS]  — PTO answer states '20 days'; corpus says '15 days' for 0-2 yr employees
    [BUG #2 RETRIEVAL]  — bereavement/sick-leave query: parental-leave chunk injected as rank-1 result
============================================================
```

---

## Lab Tasks (starter.py TODOs)

| TODO | Task |
|---|---|
| TODO-1 | Define the labeled relevance set (query → relevant sources + content keyword) |
| TODO-2 | Call the SUT `answer()` and normalise returned sources/contexts |
| TODO-3 | Implement `context_precision(retrieved_sources, relevant)` |
| TODO-4 | Implement `context_recall(retrieved_sources, relevant)` — remember to deduplicate |
| TODO-5 | Implement `content_precision_ok(top_chunk, must_contain)` to catch Bug #2 |
| TODO-6 | Implement `faithfulness_heuristic` (Tier 1: numeric grounding; Tier 2: claim-specific check for Bug #1) |
| TODO-7 | Implement `detect_bug_flags(query, faithfulness, content_ok)` |
| TODO-8 | Implement `trajectory_correctness(expected, actual)` |

---

## Key Concepts Practised

- Building and using a labeled relevance set with content constraints
- Context Precision@k and Context Recall@k (with deduplication)
- Content-precision check: detecting wrong-chunk retrieval beyond source-name matching
- Claim-specific faithfulness heuristic: catching numeric hallucinations
- Surfacing Bug #2 (retrieval content) and Bug #1 (faithfulness) systematically
- Agent trajectory / tool-call correctness evaluation
- Ragas framework usage (documented reference, no key needed for the lab itself)
