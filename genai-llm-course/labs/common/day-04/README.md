# Day 4 Lab — Reusable Prompt Library

## Objective

Build a small Python module that:

1. **Constructs prompts** via builder functions (`few_shot_classify`, `extract_json`, `summarize`, `rewrite`) that return standard `messages` lists.
2. **Runs prompts** via a provider-flexible `run(messages, system)` helper that auto-detects an API key and falls back to a deterministic mock when none is present.
3. **Parses structured output** safely with `json.loads` + `try/except`.

This lab is runnable with **no API key** — the mock path demonstrates the full flow.

---

## Setup

```bash
# From the AI_Training root, activate your venv if you have one:
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

cd labs/common/day-04

# Optional: install real providers (only needed if using a live key)
pip install -r requirements.txt
```

---

## Run Commands

### No API key (mock — always works)

```bash
python solution.py
```

### With Anthropic key

```bash
ANTHROPIC_API_KEY=sk-ant-... python solution.py
```

### With OpenAI key

```bash
OPENAI_API_KEY=sk-... python solution.py
```

Set `USE_MOCK=true` to force the mock even when a key is present:

```bash
USE_MOCK=true python solution.py
```

---

## Expected Output (mock path)

```
=== Provider: MOCK ===

--- few_shot_classify ---
Input   : "The shipment arrived three days late and was damaged."
Result  : NEGATIVE

--- extract_json ---
Input   : "Please reschedule our meeting with Dr. Patel (d.patel@clinic.org) to 2026-07-15 to discuss Q3 budget."
Parsed  : {'sender_name': 'Dr. Patel', 'sender_email': 'd.patel@clinic.org', 'meeting_date': '2026-07-15', 'meeting_topic': 'Q3 budget'}

--- summarize ---
Input   : 245 chars
Result  : [MOCK SUMMARY] Artificial intelligence is transforming industries...

--- rewrite ---
Input   : 136 chars
Result  : [MOCK REWRITE] Please provide your feedback at your earliest convenience...

All demos complete.
```

---

## Lab Tasks (starter.py)

Open `starter.py` and complete the five `TODO` blocks:

| TODO | What to implement |
|------|-------------------|
| 1 | `few_shot_classify(text, examples, labels)` — build messages list with examples |
| 2 | `extract_json(text, fields)` — build messages list with field list in the prompt |
| 3 | `summarize(text, bullets)` — build messages list for bullet-point summary |
| 4 | `rewrite(text, style, max_pct)` — build messages list for rewriting |
| 5 | `run(messages, system)` — detect key, call real API or return mock response |

---

## How to Opt Into a Real API

Set your key in the shell or in `AI_Training/.env`:

```bash
# .env (never commit this file)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

The `run()` function checks `ANTHROPIC_API_KEY` first, then `OPENAI_API_KEY`, then falls back to mock.

> **OpenAI:** uncomment `openai>=1.30.0` in `requirements.txt` and run `pip install -r requirements.txt` before using an OpenAI key.

---

## Files

| File | Description |
|------|-------------|
| `README.md` | This file |
| `requirements.txt` | Optional provider SDKs |
| `starter.py` | Skeleton with TODO blocks |
| `solution.py` | Fully working solution |
