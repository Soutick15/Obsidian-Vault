# Day 3 Lab — Generation, Decoding Parameters & Model Selection

## Objective

Make LLM decoding parameters tangible through two exercises:

1. **Decoding visualiser** — pure numpy, no API key. Given a toy probability distribution over a 10-word vocabulary, apply temperature, top-k, and top-p and watch the distribution shift in a terminal bar chart.
2. **Provider-flexible LLM call** — sends the same prompt at temperature 0 and temperature 1 to show output variation. Runs with a built-in mock by default; uses a real API if an env var is set.
3. **Model selection table** — prints a comparison across 11 model tiers on 5 practical dimensions.

---
## Setup

```bash
# From the AI_Training root, with your venv active:
cd labs/common/day-03
pip install -r requirements.txt
```

`numpy` is the only required package. `anthropic` and `openai` are optional.

---

## Run (no API key needed)

```bash
python solution.py
```

This runs the full lab using the built-in mock client. No API credits consumed.

---

## Optional: run with a real API

```bash
# Anthropic (Claude)
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python solution.py

# OpenAI (GPT)
pip install openai
export OPENAI_API_KEY=sk-...
python solution.py
```

The script auto-detects whichever key is present (Anthropic takes priority). If both are absent, the mock runs automatically.

---

## Expected Output (mock path, abbreviated)

```
############################################################
#  DAY 3 LAB — GENERATION, DECODING & MODEL SELECTION  #
############################################################

============================================================
SECTION 1 — DECODING PARAMETER VISUALISER
============================================================

Vocabulary: ['cat', 'dog', 'bird', ...]
Raw logits: [3.5 2.8 1.2 0.9 2.1 0.3 1.8 2.5 1.5 0.6]

  Baseline (T=1.0)
  ----------------------------------------------------
  cat       0.381  ████████████████
  dog       0.187  ████████
  sun       0.138  █████
  ...

  Temperature = 0.2
  ----------------------------------------------------
  cat       0.978  ████████████████████████████████████████
  ...
  (shows concentrated distribution)

  Temperature = 2.0
  ----------------------------------------------------
  cat       0.157  ██████
  dog       0.135  █████
  bird      0.102  ████
  ...
  (shows flattened distribution)

  ... (top-k and top-p sections follow) ...

============================================================
SECTION 2 — TEMPERATURE COMPARISON (LLM CALL)
============================================================

Prompt: "Name one practical use case..."

  No API key detected — running with built-in mock client.

  Temperature = 0.0  [LOW (T=0.0) — deterministic / focused]
  --------------------------------------------------------
  Sample 1: A large language model can automate code review...
  Sample 2: A large language model can automate code review...
  Sample 3: A large language model can automate code review...

  Temperature = 1.0  [HIGH (T=1.0) — varied / creative]
  --------------------------------------------------------
  Sample 1: Imagine an LLM that writes your sprint retrospectives...
  Sample 2: An LLM could auto-generate test case descriptions...
  Sample 3: You could wire an LLM to your Slack incident channel...

  INSIGHT: At T=0, outputs are identical (or very similar).
  At T=1.0, each sample varies. Match temperature to your task.

============================================================
SECTION 3 — MODEL SELECTION COMPARISON TABLE
============================================================

  Family                Tier                    Capability   Cost    Latency    Context    Hosting
  -------------------------------------------------------------------------------------...
  Claude (Anthropic)    Small/Fast (Haiku class) Good        $       Low        200K       API only
  ...
  (11 model tiers listed)

  DECISION HEURISTICS:
  • Prototype / iterate fast  →  Small/Fast hosted (Haiku / 5-mini)
  ...

============================================================
LAB COMPLETE
============================================================
```

---

## Files

| File | Purpose |
|------|---------|
| `solution.py` | Complete working implementation |
| `starter.py` | Skeleton with TODOs — fill this in yourself |
| `requirements.txt` | Package list (`numpy` required; providers optional) |
| `README.md` | This file |

---

## Learning goals

After completing this lab you should be able to explain:
- Why low temperature produces repetitive, deterministic outputs
- Why top-p is adaptive and preferred over top-k for most chat tasks
- How to detect available API providers at runtime via env vars
- How to choose a model tier based on capability, cost, latency, context, and hosting constraints
