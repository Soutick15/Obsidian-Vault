# Day 7 Lab — Testing Non-Deterministic Systems

**Track:** QA | **Day:** 7 of 15  
**Estimated time:** 70 minutes  
**Prerequisites:** Day 6 (failure taxonomy, shared SUT)

---

## Goal

Write a pytest test suite for the Acme HR Knowledge Assistant SUT that demonstrates **five assertion styles**:

| Style | What it checks |
|-------|----------------|
| (a) Property-based / invariant | Schema valid, answer non-empty, ≥ 1 source — on every response |
| (b) Semantic similarity | Answer is close enough to a reference string (difflib token overlap) |
| (c) Structural / schema | Return value has expected keys and types |
| (d) Regex / contains | Key entities and patterns present in the answer |
| (e) Exact-match (brittle demo) | Marked `xfail` — illustrates why exact match breaks |

The SUT needs **no API key** — it is a deterministic mock RAG pipeline (pure Python, TF-IDF retrieval + template generation).

---

## SUT Import Pattern

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from hr_assistant import answer
# answer(question: str, k: int = 3, guarded: bool = False)
# -> {"answer": str, "contexts": list[str], "sources": list[str]}
```

---

## Files

| File | Purpose |
|------|---------|
| `README.md` | This file |
| `requirements.txt` | Python dependencies (`pytest` only) |
| `starter.py` | Lab skeleton — work through TODO markers |
| `solution.py` | Complete reference implementation |

---

## Running the Suite

```bash
# From the repo root
python -m pytest labs/qa/day-07/ -v

# Quick summary only
python -m pytest labs/qa/day-07/ -q
```

Expected output summary:
```
PASSED  test_schema_assertion
PASSED  test_property_invariants[question0]
PASSED  test_property_invariants[question1]
PASSED  test_property_invariants[question2]
PASSED  test_contains_and_regex
PASSED  test_semantic_similarity
XFAIL   test_exact_match_is_brittle   ← expected failure; illustrates brittleness
```

---

## Lab Tasks

Work through the TODO markers in `starter.py` in order:

1. **TODO 1** — Import the SUT via the path-insertion pattern.
2. **TODO 2** — Implement `test_schema_assertion`: call the SUT and assert all keys exist with correct types.
3. **TODO 3** — Implement `test_property_invariants` (parametrized): assert non-empty answer, ≥ 1 source, non-empty contexts.
4. **TODO 4** — Implement `test_contains_and_regex`: assert key entity substrings and a numeric pattern.
5. **TODO 5** — Implement `test_semantic_similarity`: compute difflib ratio against a reference; assert ≥ threshold.
6. **TODO 6** — Implement `test_exact_match_is_brittle` marked `@pytest.mark.xfail`: show that an exact string match fails even when the answer is semantically correct.

---

## Key Concepts Reinforced

- Property-based invariants are the highest-value / lowest-cost assertion layer.
- Semantic similarity with a calibrated threshold tolerates paraphrase without missing real failures.
- `difflib.SequenceMatcher` is a no-dependency stand-in; `sentence-transformers` is the production upgrade.
- Exact-match tests on natural language output are brittle and should be avoided (or clearly marked `xfail`).

---

## No API Key Required

The shared SUT is a fully local mock — no `ANTHROPIC_API_KEY`, no `OPENAI_API_KEY`, no network calls. The suite runs offline.
