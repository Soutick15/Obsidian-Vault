# Day 9 Lab — LLM-as-Judge Scorer

**Track:** QA | **Day:** 9 of 15 | **Estimated time:** 75 min

## What you will build

An LLM-as-judge evaluation harness that:

1. Scores a system-under-test (SUT) answer against a 3-criterion rubric (groundedness, completeness, on-topic)
2. Performs pairwise comparison between two answers, demonstrating position/order bias
3. Mitigates position bias by running both orderings and requiring agreement
4. Optionally calls `claude-haiku-4-5` as a real judge when `ANTHROPIC_API_KEY` is set

**No API key required** — the deterministic `MockJudge` runs all scenarios without any network calls.

## Prerequisites

- Days 6–8 complete (failure taxonomy, assertion strategies, eval harness)
- Python 3.11+ virtual environment from `setup/environment-setup.md`
- SUT import pattern:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from hr_assistant import answer
```

## Setup

```bash
cd /path/to/AI_Training
source .venv/bin/activate      # activate your venv
pip install -r labs/qa/day-09/requirements.txt
```

## Running the lab

```bash
# Starter file (fill in the TODO blocks)
python labs/qa/day-09/starter.py

# Complete solution — no API key needed
python labs/qa/day-09/solution.py

# Complete solution with real Claude judge (optional)
ANTHROPIC_API_KEY=sk-ant-... python labs/qa/day-09/solution.py
```

## Files

| File | Purpose |
|---|---|
| `README.md` | This file — setup and overview |
| `requirements.txt` | Dependencies (stdlib only; anthropic optional) |
| `starter.py` | Skeleton with TODO blocks for learners to complete |
| `solution.py` | Fully working reference implementation |

## Key concepts exercised

- Rubric design and structured JSON output from a judge
- Single-output rubric scoring with rationale per criterion
- Pairwise comparison and detecting position bias by order-swapping
- Agreement-based bias mitigation (both orderings must agree)
- Conditional real-judge path using `claude-haiku-4-5`

## Expected output (mock judge, no API key)

```
=== SINGLE-OUTPUT SCORING ===
Question: How many PTO days do employees get?
Score: 2.3/5.0
Rationale:
  groundedness  [2/5]: Answer states 20 days but context shows a tiered schedule — partially grounded.
  completeness  [2/5]: Omits the tiered accrual structure entirely.
  on_topic      [3/5]: Addresses the PTO question directly but with wrong specifics.

=== PAIRWISE COMPARISON — POSITION BIAS DEMO ===
Order A→B: winner = A
Order B→A: winner = A   ← consistent (no flip)
... or ...
Order A→B: winner = A
Order B→A: winner = B   ← POSITION BIAS DETECTED: flip on order swap

=== POSITION BIAS MITIGATION ===
Final verdict: tie  (or consistent winner when both orderings agree)

=== REAL JUDGE (optional) ===
(skipped — ANTHROPIC_API_KEY not set)
```
