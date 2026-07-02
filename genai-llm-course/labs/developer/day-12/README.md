# Day 12 Lab — Structured Extraction Service

**Track:** Developer | **Day:** 12 — Structured Outputs & Production App Patterns

---

## What you will build

A **Structured Extraction Service** that extracts HR-policy information from a natural-language query + context document and returns a strongly-typed Pydantic object — or a typed error result if extraction fails after validation and repair attempts.

```
User query + context
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │  1. Input validation (length, not-empty)    │
  │  2. LLM call  (real provider OR mock)       │
  │  3. JSON parse                              │
  │  4. Pydantic validate                       │
  │       ├── OK  ──► ExtractionResult(ok=True) │
  │       └── FAIL ──► Repair prompt            │
  │                     └── Re-validate         │
  │                          ├── OK  ──► result │
  │                          └── FAIL ──► error │
  └─────────────────────────────────────────────┘
```

### Extracted schema

```python
class PolicyExtraction(BaseModel):
    policy_name:  str            # e.g. "Annual Leave Policy"
    entitlement:  str            # e.g. "20 days per year"
    eligibility:  str            # e.g. "All full-time employees after 3 months"
    source:       str            # e.g. "Employee Handbook, Section 4.2"
    confidence:   Optional[float]  # 0.0 – 1.0
```

---

## Files

| File | Purpose |
|------|---------|
| `README.md` | This file |
| `requirements.txt` | Python dependencies |
| `starter.py` | Lab skeleton — work through TODO markers |
| `solution.py` | Complete reference implementation |

---

## Running the lab

### No API key (mock mode — default)

```bash
cd /path/to/AI_Training
python labs/developer/day-12/solution.py
```

The mock LLM deterministically returns:
- **Case 1 (success):** valid JSON matching the schema.
- **Case 2 (repair):** malformed JSON first, then valid JSON on the repair call.

### With Anthropic key (real mode)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python labs/developer/day-12/solution.py
```

### With OpenAI key

```bash
export OPENAI_API_KEY=sk-...
python labs/developer/day-12/solution.py
```

Priority: `ANTHROPIC_API_KEY` → `OPENAI_API_KEY` → mock.

---

## Expected output (mock mode)

```
=== Day 12 Lab: Structured Extraction Service ===
Provider: mock

--- Case 1: Success path ---
[INFO] Attempt 1/3 — calling mock provider
[INFO] Validation OK on attempt 1
Result: OK
  policy_name : Annual Leave Policy
  entitlement : 20 days per calendar year, increasing to 25 days after 5 years
  eligibility : All permanent employees who have completed 3 months of service
  source      : Employee Handbook v3.2, Section 4.2
  confidence  : 0.95

--- Case 2: Malformed-output → repair path ---
[INFO] Attempt 1/3 — calling mock provider (will return malformed JSON)
[INFO] Validation FAILED on attempt 1: 1 validation error for PolicyExtraction ...
[INFO] Sending repair prompt (attempt 2/3)
[INFO] Validation OK on attempt 2
Result: OK (after repair)
  policy_name : Remote Work Policy
  entitlement : Up to 3 days per week working from home
  eligibility : Employees with at least 6 months tenure and manager approval
  source      : Remote Work Guidelines 2024, Clause 2.1
  confidence  : 0.88
```

---

## Lab tasks (starter.py)

Work through the TODOs in order:

1. **TODO 1** — Define the `PolicyExtraction` Pydantic model.
2. **TODO 2** — Implement provider detection (anthropic / openai / mock).
3. **TODO 3** — Implement the mock LLM function (two scenarios: valid, malformed).
4. **TODO 4** — Implement the extraction prompt template function.
5. **TODO 5** — Implement the repair prompt template function.
6. **TODO 6** — Implement the core `extract()` function with validation + repair loop.
7. **TODO 7** — Add structured logging to each attempt.
8. **TODO 8** — Wire up the two demo cases in `main()`.

---

## Tips

- Read the solution only after attempting each TODO yourself.
- The `ExtractionResult` dataclass is provided for you — do not change its interface.
- Keep `MAX_RETRIES = 3` (initial attempt + up to 2 repairs).
- The repair prompt must include the raw broken output AND the validation error string.
- The 30-second timeout in `call_provider()` only fires on real network calls (requires an actual provider key set); the mock path returns instantly and will not exercise timeout handling.
