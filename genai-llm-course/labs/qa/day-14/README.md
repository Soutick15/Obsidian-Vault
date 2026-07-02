# Day 14 Lab — CI Eval Gate, Regression Snapshots, and Drift Detection

## Overview

In this lab you will build a **production-style CI eval gate** for the Acme HR Assistant. The gate runs an eval harness, computes a pass-rate score, and exits non-zero when quality falls below a configurable threshold — causing your CI pipeline to fail automatically.

You will also implement:
- **Baseline snapshot comparison**: save a known-good score and alert when the current score regresses more than 5 %.
- **Drift detection**: compare a rolling window of current scores against a historical baseline window to catch gradual degradation before it becomes a crisis.

By the end of this lab you will have a working GitHub Actions workflow that enforces eval quality on every push and pull request.

---

## Prerequisites

- Days 6–13 complete (eval harness, faithfulness checks, golden sets)
- Python 3.11+
- No API key required — the SUT (`hr_assistant.answer`) runs locally

---

## Files

| File | Purpose |
|------|---------|
| `README.md` | This file |
| `requirements.txt` | Python dependencies |
| `starter.py` | Skeleton with TODO markers — fill these in |
| `solution.py` | Complete reference implementation |
| `.github/workflows/llm-eval.yml` | GitHub Actions CI workflow (reference) |

---

## Tasks

| TODO | Function | What to implement |
|------|----------|-------------------|
| TODO 1 | `build_golden_set()` | Return ≥ 8 `GoldenItem` instances covering PTO, remote work, onboarding, benefits, and a PII-safety check |
| TODO 2 | `run_contains_check()` | Return `True` iff all strings in `expected_contains` appear in the answer (case-insensitive) |
| TODO 3 | `run_faithfulness_check()` | Return `True` iff each faithfulness claim appears in at least one retrieved context |
| TODO 4 | `score_item()` | Call `answer()`, run both checks, return an `EvalResult` |
| TODO 5 | `run_harness()` | Score all golden items; return `(results, pass_rate)` |
| TODO 6 | `compare_to_baseline()` | Load `baseline.json`, compute delta, flag regression if drop > 5 % |
| TODO 7 | `detect_drift()` | Compare mean of two score windows; flag drift if drop > 10 % |

---

## Running the Lab

```bash
# Install dependencies
pip install -r labs/qa/day-14/requirements.txt

# Run the full eval gate (default threshold = 0.75)
python labs/qa/day-14/solution.py

# Force failure — threshold set above current score
python labs/qa/day-14/solution.py --threshold 0.99

# Save the current score as the new baseline
python labs/qa/day-14/solution.py --save-baseline
```

### Exit codes

| Exit code | Meaning |
|-----------|---------|
| `0` | Gate passed — score ≥ threshold, no regression |
| `1` | Gate failed — CI build is blocked |

In a real pipeline the CI system reads the exit code automatically. You do not need to add any special logic.

---

## GitHub Actions

`.github/workflows/llm-eval.yml` is provided as a ready-to-use reference. To activate it:

1. Copy the file into your repository's `.github/workflows/` directory.
2. Commit and push.
3. The workflow runs on every push to `main` and on every pull request.
4. If the eval gate exits `1`, the GitHub check turns red and merging is blocked (when branch protection is enabled).

---

## Expected Output

```
============================================================
CI EVAL GATE — Acme HR Assistant
============================================================

Results (8 items):
  [PASS] What is the remote work policy?
  [FAIL] How many PTO days do new employees get?
         Reason: expected "15" in answer
  [PASS] What benefits are offered to employees?
  [PASS] How does the onboarding process work?
  [PASS] What is the code of conduct policy?
  [PASS] How do employees submit expense reports?
  [PASS] What is the performance review cycle?
  [PASS] Does the answer leak any SSN or email PII?

Overall score: 87.50%
Threshold:     75.00%

Drift detection:
  Current window mean:  87.50%
  Baseline window mean: 96.25%
  Delta:                -8.75%
  [OK] No significant drift detected.

============================================================
GATE: PASSED
```

*(Exact output depends on your golden set. The PTO item is expected to fail — that is the eval gate catching a real bug.)*
