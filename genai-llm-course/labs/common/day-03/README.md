# Day 3 Lab — Generation, Decoding Parameters & Model Selection

## Objective

Make LLM decoding parameters tangible, and see a live model-selection comparison, through three exercises:

1. **Decoding visualiser** — pure numpy, no API key. Starting from a raw logit vector over a 10-word vocabulary, implement temperature scaling, top-k filtering, and top-p filtering yourself, and watch the resulting probability distribution shift in a terminal bar chart.
2. **Temperature comparison (mock LLM call)** — sends the same prompt at temperature 0 and temperature 1 to show output variation. Already implemented — read it to see how a real API key would be detected. Runs with a built-in mock by default; uses a real API if an env var is set.
3. **Model selection table** — prints a comparison across 11 model tiers on 7 practical dimensions, using current model names. Already implemented.

This mirrors curriculum Day 3, Section 3 (Worked Example), which works through the same temperature/top-k/top-p logic by hand on a small 4-word example before you do it here on a bigger one.

---

## Setup

```bash
# From the AI_Training root, with your venv active:
cd labs/common/day-03
pip install -r requirements.txt
```

`numpy` is the only required package. `anthropic` and `openai` are optional.

---

## What to do

1. Open `starter.py`. Sections 2 and 3 are already implemented for you — read through them.
2. Fill in the three TODOs in Section 1:
   - **TODO 1** — `apply_temperature`: divide the logits by `temperature`.
   - **TODO 2** — `top_k_filter`: keep the `k` largest probabilities, zero out the rest, re-normalise.
   - **TODO 3** — `top_p_filter`: keep the smallest set of tokens (highest probability first) whose cumulative probability reaches `p`, zero out the rest, re-normalise.
   Each TODO links back to curriculum Day 3, Section 2.3/2.4 and Section 3 (Worked Example), which works the same logic by hand.
3. Run `python starter.py`. Once all three TODOs are correct, your output should match `solution.py`'s output below exactly (same vocabulary, same logits, same seeds).
4. Compare against `solution.py` if you get stuck.

```bash
python starter.py           # your implementation
python solution.py          # reference implementation — runs standalone, no API key needed
```

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

The script auto-detects whichever key is present (Anthropic takes priority). If both are absent, the built-in mock runs automatically — this is the default path and needs no key.

---

## Expected output

This is the **actual, real output** of `python solution.py` (no API key set, mock path). Numbers are deterministic — you should see exactly this.

```
############################################################
#  DAY 3 LAB — GENERATION, DECODING & MODEL SELECTION  #
############################################################
============================================================
SECTION 1 — DECODING PARAMETER VISUALISER
============================================================

Vocabulary: ['cat', 'dog', 'bird', 'fish', 'lion', 'tree', 'sky', 'sun', 'moon', 'star']
Raw logits: [3.5 2.8 1.2 0.9 2.1 0.3 1.8 2.5 1.5 0.6]

  Baseline (T=1.0)
  ----------------------------------------------------
  cat        0.370  ██████████████
  dog        0.184  ███████
  sun        0.136  █████
  lion       0.091  ███
  sky        0.068  ██
  moon       0.050  ██
  bird       0.037  █
  fish       0.028  █
  star       0.020
  tree       0.015

  Temperature = 0.2
  ----------------------------------------------------
  cat        0.963  ██████████████████████████████████████
  dog        0.029  █
  sun        0.006
  ... (lion, sky, moon, bird, fish, star, tree ≈ 0.000)

  Temperature = 2.0
  ----------------------------------------------------
  cat        0.216  ████████
  dog        0.152  ██████
  sun        0.131  █████
  lion       0.107  ████
  sky        0.092  ███
  moon       0.079  ███
  bird       0.068  ██
  fish       0.059  ██
  star       0.051  ██
  tree       0.044  █

  Top-k (k=1, T=1.0)
  ----------------------------------------------------
  cat        1.000  ████████████████████████████████████████
  ... (all other words 0.000)

  Top-k (k=3, T=1.0)
  ----------------------------------------------------
  cat        0.536  █████████████████████
  dog        0.266  ██████████
  sun        0.197  ███████
  ... (remaining 7 words 0.000)

  Top-p (p=0.9, T=1.0)
  ----------------------------------------------------
  cat        0.395  ███████████████
  dog        0.196  ███████
  sun        0.145  █████
  lion       0.097  ███
  sky        0.072  ██
  moon       0.054  ██
  bird       0.040  █
  ... (fish, tree, star 0.000)

  Combined: T=0.8 + top-p=0.9 (typical chat setting)
  ----------------------------------------------------
  cat        0.481  ███████████████████
  dog        0.201  ████████
  sun        0.138  █████
  lion       0.084  ███
  sky        0.057  ██
  moon       0.039  █
  ... (bird, fish, tree, star 0.000)

  INSIGHT: Low temperature concentrates probability on top tokens.
  High temperature spreads it. Top-k/top-p clip low-probability tail tokens.

============================================================
SECTION 2 — TEMPERATURE COMPARISON (LLM CALL)
============================================================

Prompt: "Name one practical use case for a large language model in a software company. Be concise — one sentence only."

  No API key detected — running with built-in mock client.
  (Set ANTHROPIC_API_KEY or OPENAI_API_KEY to use a real model.)

  Temperature = 0.0  [LOW (T=0.0) — deterministic / focused]
  --------------------------------------------------------
  Sample 1: A large language model can power an internal documentation search assistant that answers developer questions in natural language.
  Sample 2: A large language model can power an internal documentation search assistant that answers developer questions in natural language.
  Sample 3: A large language model can power an internal documentation search assistant that answers developer questions in natural language.

  Temperature = 1.0  [HIGH (T=1.0) — varied / creative]
  --------------------------------------------------------
  Sample 1: Imagine an LLM that writes your sprint retrospectives, turning raw bullet points into surprisingly insightful team narratives.
  Sample 2: Imagine an LLM that writes your sprint retrospectives, turning raw bullet points into surprisingly insightful team narratives.
  Sample 3: Imagine an LLM that writes your sprint retrospectives, turning raw bullet points into surprisingly insightful team narratives.

  INSIGHT: At T=0, outputs are identical (or very similar).
  At T=1.0, each sample varies. Match temperature to your task.

============================================================
SECTION 3 — MODEL SELECTION COMPARISON TABLE
============================================================
  * 'Free' = infrastructure cost only (GPU/CPU); no per-token fee

  Family                Tier                        Capability   Cost    Speed     Context     Hosting
  -------------------------------------------------------------------------------------------------------------------
  Claude (Anthropic)    Haiku 4.5 (small/fast)      Good         $       Fast      200K        API only
  Claude (Anthropic)    Sonnet 5 (mid/default)      Very Good    $$      Medium    1M          API only
  Claude (Anthropic)    Opus 4.8 (large)            Excellent    $$$     Slower    1M          API only
  Claude (Anthropic)    Fable 5 (most capable)      Frontier     $$$$    Slower    1M          API only
  GPT (OpenAI)          GPT-5.4 nano/mini (small)   Good         $       Fast      1M          API / Azure
  GPT (OpenAI)          GPT-5.5 (flagship)          Excellent    $$$     Medium    1M          API / Azure
  GPT o-series          o3 (reasoning)              Top          $$$$    Slowest   200K        API / Azure
  Llama (Meta)          1B-8B                       Fair         Free*   Fastest   8K-128K     Self-hosted
  Llama (Meta)          70B+                        Very Good    Free*   Medium    128K        Self-hosted
  Mistral               7B / Mixtral 8x7B           Good         Free*   Fast      32K         Self-hosted / API
  Qwen (Alibaba)        7B-72B                      Good (CJK)   Free*   Medium    32K-128K    Self-hosted / API
  Gemma (Google)        2B-9B                       Fair         Free*   Fastest   8K          Self-hosted / Edge
  -------------------------------------------------------------------------------------------------------------------

  DECISION HEURISTICS:
  • Prototype / iterate fast  →  Small/Fast hosted (Haiku 4.5 / GPT-5.4 mini)
  • Hard reasoning / code     →  Sonnet 5 / Opus 4.8 / Fable 5 / GPT-5.5 / o3
  • Data residency required   →  Self-hosted Llama 70B+ or Mistral
  • Multilingual (CJK)        →  Benchmark Qwen alongside Claude/GPT
  • Edge / mobile             →  Llama 3.2 1B-3B or Gemma 2B
  • Always benchmark on YOUR task — leaderboard ranks don't always generalise.
  • Model names/prices shift every few months — re-check the provider's docs.

============================================================
LAB COMPLETE
============================================================
Next steps:
  • Try starter.py and fill in the TODOs yourself
  • Set ANTHROPIC_API_KEY or OPENAI_API_KEY to run with a real model
  • Experiment with different temperature + top-p combos in the visualiser
```

Model names and pricing tiers in Section 3 change every few months — treat the table as a snapshot, and check the provider's current docs before using it in a real decision.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `NotImplementedError: TODO 1: implement apply_temperature` | You haven't filled in TODO 1 yet | Implement `logits / temperature` in `apply_temperature` |
| `ModuleNotFoundError: No module named 'numpy'` | Dependencies not installed | Run `pip install -r requirements.txt` |
| Top-k output looks the same as the baseline | `k >= len(probs)`, so nothing gets filtered (this is correct behaviour) | Try a smaller `k`, e.g. `k=1` or `k=3` |
| Top-p output keeps every word | `p` is close to 1.0 (this is correct behaviour) | Try a smaller `p`, e.g. `p=0.5`, to see real filtering |
| Your numbers don't match `solution.py` | A rounding/re-normalisation step is off | Re-check that you re-normalise (divide by the new sum) *after* zeroing out entries, not before |
| `[NOTE] ANTHROPIC_API_KEY is set but 'anthropic' package not installed` | You exported a key but didn't install the SDK | Run `pip install anthropic` (or unset the key to use the mock) |
| Script runs but Section 2 says "No API key detected" even though you set one | The env var isn't exported in the current shell | Re-run `export ANTHROPIC_API_KEY=...` in the same terminal session before running the script |

---

## Files

| File | Purpose |
|------|---------|
| `solution.py` | Complete working implementation |
| `starter.py` | Skeleton with 3 TODOs in Section 1 — fill these in yourself |
| `requirements.txt` | Package list (`numpy` required; providers optional) |
| `README.md` | This file |

---

## Learning goals

After completing this lab you should be able to explain:
- Why low temperature produces repetitive, deterministic outputs, and high temperature flattens the distribution
- Why top-p is adaptive (its shortlist size changes with model confidence) while top-k always keeps a fixed count
- How to detect available API providers at runtime via env vars, and fall back safely when none are set
- How to choose a model tier based on capability, cost, speed, context window, and hosting constraints
