# QA Capstone — Starter Package

Welcome to the QA Capstone starter package. Your task is to fill in all the `TODO` markers across the five Python modules to build a complete automated test and evaluation suite for the Acme HR Knowledge Assistant.

---

## Module Overview

| File | What It Does | TODOs |
|------|-------------|-------|
| `eval_harness.py` | Golden-set evaluation: defines test cases, runs checks, computes pass rate | 5 |
| `judge.py` | Mock LLM-as-judge: scores answers on helpfulness and faithfulness (1–5 scale) | 2 |
| `rag_metrics.py` | RAG retrieval metrics: Precision@k, Recall@k, MRR | 4 |
| `redteam.py` | Adversarial probes: PII leak, prompt injection, hallucination, off-topic | 3 |
| `ci_gate.py` | CI entry point: runs all modules, computes gate score, exits 0 or 1 | 3 |

---

## Running in Mock Mode (No API Key Required)

All modules use a deterministic mock SUT (`hr_assistant.answer()`). No API keys, no network calls, no external dependencies beyond the Python standard library and `pytest`.

```bash
# Install the only external dependency (pytest)
pip install pytest>=7.0

# Run each module individually to see its output
python eval_harness.py
python judge.py
python rag_metrics.py
python redteam.py

# Run the full CI gate (primary entry point)
python ci_gate.py

# Run with stricter threshold
python ci_gate.py --threshold 0.9

# Skip the judge for a faster run
python ci_gate.py --skip-judge

# Run any pytest-style tests
python -m pytest . -v
```

---

## The SUT Interface

The system under test (SUT) is imported from `_shared/hr_assistant.py`:

```python
from hr_assistant import answer

result = answer("How many PTO days do new employees get?")
# Returns:
# {
#   "answer": str,       # the assistant's answer text
#   "contexts": [str],  # the retrieved context chunks
#   "sources":  [str],  # source document identifiers
# }
```

Optional parameters:
- `k=3` — number of contexts to retrieve (default 3)
- `guarded=False` — when True, enables a basic content guard

---

## Important Notes

- **Do not edit files in `_shared/`** — those are the SUT files. Your job is to test them, not modify them.
- **All TODOs are in the starter files** (`eval_harness.py`, `judge.py`, `rag_metrics.py`, `redteam.py`, `ci_gate.py`). Every other file is read-only reference material.
- **Modules raise `NotImplementedError` until you fill in the TODOs.** `ci_gate.py` catches these gracefully so you can run partial implementations.
- **Start with `eval_harness.py`** — it is the foundation and its output will reveal the PTO hallucination bug immediately.

---

## Finding the Seeded Bugs

The SUT has four seeded bugs. Your suite should catch all four:

| Bug | Where to Look |
|-----|--------------|
| PTO hallucination (returns "20" instead of "15") | `eval_harness.py` — golden set |
| Retrieval failure (wrong chunks returned) | `rag_metrics.py` — low precision@k |
| PII leak (token in output) | `redteam.py` — pii_leak probe |
| Prompt injection susceptibility | `redteam.py` — prompt_injection probe |

---

## Deliverables

When you are done, you should have:

1. All TODOs filled in and `python ci_gate.py` running without errors.
2. At least 2 seeded bugs caught and reported in the CI gate output.
3. A `FINDINGS.md` file (you create this) documenting your findings. See `../rubric.md` for what to include.
