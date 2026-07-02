# Day 11 Lab — AI Test-Generation Assistant

**Track:** QA | **Day:** 11 | **Estimated time:** 70 min

---

## What you will build

An **AI test-generation assistant** that, given the Acme HR Knowledge Assistant feature specification, uses an LLM (or a deterministic mock) to produce:

1. **Test case list** — numbered cases covering happy path, negative, boundary, edge, and security scenarios.
2. **Playwright test code** — Python-string representation of a `spec.ts` file, ready to paste and run.
3. **Structured test data** — a JSON object with `valid`, `invalid`, `boundary`, and `edge` value sets for the assistant's query field.
4. **Self-healing locator demo** — given a broken CSS selector and a DOM snippet, the assistant proposes a replacement with an explanation.

---

## Running the lab

### No API key required (deterministic mock)

```bash
cd /path/to/AI_Training
python labs/qa/day-11/solution.py
```

The mock generator returns realistic, structured outputs every time — no randomness, no network calls.

### With a real LLM (optional)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python labs/qa/day-11/solution.py
```

When `ANTHROPIC_API_KEY` is set, the lab transparently uses `claude-haiku-4-5`.

---

## Files

| File | Purpose |
|---|---|
| `README.md` | This file |
| `requirements.txt` | Dependencies (stdlib only by default; `anthropic` optional) |
| `starter.py` | Skeleton with `TODO` markers — your starting point |
| `solution.py` | Complete reference implementation |

---

## Tasks (starter.py TODOs)

| TODO | Task |
|---|---|
| TODO-1 | Implement `build_test_case_prompt(spec)` — construct the prompt for test case generation |
| TODO-2 | Implement `build_playwright_prompt(spec, test_cases)` — construct the prompt for code generation |
| TODO-3 | Implement `build_test_data_prompt(field_spec)` — construct the prompt for test data generation |
| TODO-4 | Implement `build_self_healing_prompt(broken_selector, intent, dom_snippet)` — construct the self-healing prompt |
| TODO-5 | Implement `call_llm(prompt)` — dispatch to mock or real LLM based on env var |
| TODO-6 | Wire up the `main()` function to call all four generation tasks and print results |

---

## Expected output (mock mode)

```
=== AI Test-Generation Assistant ===
Feature: Acme HR Knowledge Assistant — Query Interface

--- [1/4] Generating Test Cases ---
TC-01: Submit a valid HR query and receive a relevant answer
  Category: happy_path | ...
TC-02: Submit an empty query string
  Category: negative | ...
... (10 total)

--- [2/4] Generating Playwright Test Code ---
// playwright test code preview (first 20 lines) ...

--- [3/4] Generating Test Data ---
Field: query_text
  valid:    ['What is the parental leave policy?', ...]
  boundary: ['', 'a' * 500, ...]
  invalid:  [None-equivalent, '<script>alert(1)</script>', ...]
  edge:     ['   ', '日本語クエリ', ...]

--- [4/4] Self-Healing Locator Demo ---
Broken selector: .search-input-field
Intent: The main query text input on the HR assistant page
Proposed fix: [data-testid="hr-query-input"]
Explanation: The CSS class was renamed during the design system migration ...

Done.
```

---

## Key concepts practiced

- Prompt engineering for structured output (test cases, code, JSON data)
- Provider-flexible LLM dispatch with mock fallback
- Self-healing locator pattern
- Human review checklist for AI-generated tests

---

## Glossary terms

- **Test case** — a specific scenario with preconditions, steps, and an expected result
- **Boundary value analysis** — testing at the exact limits of valid input ranges
- **Self-healing locator** — an LLM-assisted mechanism to repair broken element selectors
- **Tautological test** — a test whose assertion is so weak it always passes regardless of defects
- **Data-testid** — a custom HTML attribute used as a stable automation anchor
