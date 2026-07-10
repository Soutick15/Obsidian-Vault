# Day 4 Lab — Prompt Library

## Objective

Write two prompt-builder functions and hand their output to a safe JSON parser:

1. `few_shot_classify(text, examples, labels)` — builds a few-shot classification prompt.
2. `extract_json(text, fields)` — builds a JSON-extraction prompt.
3. Feed the extraction reply through `parse_json_safe()` (already written for you).

The mock LLM client, the `run(messages, system)` helper, and `parse_json_safe()` are all
pre-written in `starter.py` — you don't need to touch them. The mock lets the whole lab
run with **no API key**.

See Day 4, Section 3 (Worked Example) in the curriculum for a fully worked version of
`few_shot_classify` before you write your own.

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

This is the actual output of `python solution.py` with no key set — the mock is
deterministic, so yours should match exactly:

```
=== Provider: MOCK ===

--- few_shot_classify ---
Input   : "The shipment arrived three days late and was damaged."
Result  : NEGATIVE

--- extract_json ---
Input   : "Please reschedule our meeting with Dr. Patel (d.patel@clinic.org) to 2026-07-15 to discuss Q3 budget."
Parsed  : {'sender_name': 'Dr. Patel', 'sender_email': 'd.patel@clinic.org', 'meeting_date': '2026-07-15', 'meeting_topic': 'Q3 budget'}

All demos complete.
```

---

## Lab Tasks (starter.py)

Open `starter.py` and complete the three `TODO` blocks:

| TODO | What to implement | Where the pattern comes from |
|------|-------------------|-------------------------------|
| 1 | `few_shot_classify(text, examples, labels)` — build the messages list with labels + formatted examples + target line | Day 4 §3 (Worked Example) |
| 2 | `extract_json(text, fields)` — build the messages list with field list, delimiters, and a JSON shape example | Day 4 §2.6 (Getting Clean JSON Out) |
| 3 | In `demo()`, call `parse_json_safe(raw, fallback=...)` on the extraction reply | Day 4 §2.6 (safe parsing) |

Run `python starter.py` after each TODO to check your progress — `NotImplementedError`
means that TODO isn't done yet.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `NotImplementedError: TODO 1...` | `few_shot_classify` still has the placeholder `raise` | Implement TODO 1 — return a messages list, not `None` |
| `Result` is `[MOCK] No specific handler matched.` | The prompt text doesn't end with the exact target line `Review: "<text>" ->` | The mock looks for a line ending in `->` with no label after it — check your f-string has no trailing space or extra text after the arrow |
| `Parsed` is `{'sender_name': None, ...}` (all `None`) | `extract_json` isn't mentioning `"JSON object"` or the reply doesn't parse | Make sure your instruction includes the phrase `JSON object`, and that fields are wrapped correctly |
| `[WARN] JSON parse failed: ...` printed, then a `{}` or all-`None` dict | `parsed` fallback wasn't passed, or the raw reply had unexpected formatting | Pass `fallback={f: None for f in fields}` as shown in TODO 3 |
| `TypeError: 'NoneType' object is not subscriptable` on `parsed` | TODO 3 not implemented — `parsed` is still `None` | Replace the placeholder line with the `parse_json_safe(...)` call |
| Nothing happens / `ModuleNotFoundError: anthropic` | You set `ANTHROPIC_API_KEY` but didn't install the SDK | Either `pip install -r requirements.txt`, or unset the key to use the mock |

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
