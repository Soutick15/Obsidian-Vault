# Day 8 Lab — Build a Local Evaluation Harness

## Overview

You will build a **local evaluation harness** for the shared Acme HR Assistant. The harness runs a golden Q&A dataset, scores each result with local assertions (no API key required), and prints a structured pass/fail report.

**Primary goal:** catch the seeded faithfulness bug — the SUT states 20 days PTO for new employees; the corpus says 15.

---

## Prerequisites

- Completed Days 6–7 (you know the SUT and can import it).
- Python 3.11+ with the course virtual environment active.
- **No API key required** for the core harness.

---

## Files

```
labs/qa/day-08/
├── README.md               ← you are here
├── requirements.txt        ← pytest (core); promptfoo/deepeval noted as optional
├── starter.py              ← work through TODO markers
└── solution.py             ← reference implementation (run this to verify)
```

**Also included in solution.py (as documented reference — requires an API key):**
- `promptfooconfig.yaml` content — shown as a multi-line string, explained inline.
- `test_deepeval_example.py` content — shown as a multi-line string, explained inline.

---

## Tasks (starter.py)

Work through the `# TODO` markers in order:

| # | TODO | What to implement |
|---|------|-------------------|
| 1 | `build_golden_set()` | Return a list of `GoldenItem` dataclasses covering ≥5 questions from the HR corpus, including the PTO regression question with `expected_contains=["15"]` |
| 2 | `run_contains_check()` | Check that all strings in `item.expected_contains` appear in the answer (case-insensitive) |
| 3 | `run_faithfulness_check()` | For each `item.faithfulness_claims`, verify the claim appears in at least one retrieved context |
| 4 | `score_item()` | Run contains + faithfulness checks; return an `EvalResult` with `passed=True` only if both pass |
| 5 | `run_harness()` | Iterate over golden set → call SUT → score → collect results |
| 6 | `print_report()` | Print a formatted report: per-item PASS/FAIL with failure details, then a summary score |

---

## Running the Lab

### Core harness (no API key)

```bash
# From repo root
python labs/qa/day-08/solution.py
```

Expected output (abbreviated):
```
==============================
 Acme HR Eval Harness — Day 8
==============================

[PASS] Q1: How many PTO days do new employees get in their first two years?
[FAIL] Q1 (faithfulness): Claim "15 days" not found in any retrieved context
       Answer preview: ...employees receive 20 days of PTO per year...

...

==============================
 SUMMARY
==============================
Passed : 4 / 5
Failed : 1 / 5
Score  : 80.0%

FAILURES DETAIL:
  [1] PTO days question — faithfulness: claim "15 days" unsupported by answer
      → Bug: SUT states 20 days; corpus says 15 for 0-2 yrs service (Seeded Issue #1)
==============================
```

### promptfoo example (requires API key + Node.js)

The file `labs/qa/day-08/promptfooconfig.yaml` shows the equivalent test suite for promptfoo.

```bash
npm install -g promptfoo
export ANTHROPIC_API_KEY=sk-ant-...    # or OPENAI_API_KEY
npx promptfoo eval --config labs/qa/day-08/promptfooconfig.yaml
```

### deepeval example (requires API key)

The file `labs/qa/day-08/test_deepeval_example.py` shows the same checks in deepeval's pytest style.

```bash
pip install deepeval
export OPENAI_API_KEY=sk-...           # deepeval defaults to OpenAI judge
pytest labs/qa/day-08/test_deepeval_example.py -v
```

---

## Key Learning Points

1. **Golden sets drive harnesses.** Every test is grounded in a known-correct answer from the corpus.
2. **Faithfulness ≠ correctness.** The SUT's PTO answer may sound plausible but is unsupported by — and contradicts — the retrieved context.
3. **Local metrics are fast and free.** The entire harness runs in under one second with no API calls.
4. **promptfoo and deepeval** provide richer tooling when an API key is available; the pattern is identical to what you built locally.
