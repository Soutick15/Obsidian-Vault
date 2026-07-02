# Day 13 Lab — Security & Guardrails for the HR Assistant

## Objective

Add a **guardrail layer** around the HR Assistant built on Days 6–12. The layer sits *outside* the LLM call and enforces three controls:

1. **Input Guard** — scans the user query and any retrieved document chunks for prompt-injection patterns; blocks requests before they reach the LLM.
2. **Output Guard** — redacts PII (email addresses, phone numbers, SSN-like patterns) from the LLM response and validates the response schema.
3. **Tool Allow-List** — rejects any tool call not in the registered allow-list, defending against indirect injection that tries to invoke unauthorised tools.

A **deterministic mock path** (no API key required) lets you complete the full lab offline.

---

## Directory Layout

```
labs/developer/day-13/
├── README.md          ← this file
├── requirements.txt   ← dependencies
├── starter.py         ← skeleton with TODO markers
└── solution.py        ← complete reference implementation
```

HR corpus lives at: `data/hr-corpus/` (repo root — 13 policy documents).

---

## Setup

```bash
# From the AI_Training root
source .venv/bin/activate          # or .venv\Scripts\activate on Windows
pip install -r labs/developer/day-13/requirements.txt
```

No API key needed — the lab uses a mock LLM by default.

To test with a real provider (optional):

```bash
# Copy .env.example → .env and add your key
ANTHROPIC_API_KEY=sk-ant-...  python labs/developer/day-13/solution.py
```

---

## Tasks (starter.py)

Work through the TODO markers in `starter.py` in order:

| # | TODO | What to implement |
|---|---|---|
| 1 | `InputGuard.check_text` | Regex + keyword scan for injection patterns |
| 2 | `InputGuard.check_retrieved_chunks` | Apply check_text to each retrieved chunk; return first hit |
| 3 | `OutputGuard.redact_pii` | Regex redaction: email, phone, SSN |
| 4 | `OutputGuard.validate_schema` | Check non-empty string, max length |
| 5 | `ToolAllowList.check` | Allow-list enforcement; raise on unknown tool |
| 6 | `GuardedHRAssistant.ask` | Wire all three guards around the mock LLM call |

---

## Running the Lab

```bash
# Reference solution (no API key)
python labs/developer/day-13/solution.py

# Your implementation
python labs/developer/day-13/starter.py
```

Expected output shows three scenarios: benign query (passes), indirect injection (blocked), and PII-in-output (redacted).

---

## Stretch Goals

- Add a fourth guard that detects if the response contains the system-prompt text and redacts/blocks it.
- Integrate with the Day 10 multi-agent pipeline — add guardrails at each agent boundary.
- Replace the regex injection classifier with a call to the Llama Guard API (requires a local Ollama instance).
- Log all guard events to a structured JSON file with timestamps and guard-triggered fields.
