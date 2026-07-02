# Day 12 Lab — Exploratory Testing Agent

**Track:** QA | **Day:** 12 | **Estimated time:** 70 min

---

## What you will build

A self-contained **exploratory testing agent** that probes the Acme HR Assistant (`hr_assistant.answer`) autonomously. The agent generates batches of probe questions in three categories, executes them against the SUT, evaluates responses using lightweight invariants, and produces a structured anomaly and coverage report.

No API key is required. Probe generation is fully deterministic by default. An optional real-LLM path is available if `ANTHROPIC_API_KEY` is set.

---

## Files

| File | Purpose |
|---|---|
| `README.md` | This file |
| `requirements.txt` | Dependencies (stdlib only; optional extras noted) |
| `starter.py` | Skeleton with `TODO` markers — your starting point |
| `solution.py` | Complete reference implementation |

---

## Running the lab

```bash
# From the AI_Training root directory
# No install step needed — stdlib only

# Work through the TODOs:
python labs/qa/day-12/starter.py

# Check against the reference:
python labs/qa/day-12/solution.py
```

---

## Learning goals for this lab

After completing the lab you will have:

1. Implemented a **probe bank** with factual, edge, and adversarial categories.
2. Written four **invariant checkers** that evaluate SUT responses without exact expected values.
3. Built an **agent loop** that runs all probes and collects findings.
4. Produced a **structured report** surfacing anomalies with severity levels and a coverage summary.
5. Observed which seeded SUT issues the agent detects automatically.

---

## SUT import

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from hr_assistant import answer
```

---

## Seeded issues the agent should detect

The HR Assistant has four seeded issues (documented in `_shared/README.md`):

| # | Issue | Probe category that triggers it |
|---|---|---|
| 1 | Faithfulness bug — wrong PTO numbers | factual |
| 2 | Retrieval bug — wrong document ranked first | factual |
| 3 | PII leak — sensitive token in response | adversarial |
| 4 | Prompt-injection susceptibility | adversarial |

Your agent should surface at least issues 1, 3, and 4 via invariant failures.

---

## Optional: real LLM probe generation

If `ANTHROPIC_API_KEY` is set in your environment, the solution will use `claude-haiku-4-5` to generate additional probe questions on top of the deterministic bank. Set the variable in your `.env` file:

```
ANTHROPIC_API_KEY=sk-ant-...
```

The deterministic mock path is always the default; the LLM path is additive.
